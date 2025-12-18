/**
 * Electron Main Process
 * Entry point for the MUTS desktop application
 */

import { app, BrowserWindow, ipcMain, Menu, shell, dialog } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import { logger } from './utils/logger';
import { createWindow } from './window';
import { initializeWebSocket } from './services/websocket';
import { getHealthProbe, CHECKPOINTS } from './utils/healthProbe';

let mainWindow: BrowserWindow | null = null;
const healthProbe = getHealthProbe();
// Check if running in CI/headless mode (module-level for use in callbacks)
const isCI = process.env.CI === 'true' || process.env.HEADLESS === 'true';

function createMainWindow(): void {
  // #region agent log
  const DEBUG_LOG_PATH = path.resolve(__dirname, '../../../.cursor/debug.log');
  function writeDebugLog(location: string, message: string, data: any, hypothesisId: string) {
    try {
      const logDir = path.dirname(DEBUG_LOG_PATH);
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      const logEntry = JSON.stringify({
        location,
        message,
        data,
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId
      }) + '\n';
      fs.appendFileSync(DEBUG_LOG_PATH, logEntry, 'utf-8');
    } catch (err) {
      // Ignore log write errors
    }
  }
  writeDebugLog('main.ts:19', 'createMainWindow entry', { __dirname, isCI }, 'C');
  // #endregion
  
  healthProbe.checkpoint(CHECKPOINTS.MAIN_STARTED, 'Main process started', 'PASS');
  
  // Create the browser window
  const preloadPath = path.join(__dirname, 'preload.js');
  
  // #region agent log
  writeDebugLog('main.ts:27', 'preload path check', { preloadPath, exists: fs.existsSync(preloadPath) }, 'C');
  // #endregion
  
  // Verify preload file exists
  if (!fs.existsSync(preloadPath)) {
    healthProbe.checkpoint(CHECKPOINTS.PRELOAD_OK, 'Preload script exists', 'FAIL', `Preload file not found: ${preloadPath}`);
    // #region agent log
    writeDebugLog('main.ts:30', 'preload file not found', { preloadPath }, 'C');
    // #endregion
  }
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    titleBarStyle: 'default',
    show: !isCI, // Don't show in CI/headless mode
  });

  // Load the app - always use production file loading
  const htmlPath = path.join(__dirname, 'renderer/src/index.html');
  
  // #region agent log
  writeDebugLog('main.ts:47', 'HTML path check', { htmlPath, exists: fs.existsSync(htmlPath) }, 'C');
  // #endregion
  
  // Verify HTML file exists
  if (!fs.existsSync(htmlPath)) {
    healthProbe.checkpoint(CHECKPOINTS.RENDERER_LOADED, 'Renderer HTML exists', 'FAIL', `HTML file not found: ${htmlPath}`);
    // #region agent log
    writeDebugLog('main.ts:52', 'HTML file not found', { htmlPath }, 'C');
    // #endregion
  }
  
  console.log('Loading app from:', htmlPath);
  // #region agent log
  writeDebugLog('main.ts:92', 'before loadFile call', { htmlPath, timestamp: Date.now() }, 'C');
  // #endregion
  
  const loadPromise = mainWindow.loadFile(htmlPath);
  // #region agent log
  writeDebugLog('main.ts:95', 'loadFile promise created', { timestamp: Date.now() }, 'C');
  // #endregion
  
  // Add timeout to detect hanging loadFile
  const loadTimeout = setTimeout(() => {
    // #region agent log
    writeDebugLog('main.ts:99', 'loadFile timeout warning', { htmlPath, elapsed: Date.now() - (Date.now() - 5000) }, 'C');
    // #endregion
    console.warn('loadFile is taking longer than expected...');
  }, 5000);
  
  loadPromise
    .then(() => {
      clearTimeout(loadTimeout);
      // #region agent log
      writeDebugLog('main.ts:105', 'loadFile success', { htmlPath, timestamp: Date.now() }, 'C');
      // #endregion
      healthProbe.checkpoint(CHECKPOINTS.RENDERER_LOADED, 'Renderer HTML loaded', 'PASS');
    })
    .catch(err => {
      clearTimeout(loadTimeout);
      // #region agent log
      writeDebugLog('main.ts:111', 'loadFile failed', { htmlPath, error: err.message, stack: err.stack, timestamp: Date.now() }, 'C');
      // #endregion
      console.error('Failed to load app:', err);
      healthProbe.checkpoint(CHECKPOINTS.RENDERER_LOADED, 'Renderer HTML loaded', 'FAIL', err.message);
      // Show error screen
      if (mainWindow) {
        const errorHTML = generateErrorUI('Failed to Load Application', 'Could not load the renderer. Please restart the application.', err.message);
        mainWindow.loadURL(`data:text/html,${encodeURIComponent(errorHTML)}`);
      }
    }); 
  // Only open DevTools in non-CI mode
  if (!isCI && !app.isPackaged) {
  mainWindow.webContents.openDevTools();
  }

  // Filter out expected console errors (backend not available in standalone mode)
  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    if (level === 2 || level === 3) { // error or warning
      // Filter out expected errors (backend not available in standalone mode)
      const messageStr = String(message);
      const isExpectedError = 
        messageStr.includes('Failed to load technicians') ||
        messageStr.includes('Failed to fetch') && messageStr.includes('localhost:3000') ||
        messageStr.includes('TypeError: Failed to fetch') && messageStr.includes('technicians');
      
      // Silently ignore expected errors, log others
      if (!isExpectedError) {
        console.error(`[Renderer ${level === 2 ? 'Error' : 'Warning'}]`, message);
      }
    }
  });

  // Show window when ready (unless in CI mode)
  mainWindow.once('ready-to-show', () => {
    // #region agent log
    writeDebugLog('main.ts:138', 'ready-to-show event', { timestamp: Date.now() }, 'C');
    // #endregion
    console.log('Window ready to show');
    if (!isCI) {
    mainWindow?.show();
      // #region agent log
      writeDebugLog('main.ts:142', 'window.show() called', { timestamp: Date.now() }, 'C');
      // #endregion
    }
    healthProbe.checkpoint(CHECKPOINTS.UI_VISIBLE, 'Window ready (visible or headless)', 'PASS');
    
    if (!isCI && !app.isPackaged) {
      mainWindow?.webContents.openDevTools();
    }
  });
  
  // Add did-finish-load event listener
  mainWindow.webContents.once('did-finish-load', () => {
    // #region agent log
    writeDebugLog('main.ts:152', 'did-finish-load event', { url: mainWindow?.webContents.getURL(), timestamp: Date.now() }, 'C');
    // #endregion
  });
  
  // Add did-fail-load event listener for more detailed error info
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    // Ignore navigation failures for client-side routes (React Router handles these)
    // Only log actual file loading failures
    if (errorCode === -6 && validatedURL && validatedURL.startsWith('file:///') && !validatedURL.includes('index.html')) {
      // This is a React Router navigation - ignore it
      return;
    }
    // #region agent log
    writeDebugLog('main.ts:158', 'did-fail-load event', { errorCode, errorDescription, validatedURL, timestamp: Date.now() }, 'C');
    // #endregion
    console.error('Failed to load:', { errorCode, errorDescription, validatedURL });
  });

  // Fallback: show window after 3 seconds even if not ready
  setTimeout(() => {
    if (mainWindow && !mainWindow.isVisible()) {
      console.log('Window not ready after 3 seconds, showing anyway');
      mainWindow.show();
    }
  }, 3000);

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function createMenu(): Menu {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open ROM',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            // Send event to renderer
            mainWindow?.webContents.send('menu:open-rom');
          },
        },
        {
          label: 'Quit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { label: 'Undo', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: 'Redo', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: 'Cut', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: 'Copy', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: 'Paste', accelerator: 'CmdOrCtrl+V', role: 'paste' },
      ],
    },
    {
      label: 'Tools',
      submenu: [
        {
          label: 'Connect Interface',
          accelerator: 'CmdOrCtrl+K',
          click: () => {
            mainWindow?.webContents.send('menu:connect');
          },
        },
        {
          label: 'Safety Arm',
          accelerator: 'CmdOrCtrl+Shift+A',
          click: () => {
            mainWindow?.webContents.send('menu:arm-safety');
          },
        },
        { type: 'separator' },
        {
          label: 'Developer Tools',
          accelerator: 'F12',
          click: () => {
            mainWindow?.webContents.toggleDevTools();
          },
        },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            // Show about dialog
          },
        },
      ],
    },
  ];

  return Menu.buildFromTemplate(template);
}

