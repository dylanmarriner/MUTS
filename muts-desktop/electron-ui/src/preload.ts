/**
 * Electron Preload Script
 * Exposes safe APIs to the renderer process
 */

import { contextBridge, ipcRenderer } from 'electron';

// Initialize electronAPI with safe defaults
const electronAPI: any = {
  // App info
  getVersion: () => {
    try {
      return ipcRenderer.invoke('app:getVersion');
    } catch (error) {
      console.error('Failed to get version:', error);
      return '1.0.0';
    }
  },
  getPath: (name: string) => {
    try {
      return ipcRenderer.invoke('app:getPath', name);
    } catch (error) {
      console.error('Failed to get path:', error);
      return '';
    }
  },
  
  getOperatorMode: () => {
    try {
      return ipcRenderer.invoke('system:getOperatorMode');
    } catch (error) {
      console.error('Failed to get operator mode:', error);
      return Promise.resolve('dev'); // Safe default
    }
  },

  // State management (non-blocking)
  subscribe: (channel: string, callback: (data: any) => void) => {
    try {
      const subscription = ipcRenderer.on(channel, (_: any, data: any) => callback(data));
      // Send current state immediately
      ipcRenderer.send('state:subscribe', { channel });
      return () => {
        try {
          subscription.removeListener(channel, (_: any, data: any) => callback(data));
          ipcRenderer.send('state:unsubscribe', { channel });
        } catch (error) {
          console.error('Failed to unsubscribe:', error);
        }
      };
    } catch (error) {
      console.error('Failed to subscribe:', error);
      return () => {}; // Return empty function as fallback
    }
  },

  // Command sending (non-blocking)
  sendCommand: (type: string, data?: any) => {
    try {
      ipcRenderer.send('command', { type, data });
    } catch (error) {
      console.error('Failed to send command:', error);
    }
  },

  // Interface management (commands + state)
  interface: {
    connect: (interfaceId: string) => {
      try {
        return ipcRenderer.invoke('interface:connect', interfaceId);
      } catch (error) {
        console.error('Failed to connect interface:', error);
        return Promise.reject(error);
      }
    },
    disconnect: () => {
      try {
        return ipcRenderer.invoke('interface:disconnect');
      } catch (error) {
        console.error('Failed to disconnect:', error);
        return Promise.reject(error);
      }
    },
    subscribe: (callback: (state: any) => void) => {
      try {
        return electronAPI.subscribe('connection', callback);
      } catch (error) {
        console.error('Failed to subscribe to connection:', error);
        return () => {};
      }
    },
    list: () => {
      try {
        return ipcRenderer.invoke('interface:list');
      } catch (error) {
        console.error('Failed to list interfaces:', error);
        return [];
      }
    },
    getStatus: () => {
      try {
        return ipcRenderer.invoke('interface:getStatus');
      } catch (error) {
        console.error('Failed to get interface status:', error);
        return { connected: false, type: null };
      }
    },
  },

  // Session management
  session: {
    create: (config: any) => {
      try {
        electronAPI.sendCommand('session:create', config);
      } catch (error) {
        console.error('Failed to create session:', error);
      }
    },
    close: () => {
      try {
        electronAPI.sendCommand('session:close');
      } catch (error) {
        console.error('Failed to close session:', error);
      }
    },
    subscribe: (callback: (state: any) => void) => {
      try {
        return electronAPI.subscribe('session', callback);
      } catch (error) {
        console.error('Failed to subscribe to session:', error);
        return () => {};
      }
    },
  },

  // Safety management
  safety: {
    getStatus: () => {
      try {
        return ipcRenderer.invoke('safety:getStatus');
      } catch (error) {
        console.error('Failed to get safety status:', error);
        return Promise.resolve({ armed: false, mode: 'unknown' });
      }
    },
    arm: (level: string) => {
      try {
        return ipcRenderer.invoke('safety:arm', level);
      } catch (error) {
        console.error('Failed to arm safety:', error);
        return Promise.reject(error);
      }
    },
    disarm: () => {
      try {
        return ipcRenderer.invoke('safety:disarm');
      } catch (error) {
        console.error('Failed to disarm safety:', error);
        return Promise.reject(error);
      }
    },
    createSnapshot: (telemetry: any) => {
      try {
        return ipcRenderer.invoke('safety:createSnapshot', telemetry);
      } catch (error) {
        console.error('Failed to create snapshot:', error);
        return Promise.reject(error);
      }
    },
    subscribe: (callback: (state: any) => void) => {
      try {
        return electronAPI.subscribe('safety', callback);
      } catch (error) {
        console.error('Failed to subscribe to safety:', error);
        return () => {};
      }
    },
  },

  // Configuration
  config: {
    get: (key: string) => {
      try {
        return ipcRenderer.invoke('config:get', key);
      } catch (error) {
        console.error('Failed to get config:', error);
        return null;
      }
    },
    set: (key: string, value: any) => {
      try {
        return ipcRenderer.invoke('config:set', key, value);
      } catch (error) {
        console.error('Failed to set config:', error);
        return null;
      }
    },
    load: () => {
      try {
        return ipcRenderer.invoke('config:load');
      } catch (error) {
        console.error('Failed to load config:', error);
        return {};
      }
    },
    setOperatorMode: (mode: string) => {
      try {
        return ipcRenderer.invoke('config:setOperatorMode', mode);
      } catch (error) {
        console.error('Failed to set operator mode:', error);
        return null;
      }
    },
    setTechnician: (technicianId: string) => {
      try {
        return ipcRenderer.invoke('config:setTechnician', technicianId);
      } catch (error) {
        console.error('Failed to set technician:', error);
        return null;
      }
    },
    skipModeSelection: (skip: boolean) => {
      try {
        return ipcRenderer.invoke('config:skipModeSelection', skip);
      } catch (error) {
        console.error('Failed to skip mode selection:', error);
        return null;
      }
    },
  },

  // Database operations (still blocking for now)
  db: {
    vehicle: {
      create: (vehicle: any) => {
        try {
          return ipcRenderer.invoke('db:vehicle:create', vehicle);
        } catch (error) {
          console.error('Failed to create vehicle:', error);
          return null;
        }
      },
      get: (vin: string) => {
        try {
          return ipcRenderer.invoke('db:vehicle:get', vin);
        } catch (error) {
          console.error('Failed to get vehicle:', error);
          return null;
        }
      },
      list: () => {
        try {
          return ipcRenderer.invoke('db:vehicle:list');
        } catch (error) {
          console.error('Failed to list vehicles:', error);
          return [];
        }
      },
    },
    profile: {
      create: (profile: any) => {
        try {
          return ipcRenderer.invoke('db:profile:create', profile);
        } catch (error) {
          console.error('Failed to create profile:', error);
          return null;
        }
      },
      list: (vehicleId?: string) => {
        try {
          return ipcRenderer.invoke('db:profile:list', vehicleId);
        } catch (error) {
          console.error('Failed to list profiles:', error);
          return [];
        }
      },
    },
  },

  // Telemetry (state streaming)
  telemetry: {
    start: () => {
      try {
        electronAPI.sendCommand('telemetry:start');
      } catch (error) {
        console.error('Failed to start telemetry:', error);
      }
    },
    stop: () => {
      try {
        electronAPI.sendCommand('telemetry:stop');
      } catch (error) {
        console.error('Failed to stop telemetry:', error);
      }
    },
    subscribe: (callback: (data: any) => void) => {
      try {
        return electronAPI.subscribe('telemetry', callback);
      } catch (error) {
        console.error('Failed to subscribe to telemetry:', error);
        return () => {};
      }
    },
    unsubscribe: () => {
      try {
        electronAPI.sendCommand('telemetry:unsubscribe');
      } catch (error) {
        console.error('Failed to unsubscribe from telemetry:', error);
      }
    },
    export: (sessionId: string, format: string) => {
      try {
        return ipcRenderer.invoke('telemetry:export', sessionId, format);
      } catch (error) {
        console.error('Failed to export telemetry:', error);
        return Promise.resolve(null);
      }
    },
  },

  // Flash operations
  flash: {
    validate: (romData: ArrayBuffer) => {
      try {
        return ipcRenderer.invoke('flash:validate', romData);
      } catch (error) {
        console.error('Failed to validate ROM:', error);
        return Promise.resolve({ valid: false, errors: ['Validation failed'] });
      }
    },
    checksum: (romData: ArrayBuffer) => {
      try {
        return ipcRenderer.invoke('flash:checksum', romData);
      } catch (error) {
        console.error('Failed to calculate checksum:', error);
        return Promise.resolve({ checksum: '00000000', valid: false });
      }
    },
    prepare: (romData: Buffer, options: any) => {
      try {
        return ipcRenderer.invoke('flash:prepare', romData, options);
      } catch (error) {
        console.error('Failed to prepare flash:', error);
        return Promise.reject(error);
      }
    },
    execute: (jobId: string) => {
      try {
        return ipcRenderer.invoke('flash:execute', jobId);
      } catch (error) {
        console.error('Failed to execute flash:', error);
        return Promise.reject(error);
      }
    },
    abort: (jobId: string) => {
      try {
        return ipcRenderer.invoke('flash:abort', jobId);
      } catch (error) {
        console.error('Failed to abort flash:', error);
        return Promise.reject(error);
      }
    },
  },

  // Tuning operations
  tuning: {
    createSession: (changesetId: string) => {
      try {
        return ipcRenderer.invoke('tuning:createSession', changesetId);
      } catch (error) {
        console.error('Failed to create tuning session:', error);
        return null;
      }
    },
    apply: (sessionId: string, changes: any) => {
      try {
        return ipcRenderer.invoke('tuning:apply', sessionId, changes);
      } catch (error) {
        console.error('Failed to apply tuning:', error);
        return Promise.reject(error);
      }
    },
  },
  
  // Diagnostic operations
  diagnostic: {
    start: () => {
      try {
        return ipcRenderer.invoke('diagnostic:start');
      } catch (error) {
        console.error('Failed to start diagnostic:', error);
        return Promise.reject(error);
      }
    },
    readDTCs: () => {
      try {
        return ipcRenderer.invoke('diagnostic:readDTCs');
      } catch (error) {
        console.error('Failed to read DTCs:', error);
        return Promise.resolve([]);
      }
    },
    clearDTCs: (sessionId: string) => {
      try {
        return ipcRenderer.invoke('diagnostic:clearDTCs', sessionId);
      } catch (error) {
        console.error('Failed to clear DTCs:', error);
        return Promise.reject(error);
      }
    },
  },

  // Menu events
  onMenuAction: (callback: (action: string) => void) => {
    try {
      ipcRenderer.on('menu:open-rom', () => callback('open-rom'));
      ipcRenderer.on('menu:save-profile', () => callback('save-profile'));
      ipcRenderer.on('menu:connect', () => callback('connect'));
      ipcRenderer.on('menu:arm-safety', () => callback('arm-safety'));
    } catch (error) {
      console.error('Failed to set up menu listeners:', error);
    }
  },
  
  // Debug logging
  debugLog: (location: string, message: string, data: any, hypothesisId: string) => {
    try {
      ipcRenderer.invoke('debug:log', location, message, data, hypothesisId);
    } catch (error) {
      console.error('Failed to send debug log:', error);
    }
  },
  
  // Health probe
  healthCheckpoint: (id: string, name: string, status: 'PASS' | 'FAIL' | 'DEGRADED', error?: string, metadata?: Record<string, any>) => {
    try {
      ipcRenderer.invoke('health:checkpoint', id, name, status, error, metadata);
    } catch (err) {
      console.error('Failed to send health checkpoint:', err);
    }
  },
  
  healthReport: () => {
    try {
      return ipcRenderer.invoke('health:report');
    } catch (err) {
      console.error('Failed to get health report:', err);
      return null;
    }
  },
};

// Expose the API to the renderer process
try {
  contextBridge.exposeInMainWorld('electronAPI', electronAPI);
  // Report preload success to health probe
  ipcRenderer.invoke('health:checkpoint', 'PRELOAD_OK', 'Preload script executed', 'PASS').catch(() => {});
} catch (error) {
  console.error('Failed to expose electronAPI:', error);
  // Report preload failure to health probe
  ipcRenderer.invoke('health:checkpoint', 'PRELOAD_OK', 'Preload script executed', 'FAIL', error instanceof Error ? error.message : String(error)).catch(() => {});
}

// Type definitions for the renderer
export type ElectronAPI = typeof electronAPI;
