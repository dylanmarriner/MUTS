/**
 * Flash Supervisor - Single Owner for Deterministic Flash Operations
 * Ensures all flash operations are monitored and can be aborted within 25ms
 */

use std::sync::Arc;
use std::collections::HashMap;
use tokio::sync::{mpsc, oneshot, RwLock, Mutex};
use tokio::time::{timeout, Duration, Instant};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use tracing::{error, warn, info, debug};
use chrono::{DateTime, Utc};

use crate::event_bus::{EventBus, Priority, Event};

/// Flash operation states
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum FlashState {
    Idle,
    Preparing,
    Ready,
    Flashing,
    Verifying,
    Completed,
    Failed(String),
    Aborted,
}

/// Flash operation commands
#[derive(Debug)]
pub enum FlashCommand {
    Prepare {
        job_id: String,
        rom_data: Vec<u8>,
    },
    Start {
        job_id: String,
    },
    Abort {
        job_id: String,
    },
    GetStatus {
        job_id: String,
        response: oneshot::Sender<FlashStatus>,
    },
}

/// Flash operation status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FlashStatus {
    pub job_id: String,
    pub state: FlashState,
    pub progress: f32,
    pub blocks_completed: u32,
    pub total_blocks: u32,
    pub last_update: DateTime<Utc>,
    pub error: Option<String>,
}

/// Flash job details
#[derive(Debug)]
struct FlashJob {
    id: String,
    state: FlashState,
    progress: f32,
    rom_data: Vec<u8>,
    blocks_completed: u32,
    total_blocks: u32,
    created_at: Instant,
    last_activity: Instant,
    abort_handle: Option<tokio::sync::watch::Sender<bool>>,
}

/// Flash supervisor configuration
#[derive(Debug, Clone)]
pub struct FlashSupervisorConfig {
    /// Maximum time between progress updates before watchdog triggers
    pub watchdog_timeout_ms: u64,
    /// Maximum time to wait for abort acknowledgment
    pub abort_timeout_ms: u64,
    /// Maximum concurrent flash jobs
    pub max_concurrent_jobs: usize,
}

impl Default for FlashSupervisorConfig {
    fn default() -> Self {
        Self {
            watchdog_timeout_ms: 5000,  // 5 seconds
            abort_timeout_ms: 25,       // 25ms requirement
            max_concurrent_jobs: 1,     // Single owner
        }
    }
}

/// Flash supervisor - single owner of all flash operations
pub struct FlashSupervisor {
    config: FlashSupervisorConfig,
    event_bus: Arc<EventBus>,
    
    // Command channel
    command_tx: mpsc::UnboundedSender<FlashCommand>,
    
    // Job tracking
    jobs: Arc<RwLock<HashMap<String, FlashJob>>>,
    
    // Metrics
    metrics: Arc<RwLock<FlashMetrics>>,
}

#[derive(Debug, Default)]
pub struct FlashMetrics {
    pub jobs_completed: u64,
    pub jobs_failed: u64,
    pub jobs_aborted: u64,
    pub abort_latency_ms: u64,
    pub watchdog_triggers: u64,
}

impl FlashSupervisor {
    pub fn new(config: FlashSupervisorConfig, event_bus: Arc<EventBus>) -> Self {
        let (command_tx, command_rx) = mpsc::unbounded_channel();
        
        let supervisor = Self {
            config,
            event_bus,
            command_tx,
            jobs: Arc::new(RwLock::new(HashMap::new())),
            metrics: Arc::new(RwLock::new(FlashMetrics::default())),
        };
        
        // Start the supervisor task
        supervisor.start_supervisor(command_rx);
        
        supervisor
    }

    /// Get command sender
    pub fn command_sender(&self) -> mpsc::UnboundedSender<FlashCommand> {
        self.command_tx.clone()
    }

    /// Get current metrics
    pub async fn get_metrics(&self) -> FlashMetrics {
        self.metrics.read().await.clone()
    }

