/**
 * Electron Main Process
 * Entry point for the MUTS desktop application
 */

import { app, BrowserWindow, ipcMain, Menu, shell, dialog } from 'electron';
import * as path from 'path';
import { logger } from './utils/logger';
import { createWindow } from './window';
import { initializeWebSocket } from './services/websocket';

let mainWindow: BrowserWindow | null = null;

function createMainWindow(): void {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    titleBarStyle: 'default',
    show: false, // Don't show until ready-to-show
  });

  // Load the app - always use production file loading
  console.log('Loading app from:', path.join(__dirname, 'renderer/src/index.html'));
  mainWindow.loadFile(path.join(__dirname, 'renderer/src/index.html'))
    .catch(err => {
      console.error('Failed to load app:', err);
      // Show error screen
      if (mainWindow) {
        mainWindow.loadURL('data:text/html,<html><body style="background:#1e293b;color:white;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center;"><h1 style="color:#ef4444;">Failed to Load Application</h1><p>Could not load the renderer. Please restart the application.</p></div></body></html>');
      }
    }); 
  mainWindow.webContents.openDevTools();

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    console.log('Window ready to show');
    mainWindow?.show();
    
    if (!app.isPackaged) {
      mainWindow?.webContents.openDevTools();
    }
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

// IPC handlers for main process
ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

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

// Flash handlers
ipcMain.handle('flash:validate', async (_, romData: ArrayBuffer) => {
  try {
    // Return basic validation for now
    return { valid: true, errors: [] };
  } catch (error) {
    console.error('Failed to validate ROM:', error);
    return { valid: false, errors: ['Validation failed'] };
  }
});

ipcMain.handle('flash:checksum', async (_, romData: ArrayBuffer) => {
  try {
    // Return dummy checksum for now
    return { checksum: '00000000', valid: true };
  } catch (error) {
    console.error('Failed to calculate checksum:', error);
    return { checksum: '00000000', valid: false };
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
    return { url: '', filename: `telemetry-${sessionId}.${format}` };
  } catch (error) {
    console.error('Failed to export telemetry:', error);
    return null;
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
}).catch((error) => {
  console.error('Failed to initialize app:', error);
  app.quit();
});