// App event handlers
app.on('window-all-closed', () => {
  // On macOS, keep app running
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  logger.info('Application shutting down...');
});

// Security: Prevent new window creation
app.on('web-contents-created', (_, contents) => {
  contents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
});

// Handle protocol for file associations
app.setAsDefaultProtocolClient('muts');

// Handle deep links
app.on('open-url', (event, url) => {
  event.preventDefault();
  logger.info('Received deep link:', url);
  // Handle deep link (e.g., muts://open?file=path/to/rom)
});

// IPC handler for debug logging from renderer (kept for compatibility, but no-op)
ipcMain.handle('debug:log', (_, location: string, message: string, data: any, hypothesisId: string) => {
  // Debug logging disabled - handler kept for compatibility
});

// IPC handler for health checkpoints from renderer
ipcMain.handle('health:checkpoint', (_, id: string, name: string, status: 'PASS' | 'FAIL' | 'DEGRADED', error?: string, metadata?: Record<string, any>) => {
  healthProbe.checkpoint(id, name, status, error, metadata);
});

// IPC handler for health report request
ipcMain.handle('health:report', () => {
  return healthProbe.getStatus();
});

// IPC handlers for main process
ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

// Mark IPC as ready after handlers are registered
healthProbe.checkpoint(CHECKPOINTS.IPC_READY, 'IPC handlers registered', 'PASS');