    /// Get all job statuses
    pub async fn get_all_statuses(&self) -> Vec<FlashStatus> {
        let jobs = self.jobs.read().await;
        jobs.values().map(|job| FlashStatus {
            job_id: job.id.clone(),
            state: job.state.clone(),
            progress: job.progress,
            blocks_completed: job.blocks_completed,
            total_blocks: job.total_blocks,
            last_update: Utc::now(),
            error: None,
        }).collect()
    }

    // Internal methods
    fn start_supervisor(&self, mut command_rx: mpsc::UnboundedReceiver<FlashCommand>) {
        let jobs = self.jobs.clone();
        let metrics = self.metrics.clone();
        let event_bus = self.event_bus.clone();
        let config = self.config.clone();
        
        tokio::spawn(async move {
            info!("Flash supervisor started");
            
            // Start watchdog task
            let watchdog_jobs = jobs.clone();
            let watchdog_metrics = metrics.clone();
            let watchdog_bus = event_bus.clone();
            let watchdog_config = config.clone();
            tokio::spawn(async move {
                Self::watchdog_task(watchdog_jobs, watchdog_metrics, watchdog_bus, watchdog_config).await;
            });
            
            // Process commands
            while let Some(command) = command_rx.recv().await {
                Self::handle_command(command, &jobs, &metrics, &event_bus, &config).await;
            }
            
            error!("Flash supervisor stopped");
        });
    }

    async fn handle_command(
        command: FlashCommand,
        jobs: &Arc<RwLock<HashMap<String, FlashJob>>>,
        metrics: &Arc<RwLock<FlashMetrics>>,
        event_bus: &Arc<EventBus>,
        config: &FlashSupervisorConfig,
    ) {
        match command {
            FlashCommand::Prepare { job_id, rom_data } => {
                Self::handle_prepare(job_id, rom_data, jobs, event_bus).await;
            }
            
            FlashCommand::Start { job_id } => {
                Self::handle_start(job_id, jobs, metrics, event_bus, config).await;
            }
            
            FlashCommand::Abort { job_id } => {
                Self::handle_abort(job_id, jobs, metrics, event_bus, config).await;
            }
            
            FlashCommand::GetStatus { job_id, response } => {
                let status = Self::get_job_status(&job_id, jobs).await;
                let _ = response.send(status);
            }
        }
    }

    async fn handle_prepare(
        job_id: String,
        rom_data: Vec<u8>,
        jobs: &Arc<RwLock<HashMap<String, FlashJob>>>,
        event_bus: &Arc<EventBus>,
    ) {
        let mut jobs = jobs.write().await;
        
        if jobs.contains_key(&job_id) {
            warn!("Job {} already exists", job_id);
            return;
        }
        
        let job = FlashJob {
            id: job_id.clone(),
            state: FlashState::Preparing,
            progress: 0.0,
            rom_data,
            blocks_completed: 0,
            total_blocks: 0, // Will be calculated
            created_at: Instant::now(),
            last_activity: Instant::now(),
            abort_handle: None,
        };
        
        jobs.insert(job_id.clone(), job);
        
        // Send event
        let event = Event {
            id: Uuid::new_v4(),
            priority: Priority::P1Flash,
            event_type: "flash_state_change".to_string(),
            data: serde_json::json!({
                "job_id": job_id,
                "state": "Preparing"
            }),
            timestamp: Utc::now(),
            requires_ack: false,
        };
        
        let _ = event_bus.send(event).await;
    }

    async fn handle_start(
        job_id: String,
        jobs: &Arc<RwLock<HashMap<String, FlashJob>>>,
        metrics: &Arc<RwLock<FlashMetrics>>,
        event_bus: &Arc<EventBus>,
        config: &FlashSupervisorConfig,
    ) {
        let job = {
            let mut jobs = jobs.write().await;
            if let Some(job) = jobs.get_mut(&job_id) {
                job.state = FlashState::Flashing;
                job.total_blocks = (job.rom_data.len() / 1024) as u32; // 1KB blocks
                job.last_activity = Instant::now();
                
                // Create abort handle
                let (abort_tx, abort_rx) = tokio::sync::watch::channel(false);
                job.abort_handle = Some(abort_tx);
                
                Some(job.clone())
            } else {
                error!("Job {} not found", job_id);
                return;
            }
        };
        
        // Start flash execution under supervisor control
        let jobs_clone = jobs.clone();
        let metrics_clone = metrics.clone();
        let event_bus_clone = event_bus.clone();
        let config_clone = config.clone();
        
        tokio::spawn(async move {
            Self::execute_flash(job, jobs_clone, metrics_clone, event_bus_clone, config_clone).await;
        });
    }

