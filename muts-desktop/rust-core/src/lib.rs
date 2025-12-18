/**
 * MUTS Core - Safety-critical ECU operations
 * Provides hardware abstraction and streaming capabilities
 */

use napi::bindgen_prelude::*;
use napi_derive::napi;
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use tokio::sync::{broadcast, RwLock};
use tracing::{info, error, warn};
use chrono::{DateTime, Utc};
use uuid::Uuid;

mod hardware;
mod diagnostics;
mod streaming;
mod flash;
mod flash_supervisor;
mod safety;
mod types;
mod event_bus;

pub use hardware::*;
pub use diagnostics::*;
pub use streaming::*;
pub use flash::*;
pub use flash_supervisor::*;
pub use safety::*;
pub use types::*;
pub use event_bus::*;

/// Global state for the MUTS core
pub struct MutsCoreState {
    /// Current interface connection
    interface: Arc<RwLock<Option<InterfaceHandle>>>,
    /// Event bus for prioritized events
    event_bus: Arc<EventBus>,
    /// Flash supervisor for deterministic operations
    flash_supervisor: Arc<FlashSupervisor>,
    /// Safety system state
    safety_state: Arc<RwLock<SafetyState>>,
    /// Active sessions
    sessions: Arc<RwLock<HashMap<String, SessionInfo>>>,
}

/// Global MUTS core instance
static MUTS_CORE: std::sync::OnceLock<Arc<MutsCoreState>> = std::sync::OnceLock::new();

/// Initialize the MUTS core system
#[napi]
pub async fn initialize_core() -> Result<()> {
    // Initialize logging
    #[cfg(feature = "tracing-subscriber")]
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    info!("Initializing MUTS core");

    // Create event bus with memory persistence
    let config = EventBusConfig::default();
    let persistence = Arc::new(MemoryPersistence::new());
    let event_bus = Arc::new(EventBus::new(config, persistence));

    // Create flash supervisor
    let flash_config = FlashSupervisorConfig::default();
    let flash_supervisor = Arc::new(FlashSupervisor::new(flash_config, event_bus.clone()));

    // Initialize core state
    let core_state = Arc::new(MutsCoreState {
        interface: Arc::new(RwLock::new(None)),
        event_bus,
        flash_supervisor,
        safety_state: Arc::new(RwLock::new(SafetyState::new())),
        sessions: Arc::new(RwLock::new(HashMap::new())),
    });

    // Store in global
    MUTS_CORE.set(core_state).map_err(|_| {
        Error::new(
            Status::GenericFailure,
            "MUTS core already initialized".to_string(),
        )
    })?;

    info!("MUTS core initialized successfully");
    Ok(())
}

/// List available hardware interfaces
#[napi]
pub async fn list_interfaces() -> Result<Vec<InterfaceInfo>> {
    let interfaces = hardware::scan_interfaces().await?;
    Ok(interfaces)
}

/// Connect to a hardware interface
#[napi]
pub async fn connect_interface(interface_id: String) -> Result<ConnectionResult> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    // Check safety state
    let safety_state = core.safety_state.read().await;
    if !safety_state.can_connect() {
        return Err(Error::new(
            Status::GenericFailure,
            "Cannot connect: Safety system prevents connection",
        ));
    }
    drop(safety_state);

    // Attempt connection
    let handle = hardware::connect_interface(&interface_id).await?;
    
    // Store interface
    let mut interface_guard = core.interface.write().await;
    *interface_guard = Some(handle.clone());

    // Start streaming if connection successful
    if handle.is_connected() {
        streaming::start_streaming(core.clone(), handle.clone()).await?;
        
        // Create session
        let session_id = Uuid::new_v4().to_string();
        let session = SessionInfo {
            id: session_id.clone(),
            interface_id: interface_id.clone(),
            start_time: Utc::now(),
            status: SessionStatus::Active,
        };
        
        let mut sessions = core.sessions.write().await;
        sessions.insert(session_id.clone(), session);

        Ok(ConnectionResult {
            success: true,
            session_id,
            message: "Connected successfully".to_string(),
        })
    } else {
        Err(Error::new(
            Status::GenericFailure,
            "Failed to establish connection".to_string(),
        ))
    }
}

