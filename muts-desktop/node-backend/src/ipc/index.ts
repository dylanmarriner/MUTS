/**
 * IPC Handler Registration
 * Exports all IPC handlers for registration in the main process
 */

import { ipcMain } from 'electron';
import * as handlers from './handlers';
import * as debugHandlers from './debug-handlers';
import * as subsystemHandlers from './subsystem-handlers';
import * as simulationHandlers from './simulation-handlers';
import * as dynoHandlers from './dyno-handlers';

/**
 * Register all IPC handlers with backend context
 */
export function registerAllHandlers(context: any): void {
  // Register core handlers with context
  handlers.registerIpcHandlers(context);

  // Register debug handlers (they don't need context)
  debugHandlers.registerDebugHandlers();

  // Register subsystem handlers
  subsystemHandlers.registerSubsystemHandlers();

  // Register simulation handlers
  simulationHandlers.registerSimulationHandlers(context);

  // Register dyno handlers
  dynoHandlers.registerDynoHandlers(context);
}

// Export the registerAllHandlers from handlers for direct use
export { registerIpcHandlers as registerCoreHandlers } from './handlers';
export { registerDebugHandlers } from './debug-handlers';
export { registerSubsystemHandlers } from './subsystem-handlers';
export { registerSimulationHandlers } from './simulation-handlers';
export { registerDynoHandlers } from './dyno-handlers';
