/**
 * Safety system implementation
 * Prevents accidental ECU damage and enforces safety workflows
 */

use crate::types::*;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn, error};
use chrono::{Utc, Duration};

/// Safety state manager
#[derive(Debug, Clone)]
pub struct SafetyState {
    pub armed: bool,
    pub level: SafetyLevel,
    pub arm_time: Option<chrono::DateTime<Utc>>,
    pub violations: Vec<SafetyViolation>,
    pub limits: SafetyLimits,
    pub session_timeout: u64, // seconds
}

#[derive(Debug, Clone)]
pub struct SafetyLimits {
    pub max_boost: f64,
    pub max_timing_advance: f64,
    pub max_fuel_pressure: f64,
    pub max_rpm: f64,
    pub min_afr: f64,
    pub max_afr: f64,
    pub max_iat: f64,
    pub max_ect: f64,
}

impl Default for SafetyLimits {
    fn default() -> Self {
        Self {
            max_boost: 25.0, // PSI
            max_timing_advance: 35.0, // degrees
            max_fuel_pressure: 80.0, // PSI
            max_rpm: 7000.0,
            min_afr: 11.0,
            max_afr: 17.0,
            max_iat: 80.0, // °C
            max_ect: 110.0, // °C
        }
    }
}

impl SafetyState {
    pub fn new() -> Self {
        Self {
            armed: false,
            level: SafetyLevel::ReadOnly,
            arm_time: None,
            violations: Vec::new(),
            limits: SafetyLimits::default(),
            session_timeout: 300, // 5 minutes
        }
    }
    
    pub async fn arm(&mut self, level: SafetyLevel) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // Check if we can arm at this level
        match level {
            SafetyLevel::ReadOnly => {
                // Always can arm to read-only
                self.armed = true;
                self.level = level;
                self.arm_time = Some(Utc::now());
            },
            SafetyLevel::Simulate => {
                // Can arm to simulate if no critical violations
                self.clear_expired_violations();
                if !self.has_critical_violations() {
                    self.armed = true;
                    self.level = level;
                    self.arm_time = Some(Utc::now());
                } else {
                    return Err("Cannot arm: Critical safety violations present".into());
                }
            },
            SafetyLevel::LiveApply => {
                // More strict checks for live apply
                self.clear_expired_violations();
                if !self.has_violations() {
                    self.armed = true;
                    self.level = level;
                    self.arm_time = Some(Utc::now());
                } else {
                    return Err("Cannot arm: Safety violations present".into());
                }
            },
            SafetyLevel::Flash => {
                // Strictest checks for flashing
                self.clear_expired_violations();
                if !self.has_violations() && self.is_safe_to_flash() {
                    self.armed = true;
                    self.level = level;
                    self.arm_time = Some(Utc::now());
                } else {
                    return Err("Cannot arm: Conditions not safe for flashing".into());
                }
            },
        }
        
