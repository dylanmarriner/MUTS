/**
 * Runtime Metrics and Violation Detection
 * Tracks timing violations and enforces fail-fast policies
 */

import { EventEmitter } from 'events';

export interface TimingMetrics {
  // Latency metrics (in milliseconds)
  telemetryLatency: {
    p50: number;
    p95: number;
    p99: number;
  };
  ipcLatency: {
    p50: number;
    p95: number;
    p99: number;
  };
  abortLatency: {
    p50: number;
    p95: number;
    p99: number;
  };
  
  // Queue metrics
  queueDepths: {
    safety: number;
    flash: number;
    telemetry: number;
    logs: number;
  };
  
  // Drop counts
  droppedEvents: {
    safety: number;  // MUST ALWAYS BE 0
    telemetry: number;
    logs: number;
  };
  
  // Flash metrics
  flashMetrics: {
    jobsCompleted: number;
    jobsFailed: number;
    jobsAborted: number;
    watchdogTriggers: number;
  };
}

export interface ViolationPolicy {
  telemetryLatencyThreshold: number;  // ms
  ipcLatencyThreshold: number;        // ms
  abortLatencyThreshold: number;      // ms
  safetyDropThreshold: number;        // MUST BE 0
  queueDepthThreshold: {
    safety: number;
    flash: number;
    telemetry: number;
    logs: number;
  };
}

export class MetricsCollector extends EventEmitter {
  private metrics: TimingMetrics;
  private policy: ViolationPolicy;
  private samples: Map<string, number[]>;
  private violationCounters: Map<string, number>;
  private lastViolationAlert: Map<string, number>;
  
  constructor() {
    super();
    
    this.metrics = this.initializeMetrics();
    this.policy = this.initializePolicy();
    this.samples = new Map();
    this.violationCounters = new Map();
    this.lastViolationAlert = new Map();
    
    // Start periodic evaluation
    setInterval(() => this.evaluateViolations(), 1000);
  }
  
  private initializeMetrics(): TimingMetrics {
    return {
      telemetryLatency: { p50: 0, p95: 0, p99: 0 },
      ipcLatency: { p50: 0, p95: 0, p99: 0 },
      abortLatency: { p50: 0, p95: 0, p99: 0 },
      queueDepths: {
        safety: 0,
        flash: 0,
        telemetry: 0,
        logs: 0,
      },
      droppedEvents: {
        safety: 0,  // CRITICAL: Must remain 0
        telemetry: 0,
        logs: 0,
      },
      flashMetrics: {
        jobsCompleted: 0,
        jobsFailed: 0,
        jobsAborted: 0,
        watchdogTriggers: 0,
      },
    };
  }
  
  private initializePolicy(): ViolationPolicy {
    return {
      telemetryLatencyThreshold: 50,   // < 50ms required
      ipcLatencyThreshold: 10,         // < 10ms required
      abortLatencyThreshold: 25,       // < 25ms required
      safetyDropThreshold: 0,          // MUST BE 0
      queueDepthThreshold: {
        safety: 100,    // Safety queue should not grow
        flash: 1000,    // Flash queue bounded
        telemetry: 1000, // Telemetry can grow
        logs: 500,      // Logs can grow
      },
    };
  }
  
  // Record timing samples
  recordTelemetryLatency(latencyMs: number): void {
    this.addSample('telemetryLatency', latencyMs);
    this.updatePercentiles('telemetryLatency');
  }
  
  recordIpcLatency(latencyMs: number): void {
    this.addSample('ipcLatency', latencyMs);
    this.updatePercentiles('ipcLatency');
  }
  
  recordAbortLatency(latencyMs: number): void {
    this.addSample('abortLatency', latencyMs);
    this.updatePercentiles('abortLatency');
  }
  
  // Update queue depths
  updateQueueDepth(priority: 'safety' | 'flash' | 'telemetry' | 'logs', depth: number): void {
    this.metrics.queueDepths[priority] = depth;
  }
  
  // Record dropped events
  recordDroppedEvent(priority: 'safety' | 'telemetry' | 'logs', count: number = 1): void {
    this.metrics.droppedEvents[priority] += count;
    
    // CRITICAL: Safety events should never be dropped
    if (priority === 'safety' && count > 0) {
      this.triggerCriticalViolation('SAFETY_EVENT_DROPPED', {
        dropped: count,
        timestamp: Date.now(),
      });
    }
  }
  
  // Update flash metrics
  updateFlashMetrics(metrics: Partial<TimingMetrics['flashMetrics']>): void {
    Object.assign(this.metrics.flashMetrics, metrics);
  }
  
  // Get current metrics
  getMetrics(): TimingMetrics {
    return { ...this.metrics };
  }
  