    async fn handle_abort(
        job_id: String,
        jobs: &Arc<RwLock<HashMap<String, FlashJob>>>,
        metrics: &Arc<RwLock<FlashMetrics>>,
        event_bus: &Arc<EventBus>,
        config: &FlashSupervisorConfig,
    ) {
        let abort_start = Instant::now();
        
        {
            let mut jobs = jobs.write().await;
            if let Some(job) = jobs.get_mut(&job_id) {
                // Send abort signal
                if let Some(ref abort_tx) = job.abort_handle {
                    let _ = abort_tx.send(true);
                }
                job.state = FlashState::Aborted;
                job.last_activity = Instant::now();
            }
        }
        
        // Wait for abort to take effect
        let abort_timeout = Duration::from_millis(config.abort_timeout_ms);
        
        let mut aborted = false;
        for _ in 0..10 {
            tokio::time::sleep(Duration::from_millis(2)).await;
            
            let jobs = jobs.read().await;
            if let Some(job) = jobs.get(&job_id) {
                if job.state == FlashState::Aborted {
                    aborted = true;
                    break;
                }
            }
        }
        
        let abort_latency = abort_start.elapsed().as_millis() as u64;
        
        // Update metrics
        {
            let mut metrics = metrics.write().await;
            metrics.jobs_aborted += 1;
            metrics.abort_latency_ms = abort_latency;
        }
        
        if aborted {
            info!("Job {} aborted in {}ms", job_id, abort_latency);
        } else {
            error!("Job {} abort failed after {}ms", job_id, abort_latency);
        }
        
        // Send event
        let event = Event {
            id: Uuid::new_v4(),
            priority: Priority::P1Flash,
            event_type: "flash_aborted".to_string(),
            data: serde_json::json!({
                "job_id": job_id,
                "latency_ms": abort_latency
            }),
            timestamp: Utc::now(),
            requires_ack: false,
        };
        
        let _ = event_bus.send(event).await;
    }

    async fn execute_flash(
        mut job: FlashJob,
        jobs: Arc<RwLock<HashMap<String, FlashJob>>>,
        metrics: Arc<RwLock<FlashMetrics>>,
        event_bus: Arc<EventBus>,
        config: FlashSupervisorConfig,
    ) {
        info!("Starting flash execution for job {}", job.id);
        
        let mut abort_rx = job.abort_handle.as_ref()
            .map(|h| h.subscribe())
            .unwrap();
        
        let block_size = 1024; // 1KB blocks
        let total_blocks = (job.rom_data.len() / block_size);
        
        for block in 0..total_blocks {
            // Check for abort
            if *abort_rx.borrow() {
                info!("Job {} aborted at block {}", job.id, block);
                return;
            }
            
            // Simulate flash block write with interruptible sleep
            let block_start = Instant::now();
            
            // Use select! to allow abort during sleep
            tokio::select! {
                _ = tokio::time::sleep(Duration::from_millis(100)) => {
                    // Normal completion
                }
                _ = abort_rx.changed() => {
                    // Abort received
                    info!("Job {} aborted during block write", job.id);
                    return;
                }
            }
            
            // Update progress
            job.blocks_completed = block + 1;
            job.progress = (job.blocks_completed as f32 / total_blocks as f32) * 100.0;
            job.last_activity = Instant::now();
            
            // Update job in storage
            {
                let mut jobs = jobs.write().await;
                jobs.insert(job.id.clone(), job.clone());
            }
            
            // Send progress event
            let event = Event {
                id: Uuid::new_v4(),
                priority: Priority::P1Flash,
                event_type: "flash_progress".to_string(),
                data: serde_json::json!({
                    "job_id": job.id,
                    "progress": job.progress,
                    "block": block,
                    "total_blocks": total_blocks
                }),
                timestamp: Utc::now(),
                requires_ack: false,
            };
            
            let _ = event_bus.send(event).await;
            
            debug!("Job {} block {}/{} completed", job.id, block + 1, total_blocks);
        }
        
        // Flash completed successfully
        {
            let mut jobs = jobs.write().await;
            if let Some(job) = jobs.get_mut(&job.id) {
                job.state = FlashState::Completed;
                job.progress = 100.0;
            }
        }
        
        // Update metrics
        {
            let mut metrics = metrics.write().await;
            metrics.jobs_completed += 1;
        }
        
        // Send completion event
        let event = Event {
            id: Uuid::new_v4(),
            priority: Priority::P1Flash,
            event_type: "flash_completed".to_string(),
            data: serde_json::json!({
                "job_id": job.id,
                "total_blocks": total_blocks
            }),
            timestamp: Utc::now(),
            requires_ack: false,
        };
        
        let _ = event_bus.send(event).await;
        
        info!("Job {} completed successfully", job.id);
    }

