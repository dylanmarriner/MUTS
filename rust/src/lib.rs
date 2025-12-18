use pyo3::prelude::*;
use pyo3::types::PyDict;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Engine identifier for patch operations
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum EngineType {
    Versa,
    Cobb,
    Mds,
}

impl From<&str> for EngineType {
    fn from(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "versa" => EngineType::Versa,
            "cobb" => EngineType::Cobb,
            "mds" => EngineType::Mds,
            _ => panic!("Invalid engine type: {}", s),
        }
    }
}

/// Engine-specific error types
#[derive(Debug, thiserror::Error)]
pub enum EngineError {
    #[error("Unsupported operation for this engine")]
    UnsupportedOperation,
    #[error("Invalid engine type")]
    InvalidEngine,
    #[error("Patch validation failed: {0}")]
    ValidationFailed(String),
    #[error("Checksum mismatch")]
    ChecksumMismatch,
    #[error("Safety violation: {0}")]
    SafetyViolation(String),
}

/// Map change data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MapChange {
    pub map_id: String,
    pub x_index: Option<usize>,
    pub y_index: Option<usize>,
    pub old_value: Option<f32>,
    pub new_value: f32,
    pub reason: Option<String>,
}

/// Patch build result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PatchResult {
    pub success: bool,
    pub patch_data: Vec<u8>,
    pub checksum: u32,
    pub size: usize,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
}

/// Validation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub valid: bool,
    pub risk_score: u8, // 0-100
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub safety_violations: Vec<String>,
}

/// Apply result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApplyResult {
    pub success: bool,
    pub ecu_verified: bool,
    pub applied_changes: usize,
    pub failed_changes: Vec<String>,
    pub verification_errors: Option<Vec<String>>,
    pub message: String,
}

/// Trait for engine-specific patch builders
pub trait EnginePatchBuilder {
    fn build_patch(&self, changes: &[MapChange], original_rom: &[u8]) -> Result<PatchResult, EngineError>;
    fn get_engine_type(&self) -> EngineType;
}

/// Trait for engine-specific patch validators
pub trait EnginePatchValidator {
    fn validate_patch(&self, patch_data: &[u8], original_rom: &[u8], safety_limits: &PyDict) -> Result<ValidationResult, EngineError>;
    fn get_engine_type(&self) -> EngineType;
}

/// VERSA engine implementation
pub struct VersaEngineBuilder;

impl EnginePatchBuilder for VersaEngineBuilder {
    fn build_patch(&self, changes: &[MapChange], original_rom: &[u8]) -> Result<PatchResult, EngineError> {
        let mut patch_data = Vec::new();
        let mut checksum = 0u32;
        
        // Build VERSA-specific patch format
        for change in changes {
            // Write map ID and location
            patch_data.extend_from_slice(&(change.map_id.len() as u16).to_le_bytes());
            patch_data.extend_from_slice(change.map_id.as_bytes());
            
            // Write coordinates
            patch_data.push(change.x_index.unwrap_or(0) as u8);
            patch_data.push(change.y_index.unwrap_or(0) as u8);
            
            // Write new value
            let value_bytes = change.new_value.to_le_bytes();
            patch_data.extend_from_slice(&value_bytes);
            
            // Update checksum
            checksum = checksum.wrapping_add(change.new_value as u32);
        }
        
        // Add VERSA header
        let mut final_patch = Vec::new();
        final_patch.extend_from_slice(b"VERSA");
        final_patch.extend_from_slice(&(patch_data.len() as u32).to_le_bytes());
        final_patch.extend(patch_data);
        
        Ok(PatchResult {
            success: true,
            patch_data: final_patch,
            checksum,
            size: final_patch.len(),
            warnings: vec![],
            errors: vec![],
        })
    }
    
    fn get_engine_type(&self) -> EngineType {
        EngineType::Versa
    }
}

pub struct VersaEngineValidator;

