/**
 * Data Streamer
 * Manages streaming of telemetry data to clients
 */

import { EventEmitter } from 'events';
import { TelemetryData, StreamConfig } from './types';

export class DataStreamer extends EventEmitter {
  private config: StreamConfig;
  private currentData: TelemetryData | null = null;
  private dataBuffer: TelemetryData[] = [];
  private streamActive = false;
  private lastSampleTime = 0;
  private sampleInterval = 1000 / 50; // 50 Hz default

  constructor(config: StreamConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    this.sampleInterval = 1000 / this.config.sampleRate;
    this.emit('initialized');
  }

  async start(sessionId: string): Promise<void> {
    this.streamActive = true;
    this.dataBuffer = [];
    this.emit('streamStarted', sessionId);
  }

  async stop(): Promise<void> {
    this.streamActive = false;
    this.emit('streamStopped');
  }

  addDataPoint(data: TelemetryData): void {
    const now = Date.now();
    
    // Rate limiting
    if (now - this.lastSampleTime < this.sampleInterval) {
      return;
    }
    
    this.currentData = data;
    this.dataBuffer.push(data);
    
    // Maintain buffer size
    if (this.dataBuffer.length > this.config.bufferSize) {
      this.dataBuffer.shift();
    }
    
    this.lastSampleTime = now;
    
    if (this.streamActive) {
      this.emit('data', data);
    }
  }

  getCurrentData(): TelemetryData | null {
    return this.currentData;
  }

  getBufferedData(count?: number): TelemetryData[] {
    if (count) {
      return this.dataBuffer.slice(-count);
    }
    return [...this.dataBuffer];
  }

  getCurrentSampleRate(): number {
    // Calculate actual sample rate from recent data
    if (this.dataBuffer.length < 2) {
      return 0;
    }
    
    const recent = this.dataBuffer.slice(-10);
    const timeSpan = recent[recent.length - 1].timestamp - recent[0].timestamp;
    
    return timeSpan > 0 ? (recent.length - 1) * 1000 / timeSpan : 0;
  }

  updateConfig(config: StreamConfig): void {
    this.config = config;
    this.sampleInterval = 1000 / config.sampleRate;
    this.emit('configUpdated', config);
  }

  async shutdown(): Promise<void> {
    await this.stop();
    this.emit('shutdown');
  }
}