ipcMain.handle('app:getPath', (_, name: string) => {
  return app.getPath(name as any);
});

// Configuration handlers
ipcMain.handle('config:load', async () => {
  const { configStore } = await import('./config/store');
  return configStore.load();
});

ipcMain.handle('config:get', async () => {
  const { configStore } = await import('./config/store');
  return configStore.get();
});

ipcMain.handle('config:setOperatorMode', async (_, mode: string) => {
  const { configStore } = await import('./config/store');
  return configStore.setOperatorMode(mode as any);
});

ipcMain.handle('config:setTechnician', async (_, technicianId: string) => {
  const { configStore } = await import('./config/store');
  return configStore.setTechnician(technicianId);
});

ipcMain.handle('config:clearTechnician', async () => {
  const { configStore } = await import('./config/store');
  return configStore.clearTechnician();
});

ipcMain.handle('config:skipModeSelection', async (_, skip: boolean) => {
  const { configStore } = await import('./config/store');
  return configStore.skipModeSelection(skip);
});

ipcMain.handle('system:getOperatorMode', async () => {
  try {
    // Return default mode for now
    return 'dev';
  } catch (error) {
    console.error('Failed to get operator mode:', error);
    return 'dev';
  }
});

// Interface handlers
ipcMain.handle('interface:list', async () => {
  try {
    // Return empty array for now - no interfaces connected
    return [];
  } catch (error) {
    console.error('Failed to list interfaces:', error);
    return [];
  }
});

ipcMain.handle('interface:getStatus', async () => {
  try {
    // Return disconnected status for now
    return { connected: false, type: null, port: null };
  } catch (error) {
    console.error('Failed to get interface status:', error);
    return { connected: false, type: null, port: null };
  }
});