/// Disconnect from current interface
#[napi]
pub async fn disconnect_interface() -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let mut interface_guard = core.interface.write().await;
    if let Some(handle) = interface_guard.take() {
        // Stop streaming
        streaming::stop_streaming(&handle).await?;
        
        // Disconnect hardware
        hardware::disconnect_interface(handle).await?;
        
        // Clear active sessions
        let mut sessions = core.sessions.write().await;
        sessions.clear();
        
        info!("Disconnected from interface");
    }

    Ok(())
}

/// Get current connection status
#[napi]
pub async fn get_connection_status() -> Result<ConnectionStatus> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let interface_guard = core.interface.read().await;
    
    if let Some(handle) = interface_guard.as_ref() {
        let sessions = core.sessions.read().await;
        let session_count = sessions.len();
        
        Ok(ConnectionStatus {
            connected: handle.is_connected(),
            interface_id: handle.get_id(),
            session_count: session_count as u32,
            last_activity: handle.get_last_activity(),
        })
    } else {
        Ok(ConnectionStatus {
            connected: false,
            interface_id: "NO_INTERFACE_CONNECTED".to_string(),
            session_count: 0,
            last_activity: None,
        })
    }
}

/// Start diagnostic session
#[napi]
pub async fn start_diagnostic_session(session_type: String) -> Result<String> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let interface_guard = core.interface.read().await;
    let handle = interface_guard.as_ref().ok_or_else(|| {
        Error::new(Status::GenericFailure, "No interface connected")
    })?;

    if !handle.is_connected() {
        return Err(Error::new(
            Status::GenericFailure,
            "Interface not connected".to_string(),
        ));
    }

    // Start diagnostic session
    let session_id = diagnostics::start_session(handle, &session_type).await?;
    
    info!("Started diagnostic session: {}", session_id);
    Ok(session_id)
}

/// Send diagnostic request
#[napi]
pub async fn send_diagnostic_request(
    service_id: u8,
    data: Option<Vec<u8>>,
) -> Result<DiagnosticResponse> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let interface_guard = core.interface.read().await;
    let handle = interface_guard.as_ref().ok_or_else(|| {
        Error::new(Status::GenericFailure, "No interface connected")
    })?;

    if !handle.is_connected() {
        return Err(Error::new(
            Status::GenericFailure,
            "Interface not connected".to_string(),
        ));
    }

    // Send request
    let response = diagnostics::send_request(handle, service_id, data).await?;
    
    // Broadcast response
    let broadcasters = core.event_broadcasters.read().await;
    let _ = broadcasters.diag_responses.send(response.clone());

    Ok(response)
}

/// Validate ROM image
#[napi]
pub async fn validate_rom(rom_data: Vec<u8>) -> Result<RomValidationResult> {
    let result = flash::validate_rom(&rom_data).await?;
    Ok(result)
}

/// Verify ROM checksum
#[napi]
pub async fn verify_checksum(rom_data: Vec<u8>) -> Result<ChecksumResult> {
    let result = flash::verify_checksum(&rom_data).await?;
    Ok(result)
}

/// Prepare flash operation
#[napi]
pub async fn prepare_flash(
    rom_data: Vec<u8>,
    options: FlashOptions,
) -> Result<FlashPrepareResult> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    // Check safety state
    let safety_state = core.safety_state.read().await;
    if !safety_state.can_flash() {
        return Err(Error::new(
            Status::GenericFailure,
            "Cannot flash: Safety system not armed",
        ));
    }
    drop(safety_state);

    let interface_guard = core.interface.read().await;
    let handle = interface_guard.as_ref().ok_or_else(|| {
        Error::new(Status::GenericFailure, "No interface connected")
    })?;

    // Prepare flash
    let result = flash::prepare_flash(handle, rom_data, options).await?;
    
    info!("Flash prepared with job ID: {}", result.job_id);
    Ok(result)
}

/// Execute flash operation
#[napi]
pub async fn execute_flash(job_id: String) -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    // Start flash in background
    let core_clone = core.clone();
    tokio::spawn(async move {
        if let Err(e) = flash::execute_flash(&core_clone, &job_id).await {
            error!("Flash execution failed: {}", e);
        }
    });

    Ok(())
}

/// Abort flash operation
#[napi]
pub async fn abort_flash(job_id: String) -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    flash::abort_flash(&core, &job_id).await?;
    info!("Flash aborted: {}", job_id);
    
    Ok(())
}

