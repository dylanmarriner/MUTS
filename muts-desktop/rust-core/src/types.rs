/**
 * Type definitions for MUTS core
 */

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Interface types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InterfaceInfo {
    pub id: String,
    pub name: String,
    pub interface_type: InterfaceType,
    pub capabilities: Vec<String>,
    pub is_available: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InterfaceType {
    SocketCAN,
    J2534,
    CANALyst,
    Vector,
    Mock,
    Custom(String),
}

/// Connection results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionResult {
    pub success: bool,
    pub session_id: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionStatus {
    pub connected: bool,
    pub interface_id: String,
    pub session_count: u32,
    pub last_activity: Option<DateTime<Utc>>,
}

/// Session information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionInfo {
    pub id: String,
    pub interface_id: String,
    pub start_time: DateTime<Utc>,
    pub status: SessionStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SessionStatus {
    Active,
    Idle,
    Error(String),
}

/// CAN frame data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CanFrame {
    pub id: u32,
    pub extended: bool,
    pub data: Vec<u8>,
    pub timestamp: DateTime<Utc>,
}

/// Telemetry data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryData {
    pub timestamp: DateTime<Utc>,
    pub signals: HashMap<String, f64>,
    pub metadata: TelemetryMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryMetadata {
    pub source: String,
    pub sample_rate: f64,
    pub quality: SignalQuality,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SignalQuality {
    Good,
    Fair,
    Poor,
    Invalid,
}

/// Diagnostic data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiagnosticResponse {
    pub service_id: u8,
    pub data: Vec<u8>,
    pub success: bool,
    pub timestamp: DateTime<Utc>,
    pub response_time_ms: u64,
}

/// ROM validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RomValidationResult {
    pub is_valid: bool,
    pub ecu_type: Option<String>,
    pub calibration_id: Option<String>,
    pub checksum_valid: bool,
    pub size: usize,
    pub errors: Vec<String>,
}

/// Checksum verification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChecksumResult {
    pub valid: bool,
    pub calculated: u32,
    pub expected: u32,
    pub algorithm: String,
}

/// Flash operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlashOptions {
    pub verify_after_write: bool,
    pub backup_before_flash: bool,
    pub skip_regions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlashPrepareResult {
    pub job_id: String,
    pub estimated_time_sec: u32,
    pub blocks_to_write: u32,
    pub backup_created: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlashProgress {
    pub job_id: String,
    pub progress_percent: f32,
    pub current_block: u32,
    pub total_blocks: u32,
    pub stage: FlashStage,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FlashStage {
    Preparing,
    Backup,
    Writing,
    Verifying,
    Complete,
    Failed,
}

/// Live changes
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveChange {
    pub address: u32,
    pub old_value: Vec<u8>,
    pub new_value: Vec<u8>,
    pub change_type: ChangeType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ChangeType {
    SingleByte,
    MultiByte,
    Table,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplyResult {
    pub success: bool,
    pub changes_applied: u32,
    pub failed_changes: u32,
    pub session_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevertResult {
    pub success: bool,
    pub changes_reverted: u32,
    pub message: String,
}

/// Safety system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SafetyLevel {
    ReadOnly,
    Simulate,
    LiveApply,
    Flash,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyStateInfo {
    pub armed: bool,
    pub level: SafetyLevel,
    pub time_remaining: Option<u64>,
    pub violations: Vec<SafetyViolation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyViolation {
    pub parameter: String,
    pub value: f64,
    pub limit: f64,
    pub severity: ViolationSeverity,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ViolationSeverity {
    Warning,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyEvent {
    pub event_type: SafetyEventType,
    pub level: SafetyLevel,
    pub message: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SafetyEventType {
    Armed,
    Disarmed,
    Violation,
    Warning,
    EmergencyStop,
}

/// Use HashMap for telemetry signals
use std::collections::HashMap;
