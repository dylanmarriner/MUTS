/**
 * Electron API type declarations
 */

interface ElectronAPI {
  // Interface methods
  interface: {
    list(): Promise<any[]>;
    connect(interfaceId: string): Promise<any>;
    disconnect(): Promise<any>;
    getStatus(): Promise<{ connected: boolean; interfaceId?: string }>;
    sendCanFrame(data: any): Promise<void>;
  };

  // System methods
  system: {
    getOperatorMode(): Promise<string>;
  };
  
  // Safety methods
  safety: {
    getStatus(): Promise<any>;
    arm(level: string): Promise<any>;
    disarm(): Promise<any>;
    createSnapshot(telemetry: any): Promise<any>;
  };
  
  // Flash methods
  flash: {
    validate(romData: ArrayBuffer): Promise<any>;
    checksum(romData: ArrayBuffer): Promise<any>;
    prepare(romData: Buffer, options: any): Promise<any>;
    execute(jobId: string): Promise<any>;
    abort(jobId: string): Promise<any>;
  };
  
  // Tuning methods
  tuning: {
    createSession(changesetId: string): Promise<any>;
    apply(sessionId: string, changes: any): Promise<any>;
  };
  
  // Diagnostic methods
  diagnostic: {
    start(): Promise<string>;
    readDTCs(): Promise<any[]>;
    clearDTCs(sessionId: string): Promise<any>;
  };
  
  // Telemetry methods
  telemetry: {
    start(): void;
    stop(): void;
    subscribe(callback: (data: any) => void): () => void;
    unsubscribe(): void;
    export(sessionId: string, format: string): Promise<any>;
  };
  
  // Configuration methods
  config: {
    load(): Promise<any>;
    get(): Promise<any>;
    setOperatorMode: (mode: string) => Promise<void>;
    setTechnician: (technicianId: string) => Promise<void>;
    clearTechnician: () => Promise<void>;
    skipModeSelection: (skip: boolean) => Promise<void>;
  };

  // Menu events
  onMenuAction(callback: (action: string) => void): void;
  removeAllListeners(channel: string): void;
  
  // Metrics (read-only)
  getMetrics(): Promise<any>;
  
  // Health probe
  healthCheckpoint(id: string, name: string, status: 'PASS' | 'FAIL' | 'DEGRADED', error?: string, metadata?: Record<string, any>): void;
  healthReport(): Promise<any>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};
