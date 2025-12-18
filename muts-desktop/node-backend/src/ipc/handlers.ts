/**
 * IPC Handlers
 * Handles communication between Electron UI and Node backend
 */

import { ipcMain } from 'electron';
import { Logger } from '../utils/logger';
import { RustCore } from '../core/rust-core';
import { SessionManager } from '../core/session-manager';
import { DatabaseManager } from '../core/database-manager';
import { SafetyManager } from '../core/safety-manager';

interface BackendContext {
  rustCore: RustCore;
  sessionManager: SessionManager;
  databaseManager: DatabaseManager;
  safetyManager: SafetyManager;
}

const logger = new Logger('IPCHandlers');

export function registerIpcHandlers(context: BackendContext): void {
  // Interface handlers
  registerInterfaceHandlers(context);
  
  // Session handlers
  registerSessionHandlers(context);
  
  // Diagnostic handlers
  registerDiagnosticHandlers(context);
  
  // Safety handlers
  registerSafetyHandlers(context);
  
  // Database handlers
  registerDatabaseHandlers(context);
  
  // Telemetry handlers
  registerTelemetryHandlers(context);
  
  // Flash handlers
  registerFlashHandlers(context);
  
  // Tuning handlers
  registerTuningHandlers(context);
  
  logger.info('All IPC handlers registered');
}

function registerInterfaceHandlers(context: BackendContext): void {
  const { rustCore } = context;

  // List available interfaces
  ipcMain.handle('interface:list', async () => {
    try {
      return await rustCore.listInterfaces();
    } catch (error) {
      logger.error('Failed to list interfaces:', error);
      throw error;
    }
  });

  // Connect to interface
  ipcMain.handle('interface:connect', async (event, interfaceId: string) => {
    try {
      const session = await context.sessionManager.connectInterface(interfaceId);
      return session;
    } catch (error) {
      logger.error('Failed to connect interface:', error);
      throw error;
    }
  });

  // Disconnect from interface
  ipcMain.handle('interface:disconnect', async () => {
    try {
      await context.sessionManager.disconnect();
    } catch (error) {
      logger.error('Failed to disconnect interface:', error);
      throw error;
    }
  });

  // Get connection status
  ipcMain.handle('interface:status', async () => {
    try {
      return await context.sessionManager.getConnectionStatus();
    } catch (error) {
      logger.error('Failed to get interface status:', error);
      throw error;
    }
  });
}

function registerSessionHandlers(context: BackendContext): void {
  const { sessionManager } = context;

  // Get all sessions
  ipcMain.handle('session:list', async () => {
    try {
      return sessionManager.getSessions();
    } catch (error) {
      logger.error('Failed to list sessions:', error);
      throw error;
    }
  });

  // Get specific session
  ipcMain.handle('session:get', async (event, sessionId: string) => {
    try {
      return sessionManager.getSession(sessionId);
    } catch (error) {
      logger.error('Failed to get session:', error);
      throw error;
    }
  });

  // Get current connection
  ipcMain.handle('session:connection', async () => {
    try {
      return sessionManager.getCurrentConnection();
    } catch (error) {
      logger.error('Failed to get current connection:', error);
      throw error;
    }
  });
}

function registerDiagnosticHandlers(context: BackendContext): void {
  const { sessionManager } = context;

  // Start diagnostic session
  ipcMain.handle('diagnostic:start', async (event, sessionType: string = 'default') => {
    try {
      return await sessionManager.startDiagnosticSession(sessionType);
    } catch (error) {
      logger.error('Failed to start diagnostic session:', error);
      throw error;
    }
  });

  // Send diagnostic request
  ipcMain.handle('diagnostic:request', async (event, serviceId: number, data?: Buffer) => {
    try {
      return await sessionManager.sendDiagnosticRequest(serviceId, data);
    } catch (error) {
      logger.error('Failed to send diagnostic request:', error);
      throw error;
    }
  });

  // Read DTCs
  ipcMain.handle('diagnostic:readDTCs', async () => {
    try {
      return await context.databaseManager.getDTCs();
    } catch (error) {
      logger.error('Failed to read DTCs:', error);
      throw error;
    }
  });

  // Clear DTCs
  ipcMain.handle('diagnostic:clearDTCs', async (event, sessionId: string) => {
    try {
      await context.databaseManager.clearDTCs(sessionId);
    } catch (error) {
      logger.error('Failed to clear DTCs:', error);
      throw error;
    }
  });
}

function registerSafetyHandlers(context: BackendContext): void {
  const { safetyManager } = context;

  // Arm safety system
  ipcMain.handle('safety:arm', async (event, level: string) => {
    try {
      await safetyManager.arm(level as any);
      return await safetyManager.getState();
    } catch (error) {
      logger.error('Failed to arm safety system:', error);
      throw error;
    }
  });

  // Disarm safety system
  ipcMain.handle('safety:disarm', async () => {
    try {
      await safetyManager.disarm();
      return await safetyManager.getState();
    } catch (error) {
      logger.error('Failed to disarm safety system:', error);
      throw error;
    }
  });

  // Get safety state
  ipcMain.handle('safety:state', async () => {
    try {
      return await safetyManager.getState();
    } catch (error) {
      logger.error('Failed to get safety state:', error);
      throw error;
    }
  });

  // Check parameters
  ipcMain.handle('safety:check', async (event, parameters: Record<string, number>) => {
    try {
      return await safetyManager.checkParameters(parameters);
    } catch (error) {
      logger.error('Failed to check parameters:', error);
      throw error;
    }
  });

  // Create safety snapshot
  ipcMain.handle('safety:snapshot', async (event, parameters: Record<string, number>) => {
    try {
      return await safetyManager.createSnapshot(parameters);
    } catch (error) {
      logger.error('Failed to create safety snapshot:', error);
      throw error;
    }
  });
}

