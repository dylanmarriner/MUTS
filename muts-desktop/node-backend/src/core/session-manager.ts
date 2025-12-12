/**
 * Session Manager
 * Manages connection, diagnostic, and tuning sessions
 */

import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { RustCore } from './rust-core';
import { v4 as uuidv4 } from 'uuid';

export interface SessionInfo {
  id: string;
  type: 'connection' | 'diagnostic' | 'tuning' | 'flash';
  status: 'active' | 'idle' | 'error';
  startTime: Date;
  endTime?: Date;
  metadata: Record<string, any>;
}

export interface TelemetryData {
  timestamp: Date;
  signals: Record<string, number>;
  metadata: {
    source: string;
    sampleRate: number;
    quality: 'good' | 'fair' | 'poor' | 'invalid';
  };
}

export interface CanFrame {
  id: number;
  extended: boolean;
  data: Buffer;
  timestamp: Date;
}

export class SessionManager extends EventEmitter {
  private logger: Logger;
  private rustCore: RustCore;
  private sessions: Map<string, SessionInfo> = new Map();
  private currentConnectionId?: string;
  private streamingActive: boolean = false;

  constructor(rustCore: RustCore) {
    super();
    this.logger = new Logger('SessionManager');
    this.rustCore = rustCore;
  }

