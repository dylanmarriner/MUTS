/**
 * StateStore - Single source of truth for application state
 * Provides streaming updates and command handling
 */

import { EventEmitter } from 'events';
import { PrismaClient } from '@prisma/client';
import { metricsCollector } from '../metrics';

export interface ConnectionState {
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  interface: string | null;
  lastError: string | null;
  lastUpdate: Date;
}

export interface TelemetrySnapshot {
  timestamp: Date;
  rpm: number;
  speed: number;
  throttle: number;
  boost: number;
  afr: number;
  coolant: number;
  iat: number;
  knock: number;
}

export interface DiagnosticResults {
  dtcs: Array<{
    code: string;
    severity: 'info' | 'warning' | 'error';
    description: string;
  }>;
  lastScan: Date;
  inProgress: boolean;
}

export interface FlashState {
  activeJob: {
    id: string;
    state: 'idle' | 'preparing' | 'ready' | 'flashing' | 'verifying' | 'completed' | 'failed' | 'aborted';
    progress: number;
    blocksCompleted: number;
    totalBlocks: number;
  } | null;
  history: Array<{
    id: string;
    status: string;
    completedAt: Date;
  }>;
}

export interface SafetyState {
  armed: boolean;
  level: 'read_only' | 'simulation' | 'live_apply';
  lastEvent: {
    type: string;
    timestamp: Date;
    message: string;
  } | null;
}

export interface ApplicationState {
  connection: ConnectionState;
  telemetry: TelemetrySnapshot | null;
  diagnostics: DiagnosticResults;
  flash: FlashState;
  safety: SafetyState;
}

export interface Command {
  type: string;
  data?: any;
  timestamp: Date;
  id: string;
}

export class StateStore extends EventEmitter {
  private state: ApplicationState;
  private prisma: PrismaClient;
  private commandQueue: Command[] = [];
  private processing = false;
  
  constructor(prisma: PrismaClient) {
    super();
    
    this.prisma = prisma;
    this.state = this.initializeState();
    
    // Start processing commands
    this.startCommandProcessor();
    
    // Start state streaming
    this.startStateStreaming();
  }
  
  private initializeState(): ApplicationState {
    return {
      connection: {
        status: 'disconnected',
        interface: null,
        lastError: null,
        lastUpdate: new Date(),
      },
      telemetry: null,
      diagnostics: {
        dtcs: [],
        lastScan: new Date(),
        inProgress: false,
      },
      flash: {
        activeJob: null,
        history: [],
      },
      safety: {
        armed: false,
        level: 'read_only',
        lastEvent: null,
      },
    };
  }
  
  // Public API
  
  /**
   * Get current state snapshot
   */
  getState(): ApplicationState {
    return { ...this.state };
  }
  
  /**
   * Subscribe to state updates
   */
  subscribe(channel: string, callback: (data: any) => void): () => void {
    this.on(channel, callback);
    
    // Send current state immediately
    callback(this.getChannelState(channel));
    
    // Return unsubscribe function
    return () => this.off(channel, callback);
  }
  
  /**
   * Send command (non-blocking)
   */
  async sendCommand(type: string, data?: any): Promise<void> {
    const command: Command = {
      type,
      data,
      timestamp: new Date(),
      id: Math.random().toString(36).substr(2, 9),
    };
    
    this.commandQueue.push(command);
    this.emit('command:queued', command);
  }
  
  // State update methods
  
  updateConnection(update: Partial<ConnectionState>): void {
    this.state.connection = {
      ...this.state.connection,
      ...update,
      lastUpdate: new Date(),
    };
    
    this.emit('state:update', { channel: 'connection', data: this.state.connection });
  }
  
  updateTelemetry(telemetry: TelemetrySnapshot): void {
    const startTime = Date.now();
    
    this.state.telemetry = telemetry;
    this.emit('state:update', { channel: 'telemetry', data: telemetry });
    
    // Record latency
    const latency = Date.now() - startTime;
    metricsCollector.recordTelemetryLatency(latency);
  }
  
  updateDiagnostics(update: Partial<DiagnosticResults>): void {
    this.state.diagnostics = {
      ...this.state.diagnostics,
      ...update,
    };
    
    this.emit('state:update', { channel: 'diagnostics', data: this.state.diagnostics });
  }
  
  updateFlash(update: Partial<FlashState>): void {
    this.state.flash = {
      ...this.state.flash,
      ...update,
    };
    
    this.emit('state:update', { channel: 'flash', data: this.state.flash });
  }
  
  updateSafety(update: Partial<SafetyState>): void {
    this.state.safety = {
      ...this.state.safety,
      ...update,
    };
    
    this.emit('state:update', { channel: 'safety', data: this.state.safety });
  }
  
  // Private methods
  
  private getChannelState(channel: string): any {
    switch (channel) {
      case 'connection':
        return this.state.connection;
      case 'telemetry':
        return this.state.telemetry;
      case 'diagnostics':
        return this.state.diagnostics;
      case 'flash':
        return this.state.flash;
      case 'safety':
        return this.state.safety;
      default:
        return null;
    }
  }
  
  private startCommandProcessor(): void {
    setInterval(async () => {
      if (this.processing || this.commandQueue.length === 0) {
        return;
      }
      
      this.processing = true;
      
      while (this.commandQueue.length > 0) {
        const command = this.commandQueue.shift()!;
        await this.processCommand(command);
      }
      
      this.processing = false;
    }, 1); // Process as fast as possible
  }
  