  // Get violation status
  getViolations(): { [key: string]: boolean | number } {
    return {
      telemetryLatencyOk: this.metrics.telemetryLatency.p95 < this.policy.telemetryLatencyThreshold,
      ipcLatencyOk: this.metrics.ipcLatency.p95 < this.policy.ipcLatencyThreshold,
      abortLatencyOk: this.metrics.abortLatency.p95 < this.policy.abortLatencyThreshold,
      safetyDroppedOk: this.metrics.droppedEvents.safety === this.policy.safetyDropThreshold,
      safetyQueueOk: this.metrics.queueDepths.safety < this.policy.queueDepthThreshold.safety,
      flashQueueOk: this.metrics.queueDepths.flash < this.policy.queueDepthThreshold.flash,
      telemetryQueueOk: this.metrics.queueDepths.telemetry < this.policy.queueDepthThreshold.telemetry,
      logQueueOk: this.metrics.queueDepths.logs < this.policy.queueDepthThreshold.logs,
    };
  }
  
  // Private helper methods
  private addSample(metric: string, value: number): void {
    if (!this.samples.has(metric)) {
      this.samples.set(metric, []);
    }
    
    const samples = this.samples.get(metric)!;
    samples.push(value);
    
    // Keep only last 1000 samples
    if (samples.length > 1000) {
      samples.shift();
    }
  }
  
  private updatePercentiles(metric: string): void {
    const samples = this.samples.get(metric);
    if (!samples || samples.length === 0) return;
    
    const sorted = [...samples].sort((a, b) => a - b);
    const len = sorted.length;
    
    const p50 = sorted[Math.floor(len * 0.5)];
    const p95 = sorted[Math.floor(len * 0.95)];
    const p99 = sorted[Math.floor(len * 0.99)];
    
    if (metric === 'telemetryLatency') {
      this.metrics.telemetryLatency = { p50, p95, p99 };
    } else if (metric === 'ipcLatency') {
      this.metrics.ipcLatency = { p50, p95, p99 };
    } else if (metric === 'abortLatency') {
      this.metrics.abortLatency = { p50, p95, p99 };
    }
  }
  
  private evaluateViolations(): void {
    const now = Date.now();
    const alertCooldown = 5000; // 5 seconds between alerts
    
    // Check telemetry latency
    if (this.metrics.telemetryLatency.p95 > this.policy.telemetryLatencyThreshold) {
      this.checkAndAlert('TELEMETRY_LATENCY', now, alertCooldown, {
        threshold: this.policy.telemetryLatencyThreshold,
        actual: this.metrics.telemetryLatency.p95,
      });
    }
    
    // Check IPC latency
    if (this.metrics.ipcLatency.p95 > this.policy.ipcLatencyThreshold) {
      this.checkAndAlert('IPC_LATENCY', now, alertCooldown, {
        threshold: this.policy.ipcLatencyThreshold,
        actual: this.metrics.ipcLatency.p95,
      });
    }
    
    // Check abort latency
    if (this.metrics.abortLatency.p95 > this.policy.abortLatencyThreshold) {
      this.checkAndAlert('ABORT_LATENCY', now, alertCooldown, {
        threshold: this.policy.abortLatencyThreshold,
        actual: this.metrics.abortLatency.p95,
      });
    }
    
    // Check queue depths
    if (this.metrics.queueDepths.safety >= this.policy.queueDepthThreshold.safety) {
      this.checkAndAlert('SAFETY_QUEUE_FULL', now, alertCooldown, {
        depth: this.metrics.queueDepths.safety,
        threshold: this.policy.queueDepthThreshold.safety,
      });
    }
  }
  
  private checkAndAlert(
    violationType: string,
    now: number,
    cooldown: number,
    details: any
  ): void {
    const lastAlert = this.lastViolationAlert.get(violationType) || 0;
    
    if (now - lastAlert > cooldown) {
      this.lastViolationAlert.set(violationType, now);
      this.incrementViolation(violationType);
      
      this.emit('violation', {
        type: violationType,
        details,
        timestamp: now,
        count: this.violationCounters.get(violationType) || 0,
      });
    }
  }
  
  private triggerCriticalViolation(violationType: string, details: any): void {
    this.incrementViolation(violationType);
    
    this.emit('criticalViolation', {
      type: violationType,
      details,
      timestamp: Date.now(),
      count: this.violationCounters.get(violationType) || 0,
    });
    
    // CRITICAL: System must enter safe mode
    this.emit('enterSafeMode', {
      reason: violationType,
      details,
    });
  }
  
  private incrementViolation(violationType: string): void {
    const current = this.violationCounters.get(violationType) || 0;
    this.violationCounters.set(violationType, current + 1);
  }
}

// Singleton instance
export const metricsCollector = new MetricsCollector();