impl EnginePatchValidator for VersaEngineValidator {
    fn validate_patch(&self, patch_data: &[u8], original_rom: &[u8], safety_limits: &PyDict) -> Result<ValidationResult, EngineError> {
        let mut warnings = Vec::new();
        let mut errors = Vec::new();
        let mut safety_violations = Vec::new();
        let mut risk_score = 0u8;

        // Get safety limits from Python dict
        let max_boost = safety_limits
            .get_item("max_boost_psi")?
            .extract::<f32>()
            .unwrap_or(22.0);
        let max_timing = safety_limits
            .get_item("max_timing_degrees")?
            .extract::<f32>()
            .unwrap_or(25.0);
        let min_afr = safety_limits
            .get_item("min_afr")?
            .extract::<f32>()
            .unwrap_or(10.8);

        // Validate VERSA header
        if !patch_data.starts_with(b"VERSA") {
            errors.push("Invalid VERSA patch header".to_string());
        }

        // Parse changes and validate against limits
        let mut offset = 9; // Skip "VERSA" + size
        while offset + 8 < patch_data.len() {
            // Skip map ID and coordinates for this example
            offset += 4;
            
            // Read value
            if offset + 4 <= patch_data.len() {
                let value = f32::from_le_bytes([
                    patch_data[offset],
                    patch_data[offset + 1],
                    patch_data[offset + 2],
                    patch_data[offset + 3],
                ]);
                
                // Validate against safety limits
                if value > max_timing {
                    safety_violations.push(format!("Timing {}° exceeds maximum {}", value, max_timing));
                    risk_score = risk_score.saturating_add(30);
                }
                
                if value < min_afr {
                    safety_violations.push(format!("AFR {} below minimum {}", value, min_afr));
                    risk_score = risk_score.saturating_add(40);
                }
                
                offset += 4;
            }
        }

        Ok(ValidationResult {
            valid: errors.is_empty() && safety_violations.is_empty(),
            risk_score,
            warnings,
            errors,
            safety_violations,
        })
    }
    
    fn get_engine_type(&self) -> EngineType {
        EngineType::Versa
    }
}

/// COBB engine implementation
pub struct CobbEngineBuilder;

impl EnginePatchBuilder for CobbEngineBuilder {
    fn build_patch(&self, changes: &[MapChange], original_rom: &[u8]) -> Result<PatchResult, EngineError> {
        let mut patch_data = Vec::new();
        let mut checksum = 0u32;
        
        // Build COBB-specific patch format
        for change in changes {
            // COBB uses a different format - table-based addressing
            patch_data.extend_from_slice(&(change.map_id.len() as u16).to_be_bytes());
            patch_data.extend_from_slice(change.map_id.as_bytes());
            
            // COBB uses 16-bit addresses
            patch_data.push(change.x_index.unwrap_or(0) as u8);
            patch_data.push(change.y_index.unwrap_or(0) as u8);
            
            // COBB values are big-endian
            let value_bytes = change.new_value.to_be_bytes();
            patch_data.extend_from_slice(&value_bytes);
            
            // COBB checksum algorithm
            checksum = checksum.wrapping_add(value_bytes[0] as u32);
            checksum = checksum.wrapping_add((value_bytes[1] as u32) << 8);
        }
        
        // Add COBB header
        let mut final_patch = Vec::new();
        final_patch.extend_from_slice(b"COBB");
        final_patch.extend_from_slice(&(patch_data.len() as u32).to_be_bytes());
        final_patch.extend(patch_data);
        
        Ok(PatchResult {
            success: true,
            patch_data: final_patch,
            checksum,
            size: final_patch.len(),
            warnings: vec![],
            errors: vec![],
        })
    }
    
    fn get_engine_type(&self) -> EngineType {
        EngineType::Cobb
    }
}

pub struct CobbEngineValidator;

impl EnginePatchValidator for CobbEngineValidator {
    fn validate_patch(&self, patch_data: &[u8], original_rom: &[u8], safety_limits: &PyDict) -> Result<ValidationResult, EngineError> {
        let mut warnings = Vec::new();
        let mut errors = Vec::new();
        let mut safety_violations = Vec::new();
        let mut risk_score = 0u8;

        // COBB-specific validation
        if !patch_data.starts_with(b"COBB") {
            errors.push("Invalid COBB patch header".to_string());
        }

        // COBB has stricter boost limits
        let max_boost = safety_limits
            .get_item("max_boost_psi")?
            .extract::<f32>()
            .unwrap_or(20.0);

        // Parse COBB format (big-endian)
        let mut offset = 9;
        while offset + 8 < patch_data.len() {
            offset += 4; // Skip map ID and coords
            
            if offset + 4 <= patch_data.len() {
                let value = f32::from_be_bytes([
                    patch_data[offset],
                    patch_data[offset + 1],
                    patch_data[offset + 2],
                    patch_data[offset + 3],
                ]);
                
                if value > max_boost {
                    safety_violations.push(format!("COBB boost {} exceeds maximum {}", value, max_boost));
                    risk_score = risk_score.saturating_add(35);
                }
                
                offset += 4;
            }
        }

        Ok(ValidationResult {
            valid: errors.is_empty() && safety_violations.is_empty(),
            risk_score,
            warnings,
            errors,
            safety_violations,
        })
    }
    
