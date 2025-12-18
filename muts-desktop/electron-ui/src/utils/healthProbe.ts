/**
 * Startup Health Probe System
 * Tracks application startup checkpoints and generates health reports
 */

import * as fs from 'fs';
import * as path from 'path';
import { app } from 'electron';

export type CheckpointStatus = 'PENDING' | 'PASS' | 'FAIL' | 'DEGRADED';

export interface Checkpoint {
  id: string;
  name: string;
  status: CheckpointStatus;
  timestamp: number;
  error?: string;
  metadata?: Record<string, any>;
}

export interface HealthReport {
  overall: 'HEALTHY' | 'DEGRADED' | 'FAILED';
  startTime: number;
  endTime?: number;
  checkpoints: Checkpoint[];
  errors: string[];
  warnings: string[];
}

class HealthProbe {
  private checkpoints: Map<string, Checkpoint> = new Map();
  private errors: string[] = [];
  private warnings: string[] = [];
  private startTime: number = Date.now();
  private reportPath: string;

  constructor() {
    // Store report in build_artifacts directory
    const workspaceRoot = path.resolve(__dirname, '../../../../');
    const artifactsDir = path.join(workspaceRoot, 'build_artifacts');
    if (!fs.existsSync(artifactsDir)) {
      fs.mkdirSync(artifactsDir, { recursive: true });
    }
    this.reportPath = path.join(artifactsDir, 'self_test_report.json');
    const tracePath = path.join(artifactsDir, 'startup_trace.log');
    
    // Initialize trace log
    fs.writeFileSync(tracePath, `[${new Date().toISOString()}] Health probe initialized\n`, 'utf-8');
  }

  /**
   * Register a checkpoint
   */
  checkpoint(id: string, name: string, status: CheckpointStatus, error?: string, metadata?: Record<string, any>): void {
    const checkpoint: Checkpoint = {
      id,
      name,
      status,
      timestamp: Date.now(),
      error,
      metadata,
    };
    
    this.checkpoints.set(id, checkpoint);
    
    // Write to trace log
    const tracePath = path.join(path.dirname(this.reportPath), 'startup_trace.log');
    const logLine = `[${new Date().toISOString()}] ${id}: ${name} - ${status}${error ? ` - ERROR: ${error}` : ''}\n`;
    fs.appendFileSync(tracePath, logLine, 'utf-8');
    
    if (status === 'FAIL') {
      this.errors.push(`${id}: ${name} - ${error || 'Unknown error'}`);
    } else if (status === 'DEGRADED') {
      this.warnings.push(`${id}: ${name} - ${error || 'Degraded state'}`);
    }
  }

  /**
   * Generate final health report
   */
  generateReport(): HealthReport {
    const checkpoints = Array.from(this.checkpoints.values());
    const failed = checkpoints.filter(c => c.status === 'FAIL');
    const degraded = checkpoints.filter(c => c.status === 'DEGRADED');
    
    let overall: 'HEALTHY' | 'DEGRADED' | 'FAILED';
    if (failed.length > 0) {
      overall = 'FAILED';
    } else if (degraded.length > 0) {
      overall = 'DEGRADED';
    } else {
      overall = 'HEALTHY';
    }

    const report: HealthReport = {
      overall,
      startTime: this.startTime,
      endTime: Date.now(),
      checkpoints,
      errors: this.errors,
      warnings: this.warnings,
    };

    // Write report to disk
    fs.writeFileSync(this.reportPath, JSON.stringify(report, null, 2), 'utf-8');
    
    return report;
  }

  /**
   * Get current health status
   */
  getStatus(): HealthReport {
    return this.generateReport();
  }
}

// Singleton instance
let healthProbeInstance: HealthProbe | null = null;

export function getHealthProbe(): HealthProbe {
  if (!healthProbeInstance) {
    healthProbeInstance = new HealthProbe();
  }
  return healthProbeInstance;
}

// Checkpoint IDs (must match across main and renderer)
export const CHECKPOINTS = {
  MAIN_STARTED: 'MAIN_STARTED',
  PRELOAD_OK: 'PRELOAD_OK',
  RENDERER_LOADED: 'RENDERER_LOADED',
  IPC_READY: 'IPC_READY',
  BACKEND_READY: 'BACKEND_READY',
  RUST_CORE_LOADED: 'RUST_CORE_LOADED',
  UI_VISIBLE: 'UI_VISIBLE',
  CONFIG_LOADED: 'CONFIG_LOADED',
} as const;