ipcMain.handle('interface:connect', async (_, interfaceId: string) => {
  // #region agent log
  const DEBUG_LOG_PATH = path.resolve(__dirname, '../../../.cursor/debug.log');
  function writeDebugLog(location: string, message: string, data: any, hypothesisId: string) {
    try {
      const logDir = path.dirname(DEBUG_LOG_PATH);
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      const logEntry = JSON.stringify({
        location,
        message,
        data,
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId
      }) + '\n';
      fs.appendFileSync(DEBUG_LOG_PATH, logEntry, 'utf-8');
    } catch (err) {
      // Ignore log write errors
    }
  }
  writeDebugLog('main.ts:318', 'interface:connect entry', { interfaceId }, 'D');
  // #endregion
  
  try {
    // TODO: Implement actual interface connection
    // For now, return a mock session
    const sessionId = `session-${Date.now()}`;
    logger.info(`Connecting to interface: ${interfaceId}`);
    // #region agent log
    writeDebugLog('main.ts:325', 'interface:connect success', { sessionId, interfaceId }, 'D');
    // #endregion
    return { sessionId, interfaceId, connected: true };
  } catch (error: any) {
    // #region agent log
    writeDebugLog('main.ts:329', 'interface:connect error', { interfaceId, error: error.message, stack: error.stack }, 'D');
    // #endregion
    console.error('Failed to connect interface:', error);
    throw error;
  }
});

ipcMain.handle('interface:disconnect', async () => {
  try {
    // TODO: Implement actual interface disconnection
    logger.info('Disconnecting interface');
    return { success: true };
  } catch (error) {
    console.error('Failed to disconnect interface:', error);
    throw error;
  }
});

// Flash handlers
ipcMain.handle('flash:validate', async (_, romData: ArrayBuffer) => {
  try {
    // Return basic validation for now
    return { valid: true, errors: [], ecuType: 'Unknown', calibrationId: 'Unknown' };
  } catch (error) {
    console.error('Failed to validate ROM:', error);
    return { valid: false, errors: ['Validation failed'] };
  }
});

ipcMain.handle('flash:checksum', async (_, romData: ArrayBuffer) => {
  try {
    // Calculate simple checksum
    const buffer = Buffer.from(romData);
    let checksum = 0;
    for (let i = 0; i < buffer.length; i++) {
      checksum = (checksum + buffer[i]) & 0xFFFFFFFF;
    }
    return { checksum: checksum.toString(16).padStart(8, '0'), valid: true, calculated: checksum };
  } catch (error) {
    console.error('Failed to calculate checksum:', error);
    return { checksum: '00000000', valid: false };
  }
});

ipcMain.handle('flash:prepare', async (_, romData: Buffer, options: any) => {
  try {
    // TODO: Implement actual flash preparation
    const jobId = `flash-job-${Date.now()}`;
    const blocksToWrite = Math.ceil(romData.length / 1024); // Assume 1KB blocks
    const estimatedTimeSec = blocksToWrite * 0.1; // 0.1 seconds per block
    
    logger.info(`Preparing flash job: ${jobId}, blocks: ${blocksToWrite}`);
    return { jobId, blocksToWrite, estimatedTimeSec };
  } catch (error) {
    console.error('Failed to prepare flash:', error);
    throw error;
  }
});

ipcMain.handle('flash:execute', async (_, jobId: string) => {
  try {
    // TODO: Implement actual flash execution
    logger.info(`Executing flash job: ${jobId}`);
    return { success: true, jobId };
  } catch (error) {
    console.error('Failed to execute flash:', error);
    throw error;
  }
});

ipcMain.handle('flash:abort', async (_, jobId: string) => {
  try {
    // TODO: Implement actual flash abortion
    logger.info(`Aborting flash job: ${jobId}`);
    return { success: true, jobId };
  } catch (error) {
    console.error('Failed to abort flash:', error);
    throw error;
  }
});

// Tuning handlers
ipcMain.handle('tuning:createSession', async (_, changesetId: string) => {
  try {
    // Return dummy session ID for now
    return { sessionId: `session-${Date.now()}`, changesetId };
  } catch (error) {
    console.error('Failed to create tuning session:', error);
    return null;
  }
});

