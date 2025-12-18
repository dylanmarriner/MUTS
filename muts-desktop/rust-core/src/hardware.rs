/**
 * Hardware interface abstraction layer
 * Supports CAN, J2534, and other interfaces
 */

use crate::types::*;
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{Mutex, RwLock};
use tracing::{info, warn, error};
use chrono::Utc;

#[cfg(feature = "socketcan")]
use can;

/// Hardware interface trait
#[async_trait]
pub trait HardwareInterface: Send + Sync {
    /// Get interface ID
    fn get_id(&self) -> String;
    
    /// Get interface type
    fn get_type(&self) -> InterfaceType;
    
    /// Check if connected
    async fn is_connected(&self) -> bool;
    
    /// Connect to interface
    async fn connect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;
    
    /// Disconnect from interface
    async fn disconnect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;
    
    /// Send CAN frame
    async fn send_can_frame(&self, frame: &CanFrame) -> Result<(), Box<dyn std::error::Error + Send + Sync>>;
    
    /// Receive CAN frame (with timeout)
    async fn receive_can_frame(&self, timeout_ms: u64) -> Result<Option<CanFrame>, Box<dyn std::error::Error + Send + Sync>>;
    
    /// Get interface capabilities
    fn get_capabilities(&self) -> Vec<String>;
    
    /// Get last activity timestamp
    fn get_last_activity(&self) -> Option<chrono::DateTime<Utc>>;
}

/// SocketCAN interface implementation
#[cfg(feature = "socketcan")]
pub struct SocketCANInterface {
    id: String,
    device: String,
    socket: Arc<Mutex<Option<can::Socket>>>,
    last_activity: Arc<RwLock<Option<chrono::DateTime<Utc>>>>,
}

#[cfg(feature = "socketcan")]
impl SocketCANInterface {
    pub fn new(device: String) -> Self {
        Self {
            id: format!("socketcan:{}", device),
            device,
            socket: Arc::new(Mutex::new(None)),
            last_activity: Arc::new(RwLock::new(None)),
        }
    }
}

#[cfg(feature = "socketcan")]
#[async_trait]
impl HardwareInterface for SocketCANInterface {
    fn get_id(&self) -> String {
        self.id.clone()
    }
    
    fn get_type(&self) -> InterfaceType {
        InterfaceType::SocketCAN
    }
    
    async fn is_connected(&self) -> bool {
        let socket = self.socket.lock().await;
        socket.is_some()
    }
    
    async fn connect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let socket = can::Socket::open(&self.device)
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        
        {
            let mut socket_guard = self.socket.lock().await;
            *socket_guard = Some(socket);
        }
        
        *self.last_activity.write().await = Some(Utc::now());
        info!("Connected to SocketCAN device: {}", self.device);
        
        Ok(())
    }
    
    async fn disconnect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let mut socket = self.socket.lock().await;
        *socket = None;
        info!("Disconnected from SocketCAN device: {}", self.device);
        Ok(())
    }
    
    async fn send_can_frame(&self, frame: &CanFrame) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let socket = self.socket.lock().await;
        let socket = socket.as_ref().ok_or("Not connected")?;
        
        let can_frame = can::Frame::new(
            frame.id,
            &frame.data,
            frame.extended
        ).map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        
        socket.send(&can_frame)
            .map_err(|e| Box::new(e) as Box<dyn std::error::Error + Send + Sync>)?;
        
        *self.last_activity.write().await = Some(Utc::now());
        Ok(())
    }
    
    async fn receive_can_frame(&self, timeout_ms: u64) -> Result<Option<CanFrame>, Box<dyn std::error::Error + Send + Sync>> {
        let socket = self.socket.lock().await;
        let socket = socket.as_ref().ok_or("Not connected")?;
        
        match socket.read_frame() {
            Ok(frame) => {
                *self.last_activity.write().await = Some(Utc::now());
                Ok(Some(CanFrame {
                    id: frame.id(),
                    extended: frame.is_extended(),
                    data: frame.data().to_vec(),
                    timestamp: Utc::now(),
                }))
            },
            Err(e) => {
                if e.kind() == std::io::ErrorKind::WouldBlock {
                    Ok(None) // Timeout
                } else {
                    Err(Box::new(e) as Box<dyn std::error::Error + Send + Sync>)
                }
            }
        }
    }
    
    fn get_capabilities(&self) -> Vec<String> {
        vec![
            "CAN".to_string(),
            "CAN_FD".to_string(),
            "11_BIT".to_string(),
            "29_BIT".to_string(),
        ]
    }
    
    fn get_last_activity(&self) -> Option<chrono::DateTime<Utc>> {
        // This would need async, but for now return None
        None
    }
}