  async connectInterface(interfaceId: string): Promise<SessionInfo> {
    try {
      this.logger.info(`Connecting to interface: ${interfaceId}`);

      // Connect via Rust core
      const result = await this.rustCore.connectInterface(interfaceId);
      
      if (!result.success) {
        throw new Error(result.message);
      }

      // Create connection session
      const session: SessionInfo = {
        id: result.sessionId,
        type: 'connection',
        status: 'active',
        startTime: new Date(),
        metadata: {
          interfaceId,
          connected: true,
        },
      };

      this.sessions.set(session.id, session);
      this.currentConnectionId = session.id;

      // Start streaming automatically on connection
      await this.startStreaming();

      this.logger.info(`Connected successfully, session: ${session.id}`);
      this.emit('sessionCreated', session);
      this.emit('connected', session);

      return session;
    } catch (error) {
      this.logger.error('Failed to connect:', error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (!this.currentConnectionId) {
      return;
    }

    try {
      this.logger.info('Disconnecting from interface');

      // Stop streaming
      await this.stopStreaming();

      // Disconnect via Rust core
      await this.rustCore.disconnect();

      // Update session
      const session = this.sessions.get(this.currentConnectionId);
      if (session) {
        session.status = 'idle';
        session.endTime = new Date();
        session.metadata.connected = false;
        this.emit('sessionUpdated', session);
      }

      this.currentConnectionId = undefined;
      this.logger.info('Disconnected successfully');
      this.emit('disconnected');
    } catch (error) {
      this.logger.error('Failed to disconnect:', error);
      throw error;
    }
  }

  async isConnected(): Promise<boolean> {
    return await this.rustCore.isConnected();
  }

  async getConnectionStatus(): Promise<any> {
    return await this.rustCore.getConnectionStatus();
  }

  async startDiagnosticSession(sessionType: string = 'default'): Promise<SessionInfo> {
    if (!this.currentConnectionId) {
      throw new Error('No active connection');
    }

    try {
      this.logger.info(`Starting diagnostic session: ${sessionType}`);

      // Start session via Rust core
      const sessionId = await this.rustCore.startDiagnosticSession(sessionType);

      const session: SessionInfo = {
        id: sessionId,
        type: 'diagnostic',
        status: 'active',
        startTime: new Date(),
        metadata: {
          sessionType,
          connectionId: this.currentConnectionId,
        },
      };

      this.sessions.set(session.id, session);
      this.logger.info(`Diagnostic session started: ${session.id}`);
      this.emit('sessionCreated', session);

      return session;
    } catch (error) {
      this.logger.error('Failed to start diagnostic session:', error);
      throw error;
    }
  }

  async sendDiagnosticRequest(
    serviceId: number,
    data?: Buffer
  ): Promise<any> {
    if (!this.currentConnectionId) {
      throw new Error('No active connection');
    }

    try {
      return await this.rustCore.sendDiagnosticRequest(serviceId, data);
    } catch (error) {
      this.logger.error('Failed to send diagnostic request:', error);
      throw error;
    }
  }

  async createTuningSession(changesetId: string): Promise<SessionInfo> {
    if (!this.currentConnectionId) {
      throw new Error('No active connection');
    }

    const session: SessionInfo = {
      id: uuidv4(),
      type: 'tuning',
      status: 'active',
      startTime: new Date(),
      metadata: {
        changesetId,
        connectionId: this.currentConnectionId,
        appliedChanges: 0,
        failedChanges: 0,
      },
    };

    this.sessions.set(session.id, session);
    this.logger.info(`Tuning session created: ${session.id}`);
    this.emit('sessionCreated', session);

    return session;
  }

  async applyLiveChanges(
    sessionId: string,
    changes: any[]
  ): Promise<any> {
    const session = this.sessions.get(sessionId);
    if (!session || session.type !== 'tuning') {
      throw new Error('Invalid tuning session');
    }

    try {
      const result = await this.rustCore.applyLiveChanges(changes);
      
      // Update session metadata
      session.metadata.appliedChanges = result.changesApplied;
      session.metadata.failedChanges = result.failedChanges;
      this.emit('sessionUpdated', session);

      return result;
    } catch (error) {
      this.logger.error('Failed to apply live changes:', error);
      throw error;
    }
  }

  async revertLiveChanges(sessionId: string): Promise<any> {
    const session = this.sessions.get(sessionId);
    if (!session || session.type !== 'tuning') {
      throw new Error('Invalid tuning session');
    }

    try {
      const result = await this.rustCore.revertLiveChanges(sessionId);
      
      // Update session
      session.status = 'idle';
      session.endTime = new Date();
      this.emit('sessionUpdated', session);

      return result;
    } catch (error) {
      this.logger.error('Failed to revert live changes:', error);
      throw error;
    }
  }

  async startFlashSession(
    romData: Buffer,
    options: any
  ): Promise<SessionInfo> {
    if (!this.currentConnectionId) {
      throw new Error('No active connection');
    }

    try {
      // Prepare flash
      const prepareResult = await this.rustCore.prepareFlash(romData, options);

      const session: SessionInfo = {
        id: prepareResult.jobId,
        type: 'flash',
        status: 'active',
        startTime: new Date(),
        metadata: {
          jobId: prepareResult.jobId,
          estimatedTime: prepareResult.estimatedTimeSec,
          blocksToWrite: prepareResult.blocksToWrite,
          backupCreated: prepareResult.backupCreated,
          connectionId: this.currentConnectionId,
        },
      };

      this.sessions.set(session.id, session);
      this.logger.info(`Flash session created: ${session.id}`);
      this.emit('sessionCreated', session);

      return session;
    } catch (error) {
      this.logger.error('Failed to create flash session:', error);
      throw error;
    }
  }

  async executeFlash(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session || session.type !== 'flash') {
      throw new Error('Invalid flash session');
    }

    try {
      await this.rustCore.executeFlash(sessionId);
      this.logger.info(`Flash execution started: ${sessionId}`);
    } catch (error) {
      this.logger.error('Failed to execute flash:', error);
      throw error;
    }
  }

  async abortFlash(sessionId: string): Promise<void> {
    const session = this.sessions.get(sessionId);
    if (!session || session.type !== 'flash') {
      throw new Error('Invalid flash session');
    }

    try {
      await this.rustCore.abortFlash(sessionId);
      
      // Update session
      session.status = 'error';
      session.endTime = new Date();
      this.emit('sessionUpdated', session);

      this.logger.info(`Flash aborted: ${sessionId}`);
    } catch (error) {
      this.logger.error('Failed to abort flash:', error);
      throw error;
    }
  }

  private async startStreaming(): Promise<void> {
    if (this.streamingActive) {
      return;
    }

    this.streamingActive = true;
    this.logger.info('Starting telemetry stream');

    // In a real implementation, this would subscribe to Rust core events
    // For now, simulate with mock data
    this.simulateStreaming();
  }

  private async stopStreaming(): Promise<void> {
    if (!this.streamingActive) {
      return;
    }

    this.streamingActive = false;
    this.logger.info('Stopping telemetry stream');
  }

  private simulateStreaming(): void {
    if (!this.streamingActive) {
      return;
    }

    // Simulate telemetry data
    const telemetry: TelemetryData = {
      timestamp: new Date(),
      signals: {
        engine_rpm: 2000 + Math.random() * 2000,
        vehicle_speed: Math.random() * 100,
        boost_pressure: Math.random() * 20,
        throttle_position: Math.random() * 100,
        lambda: 14.7 + (Math.random() - 0.5) * 2,
        ignition_timing: 10 + Math.random() * 20,
        iat: 20 + Math.random() * 60,
        ect: 80 + Math.random() * 30,
      },
      metadata: {
        source: 'CAN',
        sampleRate: 10,
        quality: 'good',
      },
    };

    this.emit('telemetry', telemetry);

    // Continue streaming
    setTimeout(() => this.simulateStreaming(), 100);
  }

  getSessions(): SessionInfo[] {
    return Array.from(this.sessions.values());
  }

  getSession(id: string): SessionInfo | undefined {
    return this.sessions.get(id);
  }

  getCurrentConnection(): SessionInfo | undefined {
    if (!this.currentConnectionId) {
      return undefined;
    }
    return this.sessions.get(this.currentConnectionId);
  }
}
