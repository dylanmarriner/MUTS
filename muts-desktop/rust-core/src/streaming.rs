/**
 * Streaming telemetry implementation
 * Provides real-time data from the vehicle
 */

use crate::types::*;
use crate::hardware::InterfaceHandle;
use crate::MutsCoreState;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{RwLock, broadcast};
use tokio::time::{interval, Duration};
use tracing::{info, warn, error};
use chrono::Utc;

/// Streaming configuration
#[derive(Debug, Clone)]
pub struct StreamingConfig {
    pub sample_rate_hz: f64,
    pub enabled_signals: Vec<String>,
    pub can_filters: Vec<u32>,
}

impl Default for StreamingConfig {
    fn default() -> Self {
        Self {
            sample_rate_hz: 10.0,
            enabled_signals: vec![
                "engine_rpm".to_string(),
                "vehicle_speed".to_string(),
                "boost_pressure".to_string(),
                "maf_airflow".to_string(),
                "throttle_position".to_string(),
                "lambda".to_string(),
                "ignition_timing".to_string(),
                "iat".to_string(),
                "ect".to_string(),
                "fuel_pressure".to_string(),
            ],
            can_filters: vec![0x7E8, 0x7E9, 0x7EA], // Common ECU responses
        }
    }
}

/// Signal decoder for CAN data
pub struct SignalDecoder {
    signal_definitions: HashMap<String, SignalDefinition>,
}

#[derive(Debug, Clone)]
pub struct SignalDefinition {
    pub can_id: u32,
    pub start_bit: u8,
    pub length: u8,
    pub factor: f64,
    pub offset: f64,
    pub unit: String,
    pub endian: Endianness,
}

#[derive(Debug, Clone)]
pub enum Endianness {
    Little,
    Big,
}