/// Apply live changes
#[napi]
pub async fn apply_live_changes(changes: Vec<LiveChange>) -> Result<ApplyResult> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    // Check safety state
    let safety_state = core.safety_state.read().await;
    if !safety_state.can_apply_live() {
        return Err(Error::new(
            Status::GenericFailure,
            "Cannot apply changes: Safety system not armed",
        ));
    }
    drop(safety_state);

    let interface_guard = core.interface.read().await;
    let handle = interface_guard.as_ref().ok_or_else(|| {
        Error::new(Status::GenericFailure, "No interface connected")
    })?;

    // Apply changes
    let result = flash::apply_live(handle, changes).await?;
    
    info!("Applied {} live changes", result.changes_applied);
    Ok(result)
}

/// Revert live changes
#[napi]
pub async fn revert_live_changes(session_id: String) -> Result<RevertResult> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let interface_guard = core.interface.read().await;
    let handle = interface_guard.as_ref().ok_or_else(|| {
        Error::new(Status::GenericFailure, "No interface connected")
    })?;

    // Revert changes
    let result = flash::revert_live(handle, &session_id).await?;
    
    info!("Reverted live changes for session: {}", session_id);
    Ok(result)
}

/// Arm safety system
#[napi]
pub async fn arm_safety(level: SafetyLevel) -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let mut safety_state = core.safety_state.write().await;
    safety_state.arm(level).await?;
    
    // Broadcast safety event
    let broadcasters = core.event_broadcasters.read().await;
    let _ = broadcasters.safety_events.send(SafetyEvent {
        event_type: SafetyEventType::Armed,
        level: level.clone(),
        message: format!("Safety system armed at level: {:?}", level),
        timestamp: Utc::now(),
    });

    info!("Safety system armed at level: {:?}", level);
    Ok(())
}

/// Disarm safety system
#[napi]
pub async fn disarm_safety() -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let mut safety_state = core.safety_state.write().await;
    safety_state.disarm().await?;
    
    // Broadcast safety event
    let broadcasters = core.event_broadcasters.read().await;
    let _ = broadcasters.safety_events.send(SafetyEvent {
        event_type: SafetyEventType::Disarmed,
        level: SafetyLevel::ReadOnly,
        message: "Safety system disarmed".to_string(),
        timestamp: Utc::now(),
    });

    info!("Safety system disarmed");
    Ok(())
}

/// Get current safety state
#[napi]
pub async fn get_safety_state() -> Result<SafetyStateInfo> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let safety_state = core.safety_state.read().await;
    Ok(safety_state.get_info().clone())
}

/// Prepare flash job
#[napi]
pub async fn flash_prepare(job_id: String, rom_data: Buffer) -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let command = FlashCommand::Prepare {
        job_id,
        rom_data: rom_data.to_vec(),
    };
    
    core.flash_supervisor.command_sender().send(command)
        .map_err(|_| Error::new(Status::GenericFailure, "Failed to send prepare command"))?;
    
    Ok(())
}

/// Start flash job
#[napi]
pub async fn flash_start(job_id: String) -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let command = FlashCommand::Start { job_id };
    
    core.flash_supervisor.command_sender().send(command)
        .map_err(|_| Error::new(Status::GenericFailure, "Failed to send start command"))?;
    
    Ok(())
}

/// Abort flash job
#[napi]
pub async fn flash_abort(job_id: String) -> Result<()> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let command = FlashCommand::Abort { job_id };
    
    core.flash_supervisor.command_sender().send(command)
        .map_err(|_| Error::new(Status::GenericFailure, "Failed to send abort command"))?;
    
    Ok(())
}

/// Get flash job status
#[napi]
pub async fn flash_get_status(job_id: String) -> Result<FlashStatus> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    let (tx, rx) = oneshot::channel();
    let command = FlashCommand::GetStatus { job_id, response: tx };
    
    core.flash_supervisor.command_sender().send(command)
        .map_err(|_| Error::new(Status::GenericFailure, "Failed to send status request"))?;
    
    rx.await.map_err(|_| Error::new(Status::GenericFailure, "Status request timed out"))
}

/// Get all flash job statuses
#[napi]
pub async fn flash_get_all_statuses() -> Result<Vec<FlashStatus>> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    Ok(core.flash_supervisor.get_all_statuses().await)
}

/// Get flash supervisor metrics
#[napi]
pub async fn flash_get_metrics() -> Result<FlashMetrics> {
    let core = MUTS_CORE.get().ok_or_else(|| {
        Error::new(Status::GenericFailure, "MUTS core not initialized")
    })?;

    Ok(core.flash_supervisor.get_metrics().await)
}