function registerDatabaseHandlers(context: BackendContext): void {
  const { databaseManager } = context;

  // Vehicle operations
  ipcMain.handle('db:vehicle:create', async (event, vehicle: any) => {
    try {
      return await databaseManager.createOrUpdateVehicle(vehicle);
    } catch (error) {
      logger.error('Failed to create/update vehicle:', error);
      throw error;
    }
  });

  ipcMain.handle('db:vehicle:get', async (event, vin: string) => {
    try {
      return await databaseManager.getVehicle(vin);
    } catch (error) {
      logger.error('Failed to get vehicle:', error);
      throw error;
    }
  });

  ipcMain.handle('db:vehicle:list', async () => {
    try {
      return await databaseManager.getAllVehicles();
    } catch (error) {
      logger.error('Failed to list vehicles:', error);
      throw error;
    }
  });

  // Tuning profiles
  ipcMain.handle('db:profile:create', async (event, profile: any) => {
    try {
      return await databaseManager.createProfile(profile);
    } catch (error) {
      logger.error('Failed to create tuning profile:', error);
      throw error;
    }
  });

  ipcMain.handle('db:profile:list', async (event, vehicleId?: string) => {
    try {
      return await databaseManager.getProfiles(vehicleId);
    } catch (error) {
      logger.error('Failed to list tuning profiles:', error);
      throw error;
    }
  });
}

function registerTelemetryHandlers(context: BackendContext): void {
  const { sessionManager, databaseManager } = context;

  // Get telemetry
  ipcMain.handle('telemetry:get', async (event, sessionId: string, options?: any) => {
    try {
      return await databaseManager.getTelemetry(
        sessionId,
        options?.startTime,
        options?.endTime,
        options?.limit
      );
    } catch (error) {
      logger.error('Failed to get telemetry:', error);
      throw error;
    }
  });

  // Export telemetry
  ipcMain.handle('telemetry:export', async (event, sessionId: string, format: string) => {
    try {
      const buffer = await databaseManager.exportTelemetry(sessionId, format as any);
      return buffer;
    } catch (error) {
      logger.error('Failed to export telemetry:', error);
      throw error;
    }
  });

  // Subscribe to telemetry stream
  ipcMain.on('telemetry:subscribe', (event) => {
    const unsubscribe = sessionManager.on('telemetry', (data) => {
      event.sender.send('telemetry:data', data);
    });

    // Clean up on window close
    event.sender.on('destroyed', () => {
      unsubscribe();
    });
  });
}

function registerFlashHandlers(context: BackendContext): void {
  const { sessionManager, databaseManager, rustCore } = context;

  // Validate ROM
  ipcMain.handle('flash:validate', async (event, romData: Buffer) => {
    try {
      return await rustCore.validateRom(romData);
    } catch (error) {
      logger.error('Failed to validate ROM:', error);
      throw error;
    }
  });

  // Verify checksum
  ipcMain.handle('flash:checksum', async (event, romData: Buffer) => {
    try {
      return await rustCore.verifyChecksum(romData);
    } catch (error) {
      logger.error('Failed to verify checksum:', error);
      throw error;
    }
  });

  // Prepare flash
  ipcMain.handle('flash:prepare', async (event, romData: Buffer, options: any) => {
    try {
      const session = await sessionManager.startFlashSession(romData, options);
      return session;
    } catch (error) {
      logger.error('Failed to prepare flash:', error);
      throw error;
    }
  });

  // Execute flash
  ipcMain.handle('flash:execute', async (event, sessionId: string) => {
    try {
      await sessionManager.executeFlash(sessionId);
    } catch (error) {
      logger.error('Failed to execute flash:', error);
      throw error;
    }
  });

  // Abort flash
  ipcMain.handle('flash:abort', async (event, sessionId: string) => {
    try {
      await sessionManager.abortFlash(sessionId);
    } catch (error) {
      logger.error('Failed to abort flash:', error);
      throw error;
    }
  });
}

function registerTuningHandlers(context: BackendContext): void {
  const { sessionManager, safetyManager } = context;

  // Create tuning session
  ipcMain.handle('tuning:session:create', async (event, changesetId: string) => {
    try {
      return await sessionManager.createTuningSession(changesetId);
    } catch (error) {
      logger.error('Failed to create tuning session:', error);
      throw error;
    }
  });

  // Apply live changes
  ipcMain.handle('tuning:apply', async (event, sessionId: string, changes: any[]) => {
    try {
      // Check safety first
      const violations = await safetyManager.checkParameters({});
      if (violations.length > 0) {
        throw new Error(`Safety violations prevent applying changes: ${violations.map(v => v.parameter).join(', ')}`);
      }

      return await sessionManager.applyLiveChanges(sessionId, changes);
    } catch (error) {
      logger.error('Failed to apply live changes:', error);
      throw error;
    }
  });

  // Revert live changes
  ipcMain.handle('tuning:revert', async (event, sessionId: string) => {
    try {
      return await sessionManager.revertLiveChanges(sessionId);
    } catch (error) {
      logger.error('Failed to revert live changes:', error);
      throw error;
    }
  });
}