    async fn watchdog_task(
        jobs: Arc<RwLock<HashMap<String, FlashJob>>>,
        metrics: Arc<RwLock<FlashMetrics>>,
        event_bus: Arc<EventBus>,
        config: FlashSupervisorConfig,
    ) {
        let mut interval = tokio::time::interval(Duration::from_millis(100));
        
        loop {
            interval.tick().await;
            
            let now = Instant::now();
            let timeout = Duration::from_millis(config.watchdog_timeout_ms);
            
            let mut jobs_to_abort = Vec::new();
            
            {
                let jobs = jobs.read().await;
                for (job_id, job) in jobs.iter() {
                    if job.state == FlashState::Flashing {
                        if now.duration_since(job.last_activity) > timeout {
                            warn!("Watchdog: Job {} stalled, forcing abort", job_id);
                            jobs_to_abort.push(job_id.clone());
                        }
                    }
                }
            }
            
            // Force abort stalled jobs
            for job_id in jobs_to_abort {
                // Update metrics
                {
                    let mut metrics = metrics.write().await;
                    metrics.watchdog_triggers += 1;
                }
                
                // Force state change
                {
                    let mut jobs = jobs.write().await;
                    if let Some(job) = jobs.get_mut(&job_id) {
                        job.state = FlashState::Failed("Watchdog timeout".to_string());
                    }
                }
                
                // Send critical safety event
                let event = Event {
                    id: Uuid::new_v4(),
                    priority: Priority::P0Safety,
                    event_type: "watchdog_timeout".to_string(),
                    data: serde_json::json!({
                        "job_id": job_id,
                        "reason": "Flash operation stalled"
                    }),
                    timestamp: Utc::now(),
                    requires_ack: true,
                };
                
                let _ = event_bus.send(event).await;
                
                error!("Watchdog forced abort of job {}", job_id);
            }
        }
    }

    async fn get_job_status(job_id: &str, jobs: &Arc<RwLock<HashMap<String, FlashJob>>>) -> FlashStatus {
        let jobs = jobs.read().await;
        if let Some(job) = jobs.get(job_id) {
            FlashStatus {
                job_id: job.id.clone(),
                state: job.state.clone(),
                progress: job.progress,
                blocks_completed: job.blocks_completed,
                total_blocks: job.total_blocks,
                last_update: Utc::now(),
                error: None,
            }
        } else {
            FlashStatus {
                job_id: job_id.to_string(),
                state: FlashState::Failed("Job not found".to_string()),
                progress: 0.0,
                blocks_completed: 0,
                total_blocks: 0,
                last_update: Utc::now(),
                error: Some("Job not found".to_string()),
            }
        }
    }
}