  private async processCommand(command: Command): Promise<void> {
    const startTime = Date.now();
    
    try {
      this.emit('command:processing', command);
      
      switch (command.type) {
        case 'connection:connect':
          await this.handleConnect(command.data);
          break;
          
        case 'connection:disconnect':
          await this.handleDisconnect();
          break;
          
        case 'telemetry:start':
          await this.startTelemetryStream();
          break;
          
        case 'telemetry:stop':
          await this.stopTelemetryStream();
          break;
          
        case 'diagnostics:scan':
          await this.runDiagnosticScan();
          break;
          
        case 'safety:arm':
          await this.armSafetySystem(command.data.level);
          break;
          
        case 'safety:disarm':
          await this.disarmSafetySystem();
          break;
          
        case 'flash:prepare':
          await this.prepareFlash(command.data);
          break;
          
        case 'flash:start':
          await this.startFlash(command.data.jobId);
          break;
          
        case 'flash:abort':
          await this.abortFlash(command.data.jobId);
          break;
          
        default:
          console.warn(`Unknown command type: ${command.type}`);
      }
      
      this.emit('command:completed', command);
    } catch (error) {
      console.error(`Command failed: ${command.type}`, error);
      this.emit('command:failed', { command, error });
    }
    
    // Record IPC latency
    const latency = Date.now() - startTime;
    metricsCollector.recordIpcLatency(latency);
  }
  
  private async startTelemetryStream(): Promise<void> {
    // Simulate telemetry stream
    // In real implementation, would interface with Rust core
    setInterval(() => {
      if (this.state.connection.status === 'connected') {
        this.updateTelemetry({
          timestamp: new Date(),
          rpm: 2000 + Math.random() * 1000,
          speed: Math.random() * 100,
          throttle: Math.random() * 100,
          boost: -5 + Math.random() * 20,
          afr: 14.7 + (Math.random() - 0.5) * 2,
          coolant: 80 + Math.random() * 40,
          iat: 20 + Math.random() * 60,
          knock: Math.random() * 5,
        });
      }
    }, 100); // 10 Hz
  }
  
  private async stopTelemetryStream(): Promise<void> {
    // Stop telemetry stream
    console.log('Telemetry stream stopped');
  }
  
  private async runDiagnosticScan(): Promise<void> {
    this.updateDiagnostics({ inProgress: true });
    
    // Simulate diagnostic scan
    setTimeout(() => {
      this.updateDiagnostics({
        inProgress: false,
        dtcs: [
          {
            code: 'P0001',
            severity: 'info',
            description: 'Fuel volume regulator control circuit/open',
          },
        ],
        lastScan: new Date(),
      });
    }, 2000);
  }
  
  private async armSafetySystem(level: string): Promise<void> {
    this.updateSafety({
      armed: true,
      level: level as any,
      lastEvent: {
        type: 'armed',
        timestamp: new Date(),
        message: `Safety system armed at ${level} level`,
      },
    });
  }
  
  private async disarmSafetySystem(): Promise<void> {
    this.updateSafety({
      armed: false,
      level: 'read_only',
      lastEvent: {
        type: 'disarmed',
        timestamp: new Date(),
        message: 'Safety system disarmed',
      },
    });
  }
  
  private async handleConnect(interfaceName: string): Promise<void> {
    this.updateConnection({ status: 'connecting' });
    
    // Simulate connection
    setTimeout(() => {
      this.updateConnection({
        status: 'connected',
        interface: interfaceName,
      });
    }, 1000);
  }
  
  private async handleDisconnect(): Promise<void> {
    this.updateConnection({ status: 'disconnected', interface: null });
  }
  
  private async prepareFlash(data: any): Promise<void> {
    this.updateFlash({
      activeJob: {
        id: data.jobId,
        state: 'preparing',
        progress: 0,
        blocksCompleted: 0,
        totalBlocks: data.totalBlocks || 0,
      },
    });
  }
  
  private async startFlash(jobId: string): Promise<void> {
    if (this.state.flash.activeJob?.id === jobId) {
      this.updateFlash({
        activeJob: {
          ...this.state.flash.activeJob,
          state: 'flashing',
        },
      });
    }
  }
  
  private async abortFlash(jobId: string): Promise<void> {
    const startTime = Date.now();
    
    if (this.state.flash.activeJob?.id === jobId) {
      this.updateFlash({
        activeJob: {
          ...this.state.flash.activeJob,
          state: 'aborted',
        },
      });
    }
    
    // Record abort latency
    const latency = Date.now() - startTime;
    metricsCollector.recordAbortLatency(latency);
  }
  
  private startStateStreaming(): void {
    // Stream state updates to connected clients
    setInterval(() => {
      // Emit queue depths for metrics
      metricsCollector.updateQueueDepth('safety', 0);
      metricsCollector.updateQueueDepth('flash', this.state.flash.activeJob ? 1 : 0);
      metricsCollector.updateQueueDepth('telemetry', this.state.telemetry ? 1 : 0);
      metricsCollector.updateQueueDepth('logs', 10);
    }, 1000);
  }
}

// Singleton instance
export let stateStore: StateStore;

export const initializeStateStore = (prisma: PrismaClient) => {
  stateStore = new StateStore(prisma);
  return stateStore;
};
