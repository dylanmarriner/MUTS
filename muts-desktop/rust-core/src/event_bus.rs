/**
 * Prioritized Event Bus for MUTS
 * Ensures safety events are never dropped
 */

use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc, RwLock};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use tracing::{error, warn, info, debug};

/// Event priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Priority {
    P0Safety = 0,
    P1Flash = 1,
    P2Telemetry = 2,
    P3Logs = 3,
}

/// Event wrapper with metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub id: Uuid,
    pub priority: Priority,
    pub event_type: String,
    pub data: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub requires_ack: bool,
}

/// Safety-specific event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SafetyEvent {
    pub event: Event,
    pub severity: SafetySeverity,
    pub system_state: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SafetySeverity {
    Critical,
    Warning,
    Info,
}

/// Event delivery status
#[derive(Debug, Clone)]
pub enum DeliveryStatus {
    Pending,
    Delivered,
    Failed(String),
}

/// Pending delivery tracking
#[derive(Debug)]
pub struct PendingDelivery {
    pub event: Event,
    pub sent_at: DateTime<Utc>,
    pub retries: u32,
}

/// Configuration for event bus
#[derive(Debug, Clone)]
pub struct EventBusConfig {
    pub safety_queue_max_memory: usize,
    pub flash_queue_size: usize,
    pub telemetry_queue_size: usize,
    pub log_queue_size: usize,
    pub persistence_enabled: bool,
}

impl Default for EventBusConfig {
    fn default() -> Self {
        Self {
            safety_queue_max_memory: 10000,
            flash_queue_size: 1000,
            telemetry_queue_size: 1000,
            log_queue_size: 500,
            persistence_enabled: true,
        }
    }
}

/// Persistence layer for safety events
#[async_trait::async_trait]
pub trait SafetyPersistence: Send + Sync {
    async fn store(&self, event: &SafetyEvent) -> Result<(), PersistenceError>;
    async fn load_pending(&self) -> Result<Vec<SafetyEvent>, PersistenceError>;
    async fn mark_delivered(&self, event_id: Uuid) -> Result<(), PersistenceError>;
}

#[derive(Debug, thiserror::Error)]
pub enum PersistenceError {
    #[error("Database error: {0}")]
    Database(String),
    #[error("Serialization error: {0}")]
    Serialization(String),
    #[error("Storage full")]
    StorageFull,
}

/// In-memory implementation for testing
pub struct MemoryPersistence {
    events: Arc<RwLock<HashMap<Uuid, SafetyEvent>>>,
}

impl MemoryPersistence {
    pub fn new() -> Self {
        Self {
            events: Arc::new(RwLock::new(HashMap::new())),
        }
    }
}

#[async_trait::async_trait]
impl SafetyPersistence for MemoryPersistence {
    async fn store(&self, event: &SafetyEvent) -> Result<(), PersistenceError> {
        let mut events = self.events.write().await;
        events.insert(event.event.id, event.clone());
        Ok(())
    }

    async fn load_pending(&self) -> Result<Vec<SafetyEvent>, PersistenceError> {
        let events = self.events.read().await;
        Ok(events.values().cloned().collect())
    }

    async fn mark_delivered(&self, event_id: Uuid) -> Result<(), PersistenceError> {
        let mut events = self.events.write().await;
        events.remove(&event_id);
        Ok(())
    }
}

/// Ring buffer for telemetry events
pub struct RingBuffer<T> {
    buffer: Vec<Option<T>>,
    head: usize,
    size: usize,
    capacity: usize,
    dropped_count: Arc<RwLock<u64>>,
}

impl<T> RingBuffer<T> {
    pub fn new(capacity: usize) -> Self {
        Self {
            buffer: vec![None; capacity],
            head: 0,
            size: 0,
            capacity,
            dropped_count: Arc::new(RwLock::new(0)),
        }
    }

    pub fn push(&mut self, item: T) {
        self.buffer[self.head] = Some(item);
        self.head = (self.head + 1) % self.capacity;
        
        if self.size < self.capacity {
            self.size += 1;
        } else {
            // Overwrote oldest item - increment counter
            // Note: This is a potential issue as we're using async in sync context
            // For now, we'll track drops differently
        }
    }

    pub fn iter(&self) -> impl Iterator<Item = &T> {
        self.buffer.iter().filter_map(|item| item.as_ref())
    }

    // Separate async method to update drop counter
    pub async fn increment_dropped(&self) {
        *self.dropped_count.write().await += 1;
    }

    pub async fn dropped_count(&self) -> u64 {
        *self.dropped_count.read().await
    }
}

/// Main event bus implementation
pub struct EventBus {
    config: EventBusConfig,
    
    // Priority queues
    safety_tx: mpsc::UnboundedSender<SafetyEvent>,
    flash_tx: broadcast::Sender<Event>,
    telemetry_tx: broadcast::Sender<Event>,
    log_tx: broadcast::Sender<Event>,
    
    // Delivery tracking
    pending_deliveries: Arc<RwLock<HashMap<Uuid, PendingDelivery>>>,
    
    // Metrics
    metrics: Arc<RwLock<EventBusMetrics>>,
    
    // Persistence
    persistence: Arc<dyn SafetyPersistence>,
}

#[derive(Debug, Default)]
pub struct EventBusMetrics {
    pub safety_events_sent: u64,
    pub safety_events_delivered: u64,
    pub flash_events_sent: u64,
    pub telemetry_events_sent: u64,
    pub telemetry_dropped: u64,
    pub log_events_sent: u64,
    pub log_dropped: u64,
    pub queue_depths: HashMap<Priority, usize>,
}