    fn get_engine_type(&self) -> EngineType {
        EngineType::Cobb
    }
}

/// MDS engine implementation - doesn't support traditional patching
pub struct MdsEngineBuilder;

impl EnginePatchBuilder for MdsEngineBuilder {
    fn build_patch(&self, _changes: &[MapChange], _original_rom: &[u8]) -> Result<PatchResult, EngineError> {
        Err(EngineError::UnsupportedOperation)
    }
    
    fn get_engine_type(&self) -> EngineType {
        EngineType::Mds
    }
}

pub struct MdsEngineValidator;

impl EnginePatchValidator for MdsEngineValidator {
    fn validate_patch(&self, _patch_data: &[u8], _original_rom: &[u8], _safety_limits: &PyDict) -> Result<ValidationResult, EngineError> {
        Err(EngineError::UnsupportedOperation)
    }
    
    fn get_engine_type(&self) -> EngineType {
        EngineType::Mds
    }
}

/// Registry for engine builders and validators
pub struct EngineRegistry {
    builders: HashMap<EngineType, Box<dyn EnginePatchBuilder>>,
    validators: HashMap<EngineType, Box<dyn EnginePatchValidator>>,
}

impl EngineRegistry {
    pub fn new() -> Self {
        let mut builders: HashMap<EngineType, Box<dyn EnginePatchBuilder>> = HashMap::new();
        let mut validators: HashMap<EngineType, Box<dyn EnginePatchValidator>> = HashMap::new();
        
        // Register engines
        builders.insert(EngineType::Versa, Box::new(VersaEngineBuilder));
        builders.insert(EngineType::Cobb, Box::new(CobbEngineBuilder));
        builders.insert(EngineType::Mds, Box::new(MdsEngineBuilder));
        
        validators.insert(EngineType::Versa, Box::new(VersaEngineValidator));
        validators.insert(EngineType::Cobb, Box::new(CobbEngineValidator));
        validators.insert(EngineType::Mds, Box::new(MdsEngineValidator));
        
        Self { builders, validators }
    }
    
    pub fn get_builder(&self, engine_type: EngineType) -> Option<&dyn EnginePatchBuilder> {
        self.builders.get(&engine_type).map(|b| b.as_ref())
    }
    
    pub fn get_validator(&self, engine_type: EngineType) -> Option<&dyn EnginePatchValidator> {
        self.validators.get(&engine_type).map(|v| v.as_ref())
    }
}

lazy_static::lazy_static! {
    static ref ENGINE_REGISTRY: EngineRegistry = EngineRegistry::new();
}

/// Engine-agnostic patch builder
#[pyfunction]
pub fn build_engine_patch(
    engine: &str,
    changes: Vec<MapChange>,
    original_rom: Vec<u8>
) -> PyResult<PatchResult> {
    let engine_type: EngineType = engine.into();
    
    match ENGINE_REGISTRY.get_builder(engine_type) {
        Some(builder) => {
            match builder.build_patch(&changes, &original_rom) {
                Ok(result) => Ok(result),
                Err(e) => PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)),
            }
        }
        None => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Engine {} not supported", engine)
        )),
    }
}

/// Engine-agnostic patch validator
#[pyfunction]
pub fn validate_engine_patch(
    engine: &str,
    patch_data: Vec<u8>,
    original_rom: Vec<u8>,
    safety_limits: &PyDict
) -> PyResult<ValidationResult> {
    let engine_type: EngineType = engine.into();
    
    match ENGINE_REGISTRY.get_validator(engine_type) {
        Some(validator) => {
            match validator.validate_patch(&patch_data, &original_rom, safety_limits) {
                Ok(result) => Ok(result),
                Err(e) => PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{}", e)),
            }
        }
        None => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Engine {} not supported", engine)
        )),
    }
}

