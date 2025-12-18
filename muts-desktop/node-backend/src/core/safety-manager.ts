/**
 * Safety Manager
 * Enforces safety workflows and prevents accidental ECU damage
 */

import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { RustCore, SafetyLevel, SafetyStateInfo, SafetyViolation } from './rust-core';

export interface SafetyLimits {
  maxBoost: number; // PSI
  maxTimingAdvance: number; // degrees
  maxFuelPressure: number; // PSI
  maxRpm: number;
  minAfr: number;
  maxAfr: number;
  maxIat: number; // °C
  maxEct: number; // °C
}

export interface SafetySnapshot {
  id: string;
  timestamp: Date;
  parameters: Record<string, number>;
  checksum: string;
}

export interface SafetyEvent {
  type: 'armed' | 'disarmed' | 'violation' | 'warning' | 'emergency_stop';
  level: SafetyLevel;
  message: string;
  timestamp: Date;
}

export class SafetyManager extends EventEmitter {
  private logger: Logger;
  private rustCore: RustCore;
  private currentState: SafetyStateInfo | null = null;
  private snapshots: Map<string, SafetySnapshot> = new Map();
  private monitoringActive: boolean = false;
  private limits: SafetyLimits;

  constructor(rustCore: RustCore) {
    super();
    this.logger = new Logger('SafetyManager');
    this.rustCore = rustCore;
    this.limits = {
      maxBoost: 25.0,
      maxTimingAdvance: 35.0,
      maxFuelPressure: 80.0,
      maxRpm: 7000.0,
      minAfr: 11.0,
      maxAfr: 17.0,
      maxIat: 80.0,
      maxEct: 110.0,
    };
  }

  async initialize(): Promise<void> {
    try {
      // Get initial safety state
      this.currentState = await this.rustCore.getSafetyState();
      this.logger.info('Safety manager initialized');
    } catch (error) {
      this.logger.error('Failed to initialize safety manager:', error);
      throw error;
    }
  }

  async arm(level: SafetyLevel): Promise<void> {
    try {
      this.logger.info(`Arming safety system at level: ${level}`);
      
      await this.rustCore.armSafety(level);
      this.currentState = await this.rustCore.getSafetyState();
      
      // Emit safety event
      this.emitSafetyEvent('armed', level, `Safety system armed at ${level} level`);
      
      this.logger.info(`Safety system armed at level: ${level}`);
    } catch (error) {
      this.logger.error('Failed to arm safety system:', error);
      throw error;
    }
  }

  async disarm(): Promise<void> {
    try {
      this.logger.info('Disarming safety system');
      
      await this.rustCore.disarmSafety();
      this.currentState = await this.rustCore.getSafetyState();
      
      // Emit safety event
      this.emitSafetyEvent('disarmed', 'ReadOnly', 'Safety system disarmed');
      
      this.logger.info('Safety system disarmed');
    } catch (error) {
      this.logger.error('Failed to disarm safety system:', error);
      throw error;
    }
  }

  async getState(): Promise<SafetyStateInfo> {
    try {
      this.currentState = await this.rustCore.getSafetyState();
      return this.currentState;
    } catch (error) {
      this.logger.error('Failed to get safety state:', error);
      throw error;
    }
  }

  isArmed(): boolean {
    return this.currentState?.armed || false;
  }

  getLevel(): SafetyLevel {
    return this.currentState?.level || 'ReadOnly';
  }

  canConnect(): boolean {
    // Can always connect in read-only mode
    return true;
  }

  canFlash(): boolean {
    return this.isArmed() && this.getLevel() === 'Flash';
  }

  canApplyLive(): boolean {
    const level = this.getLevel();
    return this.isArmed() && (level === 'LiveApply' || level === 'Flash');
  }

