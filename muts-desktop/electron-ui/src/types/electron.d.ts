/**
 * Electron API type declarations
 */

interface ElectronAPI {
  // Interface methods
  interface: {
    list(): Promise<string[]>;
    connect(interfaceId: string): Promise<void>;
    disconnect(): Promise<void>;
    getStatus(): Promise<{ connected: boolean; interfaceId?: string }>;
    sendCanFrame(data: any): Promise<void>;
  };

  // System methods
  system: {
    getOperatorMode(): Promise<string>;
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
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

export {};
