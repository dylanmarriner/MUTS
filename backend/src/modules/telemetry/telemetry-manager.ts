/**
 * Telemetry Manager
 * Orchestrates real-time data streaming and processing
 */

import { EventEmitter } from 'events';
import { CANProcessor } from './can-processor';
import { DataStreamer } from './data-streamer';
import { SignalDecoder } from './signal-decoder';
import { TelemetryData, StreamConfig, TelemetrySession, CANMessage } from './types';

export class TelemetryManager extends EventEmitter {
  private canProcessor: CANProcessor;
  private dataStreamer: DataStreamer;
  private signalDecoder: SignalDecoder;
  private currentSession: TelemetrySession | null = null;
  private isStreaming = false;
  private config: StreamConfig;

  constructor(config: Partial<StreamConfig> = {}) {
    super();
    
    this.config = {
      enabled: true,
      sampleRate: 50, // 50 Hz
      bufferSize: 1000,
      compressionEnabled: false,
      ...config
    };

    this.canProcessor = new CANProcessor();
    this.dataStreamer = new DataStreamer(this.config);
    this.signalDecoder = new SignalDecoder();
    
    this.setupEventHandlers();
  }

  async initialize(): Promise<void> {
    await this.canProcessor.initialize();
    await this.dataStreamer.initialize();
    await this.signalDecoder.loadDBC();
    
    this.emit('initialized');
  }

  async startStreaming(): Promise<string> {
    if (this.isStreaming) {
      throw new Error('Streaming already active');
    }

    const sessionId = this.generateSessionId();
    this.currentSession = {
      id: sessionId,
      startTime: Date.now(),
      dataPoints: [],
      config: this.config
    };

    await this.canProcessor.start();
    await this.dataStreamer.start(sessionId);
    
    this.isStreaming = true;
    this.emit('streamingStarted', sessionId);
    
    return sessionId;
  }

  async stopStreaming(): Promise<void> {
    if (!this.isStreaming || !this.currentSession) {
      return;
    }

    await this.canProcessor.stop();
    await this.dataStreamer.stop();
    
    this.currentSession.endTime = Date.now();
    this.isStreaming = false;
    
    this.emit('streamingStopped', this.currentSession);
    this.currentSession = null;
  }

  getCurrentData(): TelemetryData | null {
    return this.dataStreamer.getCurrentData();
  }

  getSessionHistory(sessionId: string): TelemetryData[] {
    // Return session data from storage
    return [];
  }

  getLiveMetrics(): {
    sampleRate: number;
    dataPoints: number;
    errors: number;
    uptime: number;
  } {
    return {
      sampleRate: this.dataStreamer.getCurrentSampleRate(),
      dataPoints: this.currentSession?.dataPoints.length || 0,
      errors: this.canProcessor.getErrorCount(),
      uptime: this.currentSession ? Date.now() - this.currentSession.startTime : 0
    };
  }

  updateConfig(config: Partial<StreamConfig>): void {
    this.config = { ...this.config, ...config };
    this.dataStreamer.updateConfig(this.config);
    this.emit('configUpdated', this.config);
  }

  private setupEventHandlers(): void {
    this.canProcessor.on('message', (message: CANMessage) => {
      const decoded = this.signalDecoder.decodeMessage(message);
      if (decoded) {
        this.dataStreamer.addDataPoint(decoded);
        
        if (this.currentSession) {
          this.currentSession.dataPoints.push(decoded);
        }
        
        this.emit('data', decoded);
      }
    });

    this.canProcessor.on('error', (error: Error) => {
      this.emit('error', error);
    });
  }

  private generateSessionId(): string {
    return `tel_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async shutdown(): Promise<void> {
    if (this.isStreaming) {
      await this.stopStreaming();
    }
    
    await this.canProcessor.shutdown();
    await this.dataStreamer.shutdown();
    
    this.emit('shutdown');
  }
}