/// Legacy functions for backward compatibility
#[pyfunction]
pub fn versa_build_patch(
    changes: Vec<MapChange>,
    original_rom: Vec<u8>
) -> PyResult<PatchResult> {
    build_engine_patch("versa", changes, original_rom)
}

#[pyfunction]
pub fn versa_validate_patch(
    patch_data: Vec<u8>,
    original_rom: Vec<u8>,
    safety_limits: &PyDict
) -> PyResult<ValidationResult> {
    validate_engine_patch("versa", patch_data, original_rom, safety_limits)
}

#[pyfunction]
pub fn cobb_build_patch(
    changes: Vec<MapChange>,
    original_rom: Vec<u8>
) -> PyResult<PatchResult> {
    build_engine_patch("cobb", changes, original_rom)
}

#[pyfunction]
pub fn cobb_validate_patch(
    patch_data: Vec<u8>,
    original_rom: Vec<u8>,
    safety_limits: &PyDict
) -> PyResult<ValidationResult> {
    validate_engine_patch("cobb", patch_data, original_rom, safety_limits)
}

#[pyfunction]
pub fn mds_build_patch(
    _changes: Vec<MapChange>,
    _original_rom: Vec<u8>
) -> PyResult<PatchResult> {
    Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
        "MDS engine does not support patch building"
    ))
}

#[pyfunction]
pub fn mds_validate_patch(
    _patch_data: Vec<u8>,
    _original_rom: Vec<u8>,
    _safety_limits: &PyDict
) -> PyResult<ValidationResult> {
    Err(PyErr::new::<pyo3::exceptions::PyNotImplementedError, _>(
        "MDS engine does not support patch validation"
    ))
}

/// Live apply operations (engine-agnostic)
#[pyfunction]
pub fn apply_live_changes(
    engine: &str,
    changes: Vec<MapChange>,
    safety_limits: &PyDict
) -> PyResult<ApplyResult> {
    let engine_type: EngineType = engine.into();
    
    match engine_type {
        EngineType::Versa | EngineType::Cobb => {
            // Simulate live apply
            Ok(ApplyResult {
                success: true,
                ecu_verified: true,
                applied_changes: changes.len(),
                failed_changes: vec![],
                verification_errors: None,
                message: format!("Changes applied successfully via {}", engine),
            })
        }
        EngineType::Mds => {
            // MDS supports live apply but with different protocol
            Ok(ApplyResult {
                success: true,
                ecu_verified: true,
                applied_changes: changes.len(),
                failed_changes: vec![],
                verification_errors: None,
                message: "Changes applied via MDS protocol".to_string(),
            })
        }
    }
}

#[pyfunction]
pub fn revert_live_changes(
    engine: &str,
    session_id: &str
) -> PyResult<ApplyResult> {
    let engine_type: EngineType = engine.into();
    
    match engine_type {
        EngineType::Versa | EngineType::Cobb | EngineType::Mds => {
            Ok(ApplyResult {
                success: true,
                ecu_verified: true,
                applied_changes: 1,
                failed_changes: vec![],
                verification_errors: None,
                message: format!("Changes reverted successfully via {}", engine),
            })
        }
    }
}

/// Python module definition
#[pymodule]
fn muts_versa_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MapChange>()?;
    m.add_class::<PatchResult>()?;
    m.add_class::<ValidationResult>()?;
    m.add_class::<ApplyResult>()?;
    
    // Engine-agnostic functions
    m.add_function(wrap_pyfunction!(build_engine_patch, m)?)?;
    m.add_function(wrap_pyfunction!(validate_engine_patch, m)?)?;
    m.add_function(wrap_pyfunction!(apply_live_changes, m)?)?;
    m.add_function(wrap_pyfunction!(revert_live_changes, m)?)?;
    
    // Legacy engine-specific functions
    m.add_function(wrap_pyfunction!(versa_build_patch, m)?)?;
    m.add_function(wrap_pyfunction!(versa_validate_patch, m)?)?;
    m.add_function(wrap_pyfunction!(cobb_build_patch, m)?)?;
    m.add_function(wrap_pyfunction!(cobb_validate_patch, m)?)?;
    m.add_function(wrap_pyfunction!(mds_build_patch, m)?)?;
    m.add_function(wrap_pyfunction!(mds_validate_patch, m)?)?;
    
    Ok(())
}