/// J2534 interface implementation
#[cfg(feature = "j2534")]
pub struct J2534Interface {
    id: String,
    device_id: u32,
    channel_id: Arc<Mutex<Option<u32>>>,
    last_activity: Arc<RwLock<Option<chrono::DateTime<Utc>>>>,
}

impl J2534Interface {
    pub fn new(device_id: u32) -> Self {
        Self {
            id: format!("j2534:{}", device_id),
            device_id,
            channel_id: Arc::new(Mutex::new(None)),
            last_activity: Arc::new(RwLock::new(None)),
        }
    }
}

#[async_trait]
impl HardwareInterface for J2534Interface {
    fn get_id(&self) -> String {
        self.id.clone()
    }
    
    fn get_type(&self) -> InterfaceType {
        InterfaceType::J2534
    }
    
    async fn is_connected(&self) -> bool {
        let channel = self.channel_id.lock().await;
        channel.is_some()
    }
    
    async fn connect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // J2534 connection logic would go here
        // For now, simulate connection
        info!("Connected to J2534 device: {}", self.device_id);
        Ok(())
    }
    
    async fn disconnect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        info!("Disconnected from J2534 device: {}", self.device_id);
        Ok(())
    }
    
    async fn send_can_frame(&self, _frame: &CanFrame) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // J2534 send logic
        Ok(())
    }
    
    async fn receive_can_frame(&self, _timeout_ms: u64) -> Result<Option<CanFrame>, Box<dyn std::error::Error + Send + Sync>> {
        // J2534 receive logic
        Ok(None)
    }
    
    fn get_capabilities(&self) -> Vec<String> {
        vec![
            "CAN".to_string(),
            "ISO9141".to_string(),
            "ISO14230".to_string(),
            "ISO15765".to_string(),
            "J1850".to_string(),
        ]
    }
    
    fn get_last_activity(&self) -> Option<chrono::DateTime<Utc>> {
        None
    }
}

/// Interface handle for managing connections
#[derive(Clone)]
pub struct InterfaceHandle {
    interface: Arc<RwLock<dyn HardwareInterface>>,
}

impl InterfaceHandle {
    pub fn new(interface: Box<dyn HardwareInterface>) -> Self {
        Self {
            interface: Arc::new(RwLock::new(interface)),
        }
    }
    
    pub async fn is_connected(&self) -> bool {
        self.interface.read().await.is_connected().await
    }
    
    pub async fn send_frame(&self, frame: &CanFrame) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        self.interface.read().await.send_can_frame(frame).await
    }
    
    pub async fn receive_frame(&self, timeout_ms: u64) -> Result<Option<CanFrame>, Box<dyn std::error::Error + Send + Sync>> {
        self.interface.read().await.receive_can_frame(timeout_ms).await
    }
    
    pub fn get_id(&self) -> String {
        // This is a limitation of the async trait - we'd need to redesign
        "interface".to_string()
    }
    
    pub fn get_last_activity(&self) -> Option<chrono::DateTime<Utc>> {
        self.interface.blocking_read().get_last_activity()
    }
}

/// Mock interface for platforms without hardware support
pub struct MockInterface {
    id: String,
    connected: Arc<Mutex<bool>>,
    last_activity: Arc<RwLock<Option<chrono::DateTime<Utc>>>>,
}

impl MockInterface {
    pub fn new(id: String) -> Self {
        Self {
            id,
            connected: Arc::new(Mutex::new(false)),
            last_activity: Arc::new(RwLock::new(None)),
        }
    }
}

#[async_trait]
impl HardwareInterface for MockInterface {
    fn get_id(&self) -> String {
        self.id.clone()
    }
    
    fn get_type(&self) -> InterfaceType {
        InterfaceType::Mock
    }
    
    async fn is_connected(&self) -> bool {
        *self.connected.lock().await
    }
    
    async fn connect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        *self.connected.lock().await = true;
        *self.last_activity.write().await = Some(Utc::now());
        info!("Mock interface connected: {}", self.id);
        Ok(())
    }
    
    async fn disconnect(&mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        *self.connected.lock().await = false;
        info!("Mock interface disconnected: {}", self.id);
        Ok(())
    }
    
    async fn send_can_frame(&self, _frame: &CanFrame) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        // Mock implementation - just log
        warn!("Mock interface: send_can_frame called but not implemented");
        Ok(())
    }
    
    async fn receive_can_frame(&self, _timeout_ms: u64) -> Result<Option<CanFrame>, Box<dyn std::error::Error + Send + Sync>> {
        // Mock implementation - always return None
        Ok(None)
    }
    
    fn get_capabilities(&self) -> Vec<String> {
        vec![
            "MOCK".to_string(),
            "NO_HARDWARE".to_string(),
        ]
    }
    
    fn get_last_activity(&self) -> Option<chrono::DateTime<Utc>> {
        self.last_activity.blocking_read().clone()
    }
}