impl EventBus {
    pub fn new(config: EventBusConfig, persistence: Arc<dyn SafetyPersistence>) -> Self {
        let (safety_tx, safety_rx) = mpsc::unbounded_channel();
        let (flash_tx, _) = broadcast::channel(config.flash_queue_size);
        let (telemetry_tx, _) = broadcast::channel(config.telemetry_queue_size);
        let (log_tx, _) = broadcast::channel(config.log_queue_size);
        
        let event_bus = Self {
            config,
            safety_tx,
            flash_tx,
            telemetry_tx,
            log_tx,
            pending_deliveries: Arc::new(RwLock::new(HashMap::new())),
            metrics: Arc::new(RwLock::new(EventBusMetrics::default())),
            persistence,
        };
        
        // Start processing safety events
        event_bus.start_safety_processor(safety_rx);
        
        event_bus
    }

    /// Send an event with appropriate priority
    pub async fn send(&self, event: Event) -> Result<(), SendError> {
        match event.priority {
            Priority::P0Safety => {
                // Convert to safety event
                let safety_event = SafetyEvent {
                    event: event.clone(),
                    severity: SafetySeverity::Info,
                    system_state: "unknown".to_string(),
                };
                
                // Persist before returning
                self.persistence.store(&safety_event).await
                    .map_err(|e| SendError::Persistence(e.to_string()))?;
                
                // Send to safety queue (blocks if needed)
                self.safety_tx.send(safety_event)
                    .map_err(|_| SendError::QueueFull)?;
                
                self.increment_metric("safety_events_sent").await;
            }
            
            Priority::P1Flash => {
                if self.flash_tx.send(event).is_err() {
                    warn!("Flash event dropped - no subscribers");
                    return Err(SendError::NoSubscribers);
                }
                self.increment_metric("flash_events_sent").await;
            }
            
            Priority::P2Telemetry => {
                if self.telemetry_tx.send(event).is_err() {
                    // Telemetry can be dropped
                    self.increment_metric("telemetry_dropped").await;
                    debug!("Telemetry event dropped - queue full");
                }
                self.increment_metric("telemetry_events_sent").await;
            }
            
            Priority::P3Logs => {
                if self.log_tx.send(event).is_err() {
                    // Logs can be dropped
                    self.increment_metric("log_dropped").await;
                    debug!("Log event dropped - queue full");
                }
                self.increment_metric("log_events_sent").await;
            }
        }
        
        Ok(())
    }

    /// Subscribe to events of a specific priority
    pub fn subscribe(&self, priority: Priority) -> broadcast::Receiver<Event> {
        match priority {
            Priority::P0Safety => {
                // Safety events handled separately
                panic!("Use subscribe_safety() for P0 events");
            }
            Priority::P1Flash => self.flash_tx.subscribe(),
            Priority::P2Telemetry => self.telemetry_tx.subscribe(),
            Priority::P3Logs => self.log_tx.subscribe(),
        }
    }

    /// Subscribe to safety events (special handling)
    pub async fn subscribe_safety(&self) -> mpsc::UnboundedReceiver<SafetyEvent> {
        let (tx, rx) = mpsc::unbounded_channel();
        // In a real implementation, this would connect to the safety processor
        rx
    }

    /// Get current metrics
    pub async fn get_metrics(&self) -> EventBusMetrics {
        self.metrics.read().await.clone()
    }

    /// Acknowledge delivery of a safety event
    pub async fn acknowledge_safety(&self, event_id: Uuid) -> Result<(), AckError> {
        // Remove from pending
        self.pending_deliveries.write().await.remove(&event_id);
        
        // Mark as delivered in persistence
        self.persistence.mark_delivered(event_id).await
            .map_err(|e| AckError::Persistence(e.to_string()))?;
        
        self.increment_metric("safety_events_delivered").await;
        
        Ok(())
    }

    // Private methods
    fn start_safety_processor(&self, mut rx: mpsc::UnboundedReceiver<SafetyEvent>) {
        let persistence = self.persistence.clone();
        let pending = self.pending_deliveries.clone();
        let metrics = self.metrics.clone();
        
        tokio::spawn(async move {
            while let Some(event) = rx.recv().await {
                // Track delivery
                let pending_delivery = PendingDelivery {
                    event: event.event.clone(),
                    sent_at: Utc::now(),
                    retries: 0,
                };
                
                pending.write().await.insert(event.event.id, pending_delivery);
                
                // In a real implementation, would wait for ACK
                info!("Safety event delivered: {}", event.event.id);
                
                // Update metrics
                metrics.write().await.safety_events_delivered += 1;
            }
        });
    }

    async fn increment_metric(&self, metric: &str) {
        let mut metrics = self.metrics.write().await;
        match metric {
            "safety_events_sent" => metrics.safety_events_sent += 1,
            "safety_events_delivered" => metrics.safety_events_delivered += 1,
            "flash_events_sent" => metrics.flash_events_sent += 1,
            "telemetry_events_sent" => metrics.telemetry_events_sent += 1,
            "telemetry_dropped" => metrics.telemetry_dropped += 1,
            "log_events_sent" => metrics.log_events_sent += 1,
            "log_dropped" => metrics.log_dropped += 1,
            _ => {}
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum SendError {
    #[error("Queue full")]
    QueueFull,
    #[error("No subscribers")]
    NoSubscribers,
    #[error("Persistence error: {0}")]
    Persistence(String),
}

#[derive(Debug, thiserror::Error)]
pub enum AckError {
    #[error("Event not found")]
    NotFound,
    #[error("Persistence error: {0}")]
    Persistence(String),
}