ipcMain.handle('tuning:apply', async (_, sessionId: string, changes: any) => {
  try {
    // TODO: Implement actual tuning apply
    logger.info(`Applying tuning changes for session: ${sessionId}`);
    return { success: true, sessionId, changesApplied: Object.keys(changes).length };
  } catch (error) {
    console.error('Failed to apply tuning:', error);
    throw error;
  }
});

// Diagnostic handlers
ipcMain.handle('diagnostic:start', async () => {
  try {
    // TODO: Implement actual diagnostic session start
    const sessionId = `diag-${Date.now()}`;
    logger.info(`Starting diagnostic session: ${sessionId}`);
    return sessionId;
  } catch (error) {
    console.error('Failed to start diagnostic:', error);
    throw error;
  }
});

ipcMain.handle('diagnostic:readDTCs', async () => {
  try {
    // TODO: Implement actual DTC reading
    // Return empty array for now (no DTCs)
    return [];
  } catch (error) {
    console.error('Failed to read DTCs:', error);
    return [];
  }
});

ipcMain.handle('diagnostic:clearDTCs', async (_, sessionId: string) => {
  try {
    // TODO: Implement actual DTC clearing
    logger.info(`Clearing DTCs for session: ${sessionId}`);
    return { success: true, sessionId };
  } catch (error) {
    console.error('Failed to clear DTCs:', error);
    throw error;
  }
});

// Database handlers (basic stubs)
ipcMain.handle('db:vehicle:create', async (_, vehicle: any) => {
  try {
    console.log('Creating vehicle:', vehicle);
    return { id: Date.now().toString(), ...vehicle };
  } catch (error) {
    console.error('Failed to create vehicle:', error);
    return null;
  }
});

ipcMain.handle('db:vehicle:get', async (_, vin: string) => {
  try {
    console.log('Getting vehicle:', vin);
    return null; // No vehicles in DB yet
  } catch (error) {
    console.error('Failed to get vehicle:', error);
    return null;
  }
});

ipcMain.handle('db:vehicle:list', async () => {
  try {
    return []; // No vehicles in DB yet
  } catch (error) {
    console.error('Failed to list vehicles:', error);
    return [];
  }
});

ipcMain.handle('db:profile:create', async (_, profile: any) => {
  try {
    console.log('Creating profile:', profile);
    return { id: Date.now().toString(), ...profile };
  } catch (error) {
    console.error('Failed to create profile:', error);
    return null;
  }
});

ipcMain.handle('db:profile:list', async (_, vehicleId?: string) => {
  try {
    return []; // No profiles in DB yet
  } catch (error) {
    console.error('Failed to list profiles:', error);
    return [];
  }
});

// Telemetry handlers
ipcMain.handle('telemetry:export', async (_, sessionId: string, format: string) => {
  try {
    console.log(`Exporting telemetry for session ${sessionId} as ${format}`);
    // TODO: Implement actual telemetry export
    // For now, return empty CSV buffer
    const csvHeader = 'timestamp,engine_rpm,boost_pressure,vehicle_speed\n';
    const csvData = csvHeader; // Empty data for now
    return Buffer.from(csvData, 'utf-8');
  } catch (error) {
    console.error('Failed to export telemetry:', error);
    throw error;
  }
});

// Metrics handler
ipcMain.handle('metrics:get', async () => {
  try {
    return { cpu: 0, memory: 0, uptime: 0 };
  } catch (error) {
    console.error('Failed to get metrics:', error);
    return {};
  }
});

// Safety handlers
ipcMain.handle('safety:getStatus', async () => {
  try {
    // Return default safety status
    return { armed: false, level: 'ReadOnly', violations: [] };
  } catch (error) {
    console.error('Failed to get safety status:', error);
    return { armed: false, level: 'ReadOnly', violations: [] };
  }
});

ipcMain.handle('safety:arm', async (_, level: string) => {
  try {
    // TODO: Implement actual safety arming
    logger.info(`Arming safety system: ${level}`);
    return { success: true, level, armed: true };
  } catch (error) {
    console.error('Failed to arm safety:', error);
    throw error;
  }
});