  async checkParameters(parameters: Record<string, number>): Promise<SafetyViolation[]> {
    const violations: SafetyViolation[] = [];

    // Check against limits
    if (parameters.boost_pressure && parameters.boost_pressure > this.limits.maxBoost) {
      violations.push({
        parameter: 'boost_pressure',
        value: parameters.boost_pressure,
        limit: this.limits.maxBoost,
        severity: 'Critical',
      });
    }

    if (parameters.ignition_timing && parameters.ignition_timing > this.limits.maxTimingAdvance) {
      violations.push({
        parameter: 'ignition_timing',
        value: parameters.ignition_timing,
        limit: this.limits.maxTimingAdvance,
        severity: 'Critical',
      });
    }

    if (parameters.engine_rpm && parameters.engine_rpm > this.limits.maxRpm) {
      violations.push({
        parameter: 'engine_rpm',
        value: parameters.engine_rpm,
        limit: this.limits.maxRpm,
        severity: 'Critical',
      });
    }

    if (parameters.lambda) {
      if (parameters.lambda < this.limits.minAfr || parameters.lambda > this.limits.maxAfr) {
        violations.push({
          parameter: 'lambda',
          value: parameters.lambda,
          limit: parameters.lambda < this.limits.minAfr ? this.limits.minAfr : this.limits.maxAfr,
          severity: 'Warning',
        });
      }
    }

    if (parameters.iat && parameters.iat > this.limits.maxIat) {
      violations.push({
        parameter: 'iat',
        value: parameters.iat,
        limit: this.limits.maxIat,
        severity: 'Warning',
      });
    }

    if (parameters.ect && parameters.ect > this.limits.maxEct) {
      violations.push({
        parameter: 'ect',
        value: parameters.ect,
        limit: this.limits.maxEct,
        severity: 'Critical',
      });
    }

    // Emit violations if any
    if (violations.length > 0) {
      const criticalViolations = violations.filter(v => v.severity === 'Critical');
      
      if (criticalViolations.length > 0) {
        this.emitSafetyEvent('emergency_stop', this.getLevel(), 
          `Critical safety violations detected: ${criticalViolations.map(v => v.parameter).join(', ')}`);
        
        // Consider auto-disarming on critical violations
        if (this.canApplyLive() || this.canFlash()) {
          this.logger.warn('Auto-disarming due to critical safety violations');
          await this.disarm();
        }
      } else {
        this.emitSafetyEvent('warning', this.getLevel(),
          `Safety warnings: ${violations.map(v => v.parameter).join(', ')}`);
      }
    }

    return violations;
  }

  async createSnapshot(parameters: Record<string, number>): Promise<string> {
    const id = this.generateChecksum(parameters);
    const timestamp = new Date();
    
    const snapshot: SafetySnapshot = {
      id,
      timestamp,
      parameters: { ...parameters },
      checksum: id,
    };

    this.snapshots.set(id, snapshot);
    
    // Clean old snapshots (keep last 100)
    if (this.snapshots.size > 100) {
      const sorted = Array.from(this.snapshots.entries())
        .sort((a, b) => a[1].timestamp.getTime() - b[1].timestamp.getTime());
      
      for (let i = 0; i < sorted.length - 100; i++) {
        this.snapshots.delete(sorted[i][0]);
      }
    }

    this.logger.info(`Created safety snapshot: ${id}`);
    return id;
  }

  async getSnapshot(id: string): Promise<SafetySnapshot | null> {
    return this.snapshots.get(id) || null;
  }

  async restoreSnapshot(id: string): Promise<Record<string, number> | null> {
    const snapshot = this.snapshots.get(id);
    if (!snapshot) {
      return null;
    }

    this.logger.info(`Restoring from safety snapshot: ${id}`);
    return { ...snapshot.parameters };
  }

  startMonitoring(): void {
    if (this.monitoringActive) {
      return;
    }

    this.monitoringActive = true;
    this.logger.info('Starting safety monitoring');

    // In a real implementation, this would subscribe to telemetry events
    // and continuously check parameters
  }

  stopMonitoring(): void {
    if (!this.monitoringActive) {
      return;
    }

    this.monitoringActive = false;
    this.logger.info('Stopping safety monitoring');
  }

  updateLimits(limits: Partial<SafetyLimits>): void {
    this.limits = { ...this.limits, ...limits };
    this.logger.info('Updated safety limits', limits);
  }

  getLimits(): SafetyLimits {
    return { ...this.limits };
  }

  private emitSafetyEvent(type: SafetyEvent['type'], level: SafetyLevel, message: string): void {
    const event: SafetyEvent = {
      type,
      level,
      message,
      timestamp: new Date(),
    };

    this.emit('safetyEvent', event);
    this.emit('event', event);
  }

  private generateChecksum(parameters: Record<string, number>): string {
    // Simple checksum generation
    const sorted = Object.entries(parameters)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([k, v]) => `${k}:${v}`)
      .join('|');
    
    // Use a simple hash for now - in production, use crypto
    let hash = 0;
    for (let i = 0; i < sorted.length; i++) {
      const char = sorted.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16);
  }
}
