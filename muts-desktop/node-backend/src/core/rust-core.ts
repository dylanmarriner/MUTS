/**
 * Rust Core Interface
 * Provides N-API bindings to the Rust safety-critical operations
 */

import { Logger } from '../utils/logger';
import { ffi } from '@node-rs/ffi';
import { join } from 'path';

// Type definitions for Rust functions
interface RustCoreApi {
  initialize_core(): Promise<void>;
  list_interfaces(): Promise<InterfaceInfo[]>;
  connect_interface(interfaceId: string): Promise<ConnectionResult>;
  disconnect_interface(): Promise<void>;
  get_connection_status(): Promise<ConnectionStatus>;
  start_diagnostic_session(sessionType: string): Promise<string>;
  send_diagnostic_request(serviceId: number, data?: Buffer): Promise<DiagnosticResponse>;
  validate_rom(romData: Buffer): Promise<RomValidationResult>;
  verify_checksum(romData: Buffer): Promise<ChecksumResult>;
  prepare_flash(romData: Buffer, options: FlashOptions): Promise<FlashPrepareResult>;
  execute_flash(jobId: string): Promise<void>;
  abort_flash(jobId: string): Promise<void>;
  apply_live_changes(changes: LiveChange[]): Promise<ApplyResult>;
  revert_live_changes(sessionId: string): Promise<RevertResult>;
  arm_safety(level: SafetyLevel): Promise<void>;
  disarm_safety(): Promise<void>;
  get_safety_state(): Promise<SafetyStateInfo>;
}

// Type definitions
export interface InterfaceInfo {
  id: string;
  name: string;
  interfaceType: 'SocketCAN' | 'J2534' | 'CANALyst' | 'Vector' | 'Custom';
  capabilities: string[];
  isAvailable: boolean;
}

export interface ConnectionResult {
  success: boolean;
  sessionId: string;
  message: string;
}

export interface ConnectionStatus {
  connected: boolean;
  interfaceId: string;
  sessionCount: number;
  lastActivity?: Date;
}

export interface DiagnosticResponse {
  serviceId: number;
  data: Buffer;
  success: boolean;
  timestamp: Date;
  responseTimeMs: number;
}

export interface RomValidationResult {
  isValid: boolean;
  ecuType?: string;
  calibrationId?: string;
  checksumValid: boolean;
  size: number;
  errors: string[];
}

export interface ChecksumResult {
  valid: boolean;
  calculated: number;
  expected: number;
  algorithm: string;
}

export interface FlashOptions {
  verifyAfterWrite: boolean;
  backupBeforeFlash: boolean;
  skipRegions: string[];
}

export interface FlashPrepareResult {
  jobId: string;
  estimatedTimeSec: number;
  blocksToWrite: number;
  backupCreated: boolean;
}

export interface LiveChange {
  address: number;
  oldValue: Buffer;
  newValue: Buffer;
  changeType: 'SingleByte' | 'MultiByte' | 'Table';
}

export interface ApplyResult {
  success: boolean;
  changesApplied: number;
  failedChanges: number;
  sessionId: string;
}

export interface RevertResult {
  success: boolean;
  changesReverted: number;
  message: string;
}

export type SafetyLevel = 'ReadOnly' | 'Simulate' | 'LiveApply' | 'Flash';

export interface SafetyStateInfo {
  armed: boolean;
  level: SafetyLevel;
  timeRemaining?: number;
  violations: SafetyViolation[];
}

export interface SafetyViolation {
  parameter: string;
  value: number;
  limit: number;
  severity: 'Warning' | 'Critical';
}

export class RustCore {
  private logger: Logger;
  private lib: any;
  private api: RustCoreApi;
  private initialized: boolean = false;

  constructor() {
    this.logger = new Logger('RustCore');
    
    // Load the Rust library
    const libPath = join(__dirname, '../../rust-core/index.node');
    try {
      this.lib = ffi(libPath);
      this.initializeApi();
    } catch (error) {
      this.logger.error('Failed to load Rust library:', error);
      throw error;
    }
  }

