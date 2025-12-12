/**
 * Diagnostic protocol implementation
 * Supports ISO-TP, UDS, and manufacturer-specific protocols
 */

use crate::types::*;
use crate::hardware::InterfaceHandle;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, warn, error};
use chrono::Utc;
use uuid::Uuid;

/// Diagnostic session information
#[derive(Debug, Clone)]
pub struct DiagnosticSession {
    pub id: String,
    pub session_type: String,
    pub start_time: chrono::DateTime<Utc>,
    pub active: bool,
}

/// Diagnostic protocol handler
pub struct DiagnosticProtocol {
    sessions: Arc<RwLock<HashMap<String, DiagnosticSession>>>,
    interface: InterfaceHandle,
}

impl DiagnosticProtocol {
    pub fn new(interface: InterfaceHandle) -> Self {
        Self {
            sessions: Arc::new(RwLock::new(HashMap::new())),
            interface,
        }
    }
    
    /// Start a new diagnostic session
    pub async fn start_session(&self, session_type: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let session_id = Uuid::new_v4().to_string();
        
        // Send diagnostic session control request
        let session_request = vec![
            0x10, // DiagnosticSessionControl
            match session_type {
                "default" => 0x01,
                "programming" => 0x02,
                "extended" => 0x03,
                _ => 0x01,
            }
        ];
        
        let response = self.send_request(0x10, Some(session_request)).await?;
        
        if !response.success {
            return Err("Failed to start diagnostic session".into());
        }
        
        // Store session
        let session = DiagnosticSession {
            id: session_id.clone(),
            session_type: session_type.to_string(),
            start_time: Utc::now(),
            active: true,
        };
        
        let mut sessions = self.sessions.write().await;
        sessions.insert(session_id.clone(), session);
        
        info!("Started diagnostic session: {} ({})", session_id, session_type);
        Ok(session_id)
    }
    
    /// Send a diagnostic request
    pub async fn send_request(
        &self,
        service_id: u8,
        data: Option<Vec<u8>>,
    ) -> Result<DiagnosticResponse, Box<dyn std::error::Error + Send + Sync>> {
        let start_time = std::time::Instant::now();
        
        // Build ISO-TP message
        let mut message = Vec::new();
        message.push(service_id);
        if let Some(data) = data {
            message.extend(data);
        }
        
        // Send via ISO-TP on CAN (simplified)
        let can_frames = self.build_iso_tp_frames(&message)?;
        
        for frame in can_frames {
            self.interface.send_frame(&frame).await?;
            
            // Wait for acknowledgment if needed
            if frame.data.len() < 8 {
                tokio::time::sleep(std::time::Duration::from_millis(10)).await;
            }
        }
        
        // Wait for response
        let response = self.wait_for_response(service_id + 0x40).await?;
        
        let elapsed = start_time.elapsed();
        
        Ok(DiagnosticResponse {
            service_id: response[0],
            data: response.into_iter().skip(1).collect(),
            success: true,
            timestamp: Utc::now(),
            response_time_ms: elapsed.as_millis() as u64,
        })
    }
    
    /// Build ISO-TP frames from message
    fn build_iso_tp_frames(&self, message: &[u8]) -> Result<Vec<CanFrame>, Box<dyn std::error::Error + Send + Sync>> {
        let mut frames = Vec::new();
        
        if message.len() <= 7 {
            // Single frame
            frames.push(CanFrame {
                id: 0x7E0, // ECU request ID
                extended: false,
                data: {
                    let mut data = vec![message.len() as u8];
                    data.extend(message);
                    data
                },
                timestamp: Utc::now(),
            });
        } else {
            // First frame
            frames.push(CanFrame {
                id: 0x7E0,
                extended: false,
                data: {
                    let mut data = vec![0x10 | ((message.len() >> 8) & 0x0F) as u8, message.len() as u8];
                    data.extend(&message[..6]);
                    data
                },
                timestamp: Utc::now(),
            });
            
            // Consecutive frames
            let mut sequence = 1;
            for chunk in message[6..].chunks(7) {
                let mut data = vec![0x20 | (sequence & 0x0F) as u8];
                data.extend(chunk);
                frames.push(CanFrame {
                    id: 0x7E0,
                    extended: false,
                    data,
                    timestamp: Utc::now(),
                });
                sequence += 1;
            }
        }
        
        Ok(frames)
    }
    