ipcMain.handle('safety:disarm', async () => {
  try {
    // TODO: Implement actual safety disarming
    logger.info('Disarming safety system');
    return { success: true, armed: false, level: 'ReadOnly' };
  } catch (error) {
    console.error('Failed to disarm safety:', error);
    throw error;
  }
});

ipcMain.handle('safety:createSnapshot', async (_, telemetry: any) => {
  try {
    // TODO: Implement actual snapshot creation
    const snapshotId = `snapshot-${Date.now()}`;
    logger.info(`Creating safety snapshot: ${snapshotId}`);
    return { snapshotId, timestamp: Date.now(), telemetry };
  } catch (error) {
    console.error('Failed to create snapshot:', error);
    throw error;
  }
});

// Error handling
(process as NodeJS.EventEmitter).on('uncaughtException', (error: Error) => {
  logger.error('Uncaught exception:', error);
  console.error('Uncaught exception:', error);
});

(process as NodeJS.EventEmitter).on('unhandledRejection', (reason: any, promise: Promise<any>) => {
  logger.error('Unhandled rejection at:', promise, 'reason:', reason);
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});

// Handle app ready
app.whenReady().then(() => {
  console.log('App is ready, creating main window...');
  createMainWindow();
  const menu = createMenu();
  if (menu) {
    Menu.setApplicationMenu(menu);
  }
  initializeWebSocket();
  
  // Check backend availability (non-blocking)
  checkBackendHealth();
  
  // Generate health report after 5 seconds
  setTimeout(() => {
    const report = healthProbe.generateReport();
    console.log('Health Report:', JSON.stringify(report, null, 2));
    
    // In CI mode, exit after health check
    if (isCI) {
      const critical = ['MAIN_STARTED', 'PRELOAD_OK', 'RENDERER_LOADED', 'IPC_READY', 'UI_VISIBLE'];
      const allCriticalPassed = critical.every(id => {
        const checkpoint = report.checkpoints.find(c => c.id === id);
        return checkpoint && checkpoint.status === 'PASS';
      });
      
      if (report.overall === 'FAILED' || !allCriticalPassed) {
        console.error('❌ Health check failed - exiting with error code');
        if (mainWindow) {
          mainWindow.close();
        }
        process.exit(1);
      } else {
        console.log('✓ Health check passed - exiting');
        if (mainWindow) {
          mainWindow.close();
        }
        process.exit(0);
      }
    }
  }, 5000);
}).catch((error) => {
  console.error('Failed to initialize app:', error);
  healthProbe.checkpoint(CHECKPOINTS.MAIN_STARTED, 'Main process started', 'FAIL', error.message);
  healthProbe.generateReport();
  app.quit();
  process.exit(1);
});

