/**
 * MUTS Desktop Backend
 * Node.js backend for ECU tuning and diagnostics
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';
import { Logger } from './utils/logger';
import { RustCore } from './core/rust-core';
import { SessionManager } from './core/session-manager';
import { DatabaseManager } from './core/database-manager';
import { SafetyManager } from './core/safety-manager';
import { registerIpcHandlers } from './ipc/handlers';

class MutsBackend {
  private logger: Logger;
  private rustCore: RustCore;
  private sessionManager: SessionManager;
  private databaseManager: DatabaseManager;
  private safetyManager: SafetyManager;

  constructor() {
    this.logger = new Logger('MutsBackend');
    this.rustCore = new RustCore();
    this.sessionManager = new SessionManager(this.rustCore);
    this.databaseManager = new DatabaseManager();
    this.safetyManager = new SafetyManager();
  }

  async initialize(): Promise<void> {
    try {
      this.logger.info('Initializing MUTS Backend...');

      // Initialize Rust core
      await this.rustCore.initialize();
      this.logger.info('Rust core initialized');

      // Initialize database
      await this.databaseManager.initialize();
      this.logger.info('Database initialized');

      // Initialize safety manager
      await this.safetyManager.initialize();
      this.logger.info('Safety manager initialized');

      // Register IPC handlers
      registerIpcHandlers({
        rustCore: this.rustCore,
        sessionManager: this.sessionManager,
        databaseManager: this.databaseManager,
        safetyManager: this.safetyManager,
      });

      this.logger.info('MUTS Backend initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize backend:', error);
      throw error;
    }
  }

  async shutdown(): Promise<void> {
    try {
      this.logger.info('Shutting down MUTS Backend...');

      // Disconnect from interface if connected
      if (await this.rustCore.isConnected()) {
        await this.rustCore.disconnect();
      }

      // Close database
      await this.databaseManager.close();

      this.logger.info('MUTS Backend shut down');
    } catch (error) {
      this.logger.error('Error during shutdown:', error);
    }
  }
}

// Backend instance
const backend = new MutsBackend();

// Initialize when ready
app.whenReady().then(async () => {
  try {
    await backend.initialize();
  } catch (error) {
    console.error('Failed to start backend:', error);
    app.quit();
  }
});

// Handle shutdown
app.on('before-quit', async () => {
  await backend.shutdown();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  backend.shutdown().then(() => process.exit(1));
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});

export default backend;