/// Scan for available interfaces
pub async fn scan_interfaces() -> Result<Vec<InterfaceInfo>, Box<dyn std::error::Error + Send + Sync>> {
    let mut interfaces = Vec::new();
    
    // Scan for SocketCAN devices (Linux only)
    #[cfg(feature = "socketcan")]
    {
        if let Ok(entries) = std::fs::read_dir("/sys/class/net") {
            for entry in entries.flatten() {
                let name = entry.file_name().to_string_lossy().to_string();
                if name.starts_with("can") {
                    interfaces.push(InterfaceInfo {
                        id: format!("socketcan:{}", name),
                        name: format!("SocketCAN ({})", name),
                        interface_type: InterfaceType::SocketCAN,
                        capabilities: vec![
                            "CAN".to_string(),
                            "CAN_FD".to_string(),
                        ],
                        is_available: true,
                    });
                }
            }
        }
    }
    
    // Scan for J2534 devices (Windows only)
    #[cfg(feature = "j2534")]
    {
        // This would involve scanning for J2534 DLLs or USB devices
        // For now, add a placeholder
        interfaces.push(InterfaceInfo {
            id: "j2534:0".to_string(),
            name: "J2534 Device 0".to_string(),
            interface_type: InterfaceType::J2534,
            capabilities: vec![
                "J2534".to_string(),
                "ISO15765".to_string(),
                "ISO9141".to_string(),
            ],
            is_available: false,
        });
    }
    
    // Always add mock interface as fallback (DEV mode only)
    interfaces.push(InterfaceInfo {
        id: "mock:0".to_string(),
        name: "Mock Interface (No Hardware)".to_string(),
        interface_type: InterfaceType::Mock,
        capabilities: vec![
            "MOCK".to_string(),
            "NO_HARDWARE".to_string(),
        ],
        is_available: true, // Will be checked at connection time
    });
    
    Ok(interfaces)
}

/// Connect to an interface
pub async fn connect_interface(interface_id: &str) -> Result<InterfaceHandle, Box<dyn std::error::Error + Send + Sync>> {
    #[cfg(feature = "socketcan")]
    {
        if interface_id.starts_with("socketcan:") {
            let device = interface_id.strip_prefix("socketcan:").unwrap();
            let mut iface = SocketCANInterface::new(device.to_string());
            iface.connect().await?;
            return Ok(InterfaceHandle::new(Box::new(iface)));
        }
    }
    
    #[cfg(feature = "j2534")]
    {
        if interface_id.starts_with("j2534:") {
            let device_id = interface_id.strip_prefix("j2534:").unwrap().parse::<u32>()?;
            let mut iface = J2534Interface::new(device_id);
            iface.connect().await?;
            return Ok(InterfaceHandle::new(Box::new(iface)));
        }
    }
    
    if interface_id.starts_with("mock:") {
        // Check operator mode - mock interface only allowed in DEV mode
        let operator_mode = std::env::var("OPERATOR_MODE").unwrap_or_else(|_| "dev".to_string());
        
        if operator_mode != "dev" {
            return Err("Mock interface only available in DEV mode".into());
        }
        
        let mut iface = MockInterface::new(interface_id.to_string());
        iface.connect().await?;
        return Ok(InterfaceHandle::new(Box::new(iface)));
    }
    
    Err(format!("Unknown interface type: {}", interface_id).into())
}

/// Disconnect from an interface
pub async fn disconnect_interface(handle: InterfaceHandle) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // The interface handle would need to support disconnect
    // This is a limitation of the current design
    warn!("Disconnect not fully implemented");
    Ok(())
}

// Mock can crate for compilation
// In a real implementation, you'd use the actual socketcan crate
pub mod can {
    pub struct Socket;
    pub struct Frame {
        id: u32,
        data: Vec<u8>,
        extended: bool,
    }
    
    impl Socket {
        pub fn open(_device: &str) -> Result<Self, std::io::Error> {
            Ok(Socket)
        }
        
        pub fn send(&self, _frame: &Frame) -> Result<(), std::io::Error> {
            Ok(())
        }
        
        pub fn read_frame(&self) -> Result<Frame, std::io::Error> {
            Err(std::io::Error::new(std::io::ErrorKind::WouldBlock, "No data"))
        }
    }
    
    impl Frame {
        pub fn new(id: u32, data: &[u8], extended: bool) -> Result<Self, std::io::Error> {
            Ok(Frame {
                id,
                data: data.to_vec(),
                extended,
            })
        }
        
        pub fn id(&self) -> u32 { self.id }
        pub fn data(&self) -> &[u8] { &self.data }
        pub fn is_extended(&self) -> bool { self.extended }
    }
}