// Check backend health with retry mechanism (non-blocking, graceful failure)
async function checkBackendHealth(): Promise<void> {
  // #region agent log
  const DEBUG_LOG_PATH = path.resolve(__dirname, '../../../.cursor/debug.log');
  function writeDebugLog(location: string, message: string, data: any, hypothesisId: string) {
    try {
      const logDir = path.dirname(DEBUG_LOG_PATH);
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      const logEntry = JSON.stringify({
        location,
        message,
        data,
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId
      }) + '\n';
      fs.appendFileSync(DEBUG_LOG_PATH, logEntry, 'utf-8');
    } catch (err) {
      // Ignore log write errors
    }
  }
  writeDebugLog('main.ts:717', 'checkBackendHealth entry', { timestamp: Date.now() }, 'A');
  // #endregion
  
  const maxRetries = 3;
  const retryDelay = 2000; // 2 seconds between retries
  
  const attemptConnection = (attempt: number): Promise<void> => {
    return new Promise((resolve) => {
      // #region agent log
      writeDebugLog('main.ts:730', 'backend connection attempt', { attempt, maxRetries, url: 'http://localhost:3000/health' }, 'A');
      // #endregion
      
      const http = require('http');
      const request = http.get('http://localhost:3000/health', { timeout: 2000 }, (res: any) => {
        // #region agent log
        writeDebugLog('main.ts:735', 'http.get response', { statusCode: res.statusCode, attempt }, 'A');
        // #endregion
        
        if (res.statusCode === 200) {
          healthProbe.checkpoint(CHECKPOINTS.BACKEND_READY, 'Backend available', 'PASS');
          // #region agent log
          writeDebugLog('main.ts:739', 'backend health PASS', { attempt }, 'A');
          // #endregion
          resolve();
        } else {
          if (attempt < maxRetries) {
            // #region agent log
            writeDebugLog('main.ts:744', 'backend retry scheduled', { attempt, nextAttempt: attempt + 1, delay: retryDelay }, 'A');
            // #endregion
            setTimeout(() => attemptConnection(attempt + 1).then(resolve), retryDelay);
          } else {
            healthProbe.checkpoint(CHECKPOINTS.BACKEND_READY, 'Backend available', 'DEGRADED', 'Backend not running (standalone mode)');
            // #region agent log
            writeDebugLog('main.ts:750', 'backend health DEGRADED - max retries', { attempt, statusCode: res.statusCode }, 'A');
            // #endregion
            resolve();
          }
        }
      });
      
      request.on('error', (err: any) => {
        // #region agent log
        writeDebugLog('main.ts:757', 'http.get error', { error: err.message, code: err.code, attempt }, 'B');
        // #endregion
        
        if (attempt < maxRetries) {
          // #region agent log
          writeDebugLog('main.ts:761', 'backend retry scheduled after error', { attempt, nextAttempt: attempt + 1, delay: retryDelay }, 'B');
          // #endregion
          setTimeout(() => attemptConnection(attempt + 1).then(resolve), retryDelay);
        } else {
          healthProbe.checkpoint(CHECKPOINTS.BACKEND_READY, 'Backend available', 'DEGRADED', 'Backend not available (standalone mode)');
          // #region agent log
          writeDebugLog('main.ts:767', 'backend health DEGRADED - max retries after error', { attempt }, 'B');
          // #endregion
          resolve();
        }
      });
      
      request.on('timeout', () => {
        // #region agent log
        writeDebugLog('main.ts:774', 'http.get timeout', { attempt }, 'B');
        // #endregion
        request.destroy();
        
        if (attempt < maxRetries) {
          // #region agent log
          writeDebugLog('main.ts:779', 'backend retry scheduled after timeout', { attempt, nextAttempt: attempt + 1, delay: retryDelay }, 'B');
          // #endregion
          setTimeout(() => attemptConnection(attempt + 1).then(resolve), retryDelay);
        } else {
          healthProbe.checkpoint(CHECKPOINTS.BACKEND_READY, 'Backend available', 'DEGRADED', 'Backend not available (standalone mode)');
          // #region agent log
          writeDebugLog('main.ts:785', 'backend health DEGRADED - max retries after timeout', { attempt }, 'B');
          // #endregion
          resolve();
        }
      });
    });
  };
  
  // Start first attempt
  attemptConnection(1).catch((error: any) => {
    // #region agent log
    writeDebugLog('main.ts:793', 'checkBackendHealth catch', { error: error.message, stack: error.stack }, 'B');
    // #endregion
    healthProbe.checkpoint(CHECKPOINTS.BACKEND_READY, 'Backend available', 'DEGRADED', 'Backend not available (standalone mode)');
  });
}

// Generate error UI HTML
function generateErrorUI(title: string, message: string, details?: string): string {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
      color: white;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .error-container {
      text-align: center;
      max-width: 600px;
      padding: 2rem;
    }
    h1 { color: #ef4444; margin-bottom: 1rem; font-size: 2rem; }
    p { margin-bottom: 1rem; font-size: 1.1rem; }
    .details {
      background: rgba(0, 0, 0, 0.3);
      padding: 1rem;
      border-radius: 8px;
      margin-top: 1rem;
      font-family: monospace;
      font-size: 0.9rem;
      text-align: left;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <div class="error-container">
    <h1>${title}</h1>
    <p>${message}</p>
    ${details ? `<div class="details">${details}</div>` : ''}
  </div>
</body>
</html>`;
}