  private initializeApi(): void {
    // Initialize the API with FFI bindings
    this.api = {
      initialize_core: this.lib.wrap('initialize_core', {
        args: [],
        returns: 'void',
        async: true,
      }),
      
      list_interfaces: this.lib.wrap('list_interfaces', {
        args: [],
        returns: 'json',
        async: true,
      }),
      
      connect_interface: this.lib.wrap('connect_interface', {
        args: ['string'],
        returns: 'json',
        async: true,
      }),
      
      disconnect_interface: this.lib.wrap('disconnect_interface', {
        args: [],
        returns: 'void',
        async: true,
      }),
      
      get_connection_status: this.lib.wrap('get_connection_status', {
        args: [],
        returns: 'json',
        async: true,
      }),
      
      start_diagnostic_session: this.lib.wrap('start_diagnostic_session', {
        args: ['string'],
        returns: 'string',
        async: true,
      }),
      
      send_diagnostic_request: this.lib.wrap('send_diagnostic_request', {
        args: ['uint8', 'buffer'],
        returns: 'json',
        async: true,
      }),
      
      validate_rom: this.lib.wrap('validate_rom', {
        args: ['buffer'],
        returns: 'json',
        async: true,
      }),
      
      verify_checksum: this.lib.wrap('verify_checksum', {
        args: ['buffer'],
        returns: 'json',
        async: true,
      }),
      
      prepare_flash: this.lib.wrap('prepare_flash', {
        args: ['buffer', 'json'],
        returns: 'json',
        async: true,
      }),
      
      execute_flash: this.lib.wrap('execute_flash', {
        args: ['string'],
        returns: 'void',
        async: true,
      }),
      
      abort_flash: this.lib.wrap('abort_flash', {
        args: ['string'],
        returns: 'void',
        async: true,
      }),
      
      apply_live_changes: this.lib.wrap('apply_live_changes', {
        args: ['json'],
        returns: 'json',
        async: true,
      }),
      
      revert_live_changes: this.lib.wrap('revert_live_changes', {
        args: ['string'],
        returns: 'json',
        async: true,
      }),
      
      arm_safety: this.lib.wrap('arm_safety', {
        args: ['string'],
        returns: 'void',
        async: true,
      }),
      
      disarm_safety: this.lib.wrap('disarm_safety', {
        args: [],
        returns: 'void',
        async: true,
      }),
      
      get_safety_state: this.lib.wrap('get_safety_state', {
        args: [],
        returns: 'json',
        async: true,
      }),
    };
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      await this.api.initialize_core();
      this.initialized = true;
      this.logger.info('Rust core initialized');
    } catch (error) {
      this.logger.error('Failed to initialize Rust core:', error);
      throw error;
    }
  }

  async listInterfaces(): Promise<InterfaceInfo[]> {
    this.ensureInitialized();
    return await this.api.list_interfaces();
  }

  async connectInterface(interfaceId: string): Promise<ConnectionResult> {
    this.ensureInitialized();
    const result = await this.api.connect_interface(interfaceId);
    
    // Convert dates
    if (result.timestamp) {
      result.timestamp = new Date(result.timestamp);
    }
    
    return result;
  }

  async disconnect(): Promise<void> {
    this.ensureInitialized();
    await this.api.disconnect_interface();
  }

  async isConnected(): Promise<boolean> {
    this.ensureInitialized();
    const status = await this.api.get_connection_status();
    return status.connected;
  }

  async getConnectionStatus(): Promise<ConnectionStatus> {
    this.ensureInitialized();
    const status = await this.api.get_connection_status();
    
    // Convert dates
    if (status.lastActivity) {
      status.lastActivity = new Date(status.lastActivity);
    }
    
    return status;
  }

  async startDiagnosticSession(sessionType: string): Promise<string> {
    this.ensureInitialized();
    return await this.api.start_diagnostic_session(sessionType);
  }

  async sendDiagnosticRequest(
    serviceId: number,
    data?: Buffer
  ): Promise<DiagnosticResponse> {
    this.ensureInitialized();
    const result = await this.api.send_diagnostic_request(serviceId, data);
    
    // Convert Buffer and Date
    result.data = Buffer.from(result.data);
    result.timestamp = new Date(result.timestamp);
    
    return result;
  }

  async validateRom(romData: Buffer): Promise<RomValidationResult> {
    this.ensureInitialized();
    return await this.api.validate_rom(romData);
  }

  async verifyChecksum(romData: Buffer): Promise<ChecksumResult> {
    this.ensureInitialized();
    return await this.api.verify_checksum(romData);
  }

  async prepareFlash(
    romData: Buffer,
    options: FlashOptions
  ): Promise<FlashPrepareResult> {
    this.ensureInitialized();
    return await this.api.prepare_flash(romData, options);
  }

  async executeFlash(jobId: string): Promise<void> {
    this.ensureInitialized();
    await this.api.execute_flash(jobId);
  }

  async abortFlash(jobId: string): Promise<void> {
    this.ensureInitialized();
    await this.api.abort_flash(jobId);
  }

  async applyLiveChanges(changes: LiveChange[]): Promise<ApplyResult> {
    this.ensureInitialized();
    
    // Convert Buffers
    const serializedChanges = changes.map(change => ({
      ...change,
      oldValue: Array.from(change.oldValue),
      newValue: Array.from(change.newValue),
    }));
    
    return await this.api.apply_live_changes(serializedChanges);
  }

  async revertLiveChanges(sessionId: string): Promise<RevertResult> {
    this.ensureInitialized();
    return await this.api.revert_live_changes(sessionId);
  }

  async armSafety(level: SafetyLevel): Promise<void> {
    this.ensureInitialized();
    await this.api.arm_safety(level);
  }

  async disarmSafety(): Promise<void> {
    this.ensureInitialized();
    await this.api.disarm_safety();
  }

  async getSafetyState(): Promise<SafetyStateInfo> {
    this.ensureInitialized();
    return await this.api.get_safety_state();
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new Error('Rust core not initialized');
    }
  }
}