    /// Wait for diagnostic response
    async fn wait_for_response(&self, expected_service: u8) -> Result<Vec<u8>, Box<dyn std::error::Error + Send + Sync>> {
        let timeout = std::time::Duration::from_secs(2);
        let start = std::time::Instant::now();
        
        while start.elapsed() < timeout {
            if let Some(frame) = self.interface.receive_frame(100).await? {
                if frame.id == 0x7E8 && !frame.data.is_empty() {
                    let first_byte = frame.data[0];
                    
                    if (first_byte & 0xF0) == 0x00 {
                        // Single frame response
                        if frame.data.len() > 1 && frame.data[1] == expected_service {
                            return Ok(frame.data[2..].to_vec());
                        }
                    } else if (first_byte & 0xF0) == 0x10 {
                        // First frame of multi-frame response
                        let length = ((first_byte & 0x0F) as usize) << 8 | frame.data[1] as usize;
                        let mut response = frame.data[2..].to_vec();
                        
                        // Receive remaining frames
                        let mut sequence = 1;
                        while response.len() < length {
                            if let Some(frame) = self.interface.receive_frame(100).await? {
                                if frame.id == 0x7E8 && !frame.data.is_empty() {
                                    let seq_byte = frame.data[0];
                                    if (seq_byte & 0xF0) == 0x20 && (seq_byte & 0x0F) == sequence {
                                        response.extend(&frame.data[1..]);
                                        sequence += 1;
                                    }
                                }
                            }
                        }
                        
                        if !response.is_empty() && response[0] == expected_service {
                            return Ok(response[1..].to_vec());
                        }
                    }
                }
            }
        }
        
        Err("Timeout waiting for response".into())
    }
    
    /// End diagnostic session
    pub async fn end_session(&self, session_id: &str) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // Send end session request
        let _ = self.send_request(0x10, Some(vec![0x01])).await;
        
        let mut sessions = self.sessions.write().await;
        if let Some(mut session) = sessions.remove(session_id) {
            session.active = false;
            info!("Ended diagnostic session: {}", session_id);
        }
        
        Ok(())
    }
}

/// Start diagnostic session (public API)
pub async fn start_session(
    interface: &InterfaceHandle,
    session_type: &str,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let protocol = DiagnosticProtocol::new(interface.clone());
    protocol.start_session(session_type).await
}

/// Send diagnostic request (public API)
pub async fn send_request(
    interface: &InterfaceHandle,
    service_id: u8,
    data: Option<Vec<u8>>,
) -> Result<DiagnosticResponse, Box<dyn std::error::Error + Send + Sync>> {
    let protocol = DiagnosticProtocol::new(interface.clone());
    protocol.send_request(service_id, data).await
}

/// Common diagnostic service IDs
pub mod services {
    pub const DIAGNOSTIC_SESSION_CONTROL: u8 = 0x10;
    pub const ECU_RESET: u8 = 0x11;
    pub const SECURITY_ACCESS: u8 = 0x27;
    pub const READ_DATA_BY_IDENTIFIER: u8 = 0x22;
    pub const READ_MEMORY_BY_ADDRESS: u8 = 0x23;
    pub const WRITE_DATA_BY_IDENTIFIER: u8 = 0x2E;
    pub const WRITE_MEMORY_BY_ADDRESS: u8 = 0x3D;
    pub const TESTER_PRESENT: u8 = 0x3E;
    pub const READ_DTC: u8 = 0x19;
    pub const CLEAR_DTC: u8 = 0x14;
}

/// Common data identifiers
pub mod identifiers {
    pub const VIN: u16 = 0xF190;
    pub const CALIBRATION_ID: u16 = 0xF18A;
    pub const CALIBRATION_VERIFICATION: u16 = 0xF18B;
    pub const ECU_NAME: u16 = 0xF18C;
    pub const ACTIVE_DIAGNOSTIC_SESSION: u16 = 0xF194;
}
