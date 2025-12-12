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
        electronAPI.sendCommand('connection:connect', { interfaceId });
      } catch (error) {
        console.error('Failed to connect interface:', error);
      }
    },
    disconnect: () => {
      try {
        electronAPI.sendCommand('connection:disconnect');
      } catch (error) {
        console.error('Failed to disconnect:', error);
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
        return { armed: false, mode: 'unknown' };
      }
    },
    arm: () => {
      try {
        electronAPI.sendCommand('safety:arm');
      } catch (error) {
        console.error('Failed to arm safety:', error);
      }
    },
    disarm: () => {
      try {
        electronAPI.sendCommand('safety:disarm');
      } catch (error) {
        console.error('Failed to disarm safety:', error);
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
    export: (sessionId: string, format: string) => {
      try {
        return ipcRenderer.invoke('telemetry:export', sessionId, format);
      } catch (error) {
        console.error('Failed to export telemetry:', error);
        return null;
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
        return { valid: false, errors: ['Validation failed'] };
      }
    },
    checksum: (romData: ArrayBuffer) => {
      try {
        return ipcRenderer.invoke('flash:checksum', romData);
      } catch (error) {
        console.error('Failed to calculate checksum:', error);
        return { checksum: '00000000', valid: false };
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
};

// Expose the API to the renderer process
try {
  contextBridge.exposeInMainWorld('electronAPI', electronAPI);
} catch (error) {
  console.error('Failed to expose electronAPI:', error);
}

// Type definitions for the renderer
export type ElectronAPI = typeof electronAPI;