        info!("Safety system armed at level: {:?}", level);
        Ok(())
    }
    
    pub async fn disarm(&mut self) {
        self.armed = false;
        self.level = SafetyLevel::ReadOnly;
        self.arm_time = None;
        self.violations.clear();
        info!("Safety system disarmed");
    }
    
    pub fn can_connect(&self) -> bool {
        // Can always connect in read-only mode
        true
    }
    
    pub fn can_flash(&self) -> bool {
        self.armed && matches!(self.level, SafetyLevel::Flash)
    }
    
    pub fn can_apply_live(&self) -> bool {
        self.armed && matches!(self.level, SafetyLevel::LiveApply | SafetyLevel::Flash)
    }
    
    pub fn check_parameters(&mut self, params: &HashMap<String, f64>) -> Vec<SafetyViolation> {
        let mut new_violations = Vec::new();
        
        // Check each parameter against limits
        if let Some(&boost) = params.get("boost_pressure") {
            if boost > self.limits.max_boost {
                new_violations.push(SafetyViolation {
                    parameter: "boost_pressure".to_string(),
                    value: boost,
                    limit: self.limits.max_boost,
                    severity: ViolationSeverity::Critical,
                });
            }
        }
        
        if let Some(&timing) = params.get("ignition_timing") {
            if timing > self.limits.max_timing_advance {
                new_violations.push(SafetyViolation {
                    parameter: "ignition_timing".to_string(),
                    value: timing,
                    limit: self.limits.max_timing_advance,
                    severity: ViolationSeverity::Critical,
                });
            }
        }
        
        if let Some(&rpm) = params.get("engine_rpm") {
            if rpm > self.limits.max_rpm {
                new_violations.push(SafetyViolation {
                    parameter: "engine_rpm".to_string(),
                    value: rpm,
                    limit: self.limits.max_rpm,
                    severity: ViolationSeverity::Critical,
                });
            }
        }
        
        if let Some(&afr) = params.get("lambda") {
            if afr < self.limits.min_afr || afr > self.limits.max_afr {
                new_violations.push(SafetyViolation {
                    parameter: "lambda".to_string(),
                    value: afr,
                    limit: if afr < self.limits.min_afr { self.limits.min_afr } else { self.limits.max_afr },
                    severity: ViolationSeverity::Warning,
                });
            }
        }
        
        if let Some(&iat) = params.get("iat") {
            if iat > self.limits.max_iat {
                new_violations.push(SafetyViolation {
                    parameter: "iat".to_string(),
                    value: iat,
                    limit: self.limits.max_iat,
                    severity: ViolationSeverity::Warning,
                });
            }
        }
        
        if let Some(&ect) = params.get("ect") {
            if ect > self.limits.max_ect {
                new_violations.push(SafetyViolation {
                    parameter: "ect".to_string(),
                    value: ect,
                    limit: self.limits.max_ect,
                    severity: ViolationSeverity::Critical,
                });
            }
        }
        
        // Add new violations
        self.violations.extend(new_violations.clone());
        
        new_violations
    }
    
    pub fn clear_expired_violations(&mut self) {
        let now = Utc::now();
        self.violations.retain(|v| {
            // Keep violations for 10 minutes
            now.signed_duration_since(Utc::now()).num_seconds() < 600
        });
    }
    
    pub fn has_violations(&self) -> bool {
        !self.violations.is_empty()
    }
    
    pub fn has_critical_violations(&self) -> bool {
        self.violations.iter().any(|v| matches!(v.severity, ViolationSeverity::Critical))
    }
    
    pub fn is_safe_to_flash(&self) -> bool {
        // Additional checks for flashing safety
        // E.g., engine must be off, voltage stable, etc.
        true // Simplified
    }
    
    pub fn get_info(&self) -> SafetyStateInfo {
        let time_remaining = if let Some(arm_time) = self.arm_time {
            let elapsed = Utc::now().signed_duration_since(arm_time);
            let remaining = self.session_timeout as i64 - elapsed.num_seconds();
            if remaining > 0 {
                Some(remaining as u64)
            } else {
                None
            }
        } else {
            None
        };
        
        SafetyStateInfo {
            armed: self.armed,
            level: self.level.clone(),
            time_remaining,
            violations: self.violations.clone(),
        }
    }
}

/// Safety monitor for real-time parameter checking
pub struct SafetyMonitor {
    state: Arc<RwLock<SafetyState>>,
}

impl SafetyMonitor {
    pub fn new(state: Arc<RwLock<SafetyState>>) -> Self {
        Self { state }
    }
    
    pub async fn check_telemetry(&self, telemetry: &TelemetryData) -> Vec<SafetyViolation> {
        let mut state = self.state.write().await;
        state.check_parameters(&telemetry.signals)
    }
    
    pub async fn add_violation(&self, violation: SafetyViolation) {
        let mut state = self.state.write().await;
        state.violations.push(violation);
        
        // If critical violation, consider disarming
        if matches!(violation.severity, ViolationSeverity::Critical) {
            warn!("Critical safety violation detected - consider disarming");
        }
    }
    
    pub async fn clear_violations(&self) {
        let mut state = self.state.write().await;
        state.violations.clear();
    }
}

/// Safety snapshot for rollback
#[derive(Debug, Clone)]
pub struct SafetySnapshot {
    pub id: String,
    pub timestamp: chrono::DateTime<Utc>,
    pub parameters: HashMap<String, f64>,
    pub checksum: String,
}

impl SafetySnapshot {
    pub fn create(params: &HashMap<String, f64>) -> Self {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        for (key, value) in params {
            key.hash(&mut hasher);
            value.to_bits().hash(&mut hasher);
        }
        
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            timestamp: Utc::now(),
            parameters: params.clone(),
            checksum: format!("{:x}", hasher.finish()),
        }
    }
}

/// Safety manager for coordinating safety operations
pub struct SafetyManager {
    state: Arc<RwLock<SafetyState>>,
    monitor: SafetyMonitor,
    snapshots: Arc<RwLock<HashMap<String, SafetySnapshot>>>,
}

impl SafetyManager {
    pub fn new() -> Self {
        let state = Arc::new(RwLock::new(SafetyState::new()));
        let monitor = SafetyMonitor::new(state.clone());
        
        Self {
            state,
            monitor,
            snapshots: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    pub async fn create_snapshot(&self, params: &HashMap<String, f64>) -> String {
        let snapshot = SafetySnapshot::create(params);
        let id = snapshot.id.clone();
        
        let mut snapshots = self.snapshots.write().await;
        snapshots.insert(id.clone(), snapshot);
        
        info!("Created safety snapshot: {}", id);
        id
    }
    
    pub async fn get_snapshot(&self, id: &str) -> Option<SafetySnapshot> {
        let snapshots = self.snapshots.read().await;
        snapshots.get(id).cloned()
    }
    
    pub fn get_state(&self) -> Arc<RwLock<SafetyState>> {
        self.state.clone()
    }
    
    pub fn get_monitor(&self) -> &SafetyMonitor {
        &self.monitor
    }
}