impl SignalDecoder {
    pub fn new() -> Self {
        let mut definitions = HashMap::new();
        
        // Define common Mazda Speed3 signals
        definitions.insert("engine_rpm".to_string(), SignalDefinition {
            can_id: 0x7E8,
            start_bit: 24,
            length: 16,
            factor: 0.25,
            offset: 0.0,
            unit: "RPM".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("vehicle_speed".to_string(), SignalDefinition {
            can_id: 0x7E8,
            start_bit: 40,
            length: 16,
            factor: 0.01,
            offset: 0.0,
            unit: "km/h".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("boost_pressure".to_string(), SignalDefinition {
            can_id: 0x7E9,
            start_bit: 16,
            length: 16,
            factor: 0.01,
            offset: 101.3,
            unit: "kPa".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("maf_airflow".to_string(), SignalDefinition {
            can_id: 0x7E9,
            start_bit: 32,
            length: 16,
            factor: 0.01,
            offset: 0.0,
            unit: "g/s".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("throttle_position".to_string(), SignalDefinition {
            can_id: 0x7EA,
            start_bit: 0,
            length: 8,
            factor: 0.392,
            offset: 0.0,
            unit: "%".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("lambda".to_string(), SignalDefinition {
            can_id: 0x7EA,
            start_bit: 8,
            length: 8,
            factor: 0.0078,
            offset: 0.0,
            unit: "lambda".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("ignition_timing".to_string(), SignalDefinition {
            can_id: 0x7EA,
            start_bit: 16,
            length: 8,
            factor: 1.0,
            offset: -40.0,
            unit: "°".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("iat".to_string(), SignalDefinition {
            can_id: 0x7EA,
            start_bit: 24,
            length: 8,
            factor: 1.0,
            offset: -40.0,
            unit: "°C".to_string(),
            endian: Endianness::Big,
        });
        
        definitions.insert("ect".to_string(), SignalDefinition {
            can_id: 0x7EA,
            start_bit: 32,
            length: 8,
            factor: 1.0,
            offset: -40.0,
            unit: "°C".to_string(),
            endian: Endianness::Big,
        });
        
        Self {
            signal_definitions: definitions,
        }
    }
    
    pub fn decode_frame(&self, frame: &CanFrame) -> HashMap<String, f64> {
        let mut signals = HashMap::new();
        
        for (name, definition) in &self.signal_definitions {
            if definition.can_id == frame.id {
                if let Some(value) = self.extract_signal(frame.data.as_slice(), definition) {
                    signals.insert(name.clone(), value);
                }
            }
        }
        
        signals
    }
    
    fn extract_signal(&self, data: &[u8], definition: &SignalDefinition) -> Option<f64> {
        let byte_offset = definition.start_bit / 8;
        let bit_offset = definition.start_bit % 8;
        
        if byte_offset + ((definition.length + bit_offset + 7) / 8) > data.len() {
            return None;
        }
        
        let mut raw_value: u64 = 0;
        let mut bits_extracted = 0;
        
        for i in 0..definition.length {
            let bit_pos = definition.start_bit + i;
            let byte_pos = bit_pos / 8;
            let bit_in_byte = 7 - (bit_pos % 8); // MSB first
            
            if data[byte_pos] & (1 << bit_in_byte) != 0 {
                raw_value |= 1 << i;
            }
        }
        
        let scaled_value = (raw_value as f64) * definition.factor + definition.offset;
        Some(scaled_value)
    }
}

/// Streaming manager
pub struct StreamingManager {
    config: StreamingConfig,
    decoder: SignalDecoder,
    interface: InterfaceHandle,
    core_state: Arc<MutsCoreState>,
    running: Arc<RwLock<bool>>,
}

impl StreamingManager {
    pub fn new(
        config: StreamingConfig,
        interface: InterfaceHandle,
        core_state: Arc<MutsCoreState>,
    ) -> Self {
        Self {
            config,
            decoder: SignalDecoder::new(),
            interface,
            core_state,
            running: Arc::new(RwLock::new(false)),
        }
    }
    
    pub async fn start(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        {
            let mut running = self.running.write().await;
            if *running {
                return Err("Already streaming".into());
            }
            *running = true;
        }
        
        info!("Starting telemetry stream at {} Hz", self.config.sample_rate_hz);
        
        let config = self.config.clone();
        let decoder = self.decoder.clone();
        let interface = self.interface.clone();
        let core_state = self.core_state.clone();
        let running = self.running.clone();
        
        tokio::spawn(async move {
            let interval_duration = Duration::from_secs_f64(1.0 / config.sample_rate_hz);
            let mut interval = interval(interval_duration);
            
            let mut last_values: HashMap<String, f64> = HashMap::new();
            
            while *running.read().await {
                interval.tick().await;
                
                // Collect CAN frames
                let mut frame_buffer = Vec::new();
                let timeout = Duration::from_millis(10);
                
                // Try to receive multiple frames
                for _ in 0..10 {
                    match interface.receive_frame(timeout.as_millis() as u64).await {
                        Ok(Some(frame)) => {
                            frame_buffer.push(frame);
                        },
                        Ok(None) => break, // No more frames
                        Err(_) => break,
                    }
                }
                
                // Decode signals
                let mut signals = HashMap::new();
                for frame in &frame_buffer {
                    let frame_signals = decoder.decode_frame(frame);
                    signals.extend(frame_signals);
                    
                    // Broadcast raw frame
                    let broadcasters = core_state.event_broadcasters.read().await;
                    let _ = broadcasters.can_frames.send(frame.clone());
                }
                
                // Filter enabled signals
                let filtered_signals: HashMap<String, f64> = config.enabled_signals
                    .iter()
                    .filter_map(|name| {
                        signals.get(name).map(|value| (name.clone(), *value))
                    })
                    .collect();
                
                // Check for changes (only send if values changed)
                let has_changes = filtered_signals.iter()
                    .any(|(name, value)| {
                        last_values.get(name).map_or(true, |last| {
                            (last - value).abs() > 0.01 // Small threshold
                        })
                    });
                
                if has_changes || signals.is_empty() {
                    last_values = filtered_signals.clone();
                    
                    // Create telemetry data
                    let telemetry = TelemetryData {
                        timestamp: Utc::now(),
                        signals: filtered_signals,
                        metadata: TelemetryMetadata {
                            source: "CAN".to_string(),
                            sample_rate: config.sample_rate_hz,
                            quality: if signals.is_empty() {
                                SignalQuality::Invalid
                            } else {
                                SignalQuality::Good
                            },
                        },
                    };
                    
                    // Broadcast telemetry
                    let broadcasters = core_state.event_broadcasters.read().await;
                    let _ = broadcasters.telemetry.send(telemetry);
                }
            }
            
            info!("Telemetry stream stopped");
        });
        
        Ok(())
    }
    
    pub async fn stop(&self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut running = self.running.write().await;
        *running = false;
        info!("Stopping telemetry stream");
        Ok(())
    }
    
    pub async fn is_running(&self) -> bool {
        *self.running.read().await
    }
}

/// Start streaming (public API)
pub async fn start_streaming(
    core_state: Arc<MutsCoreState>,
    interface: InterfaceHandle,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let config = StreamingConfig::default();
    let manager = StreamingManager::new(config, interface, core_state);
    manager.start().await
}

/// Stop streaming (public API)
pub async fn stop_streaming(
    interface: &InterfaceHandle,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // This would need to track the streaming manager
    // For now, just log
    info!("Stopping streaming (not fully implemented)");
    Ok(())
}
