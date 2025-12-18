const { app, BrowserWindow, ipcMain, Menu, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const APIService = require('./api-service');

// Initialize API service
const api = new APIService();

// Backend process reference
let backendProcess = null;

// Start Python backend
function startBackend() {
  const isDev = process.env.NODE_ENV === 'development';
  const isProd = process.env.NODE_ENV === 'production';

  let backendPath;
  let backendArgs;

  if (isProd) {
    // In production, use the bundled executable
    const resourcesPath = process.resourcesPath;
    backendPath = path.join(resourcesPath, 'backend', 'muts-backend.exe');
    backendArgs = [];
  } else {
    // In development, use Python directly
    backendPath = 'python';
    backendArgs = ['-m', 'app.api.main'];
  }

  console.log(`Starting backend: ${backendPath} ${backendArgs.join(' ')}`);

  backendProcess = spawn(backendPath, backendArgs, {
    cwd: isDev ? path.join(__dirname, '..') : process.resourcesPath,
    stdio: ['pipe', 'pipe', 'pipe']
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data}`);
  });

  backendProcess.on('error', (error) => {
    console.error(`Failed to start backend: ${error}`);
    dialog.showErrorBox(
      'Backend Error',
      'Failed to start the MUTS backend. Please check your installation.'
    );
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    backendProcess = null;
  });

  return backendProcess;
}

// Check if API server is running
async function checkAPIServer(maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    const health = await api.healthCheck();
    if (health) {
      console.log('API server is healthy');
      return true;
    }

    console.log(`Waiting for API server... (${i + 1}/${maxRetries})`);
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log('API server failed to start');
  return false;
}

// Enable live reload for development
if (process.env.NODE_ENV === 'development') {
  require('electron-reload')(__dirname, {
    electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
    hardResetMethod: 'exit'
  });
}

let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    show: false,
    frame: false,
    transparent: true,
    backgroundColor: '#0f172a'
  });

  // Load the index.html file
  mainWindow.loadFile('index.html');

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();

    // Open DevTools in development
    if (process.env.NODE_ENV === 'development') {
      mainWindow.webContents.openDevTools();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open ROM',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            mainWindow.webContents.send('menu-open-rom');
          }
        },
        {
          label: 'Save Tune',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            mainWindow.webContents.send('menu-save-tune');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Toggle Full Screen',
          accelerator: 'F11',
          click: () => {
            if (mainWindow) {
              mainWindow.setFullScreen(!mainWindow.isFullScreen());
            }
          }
        },
        {
          label: 'Toggle DevTools',
          accelerator: 'F12',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        }
      ]
    },
    {
      label: 'Theme',
      submenu: [
        {
          label: 'Sci-fi Cyan',
          type: 'radio',
          checked: true,
          click: () => {
            mainWindow.webContents.send('theme-change', 'cyan');
          }
        },
        {
          label: 'Sci-fi Violet',
          type: 'radio',
          click: () => {
            mainWindow.webContents.send('theme-change', 'violet');
          }
        },
        {
          label: 'Sci-fi Red',
          type: 'radio',
          click: () => {
            mainWindow.webContents.send('theme-change', 'red');
          }
        },
        {
          label: 'Sci-fi Amber',
          type: 'radio',
          click: () => {
            mainWindow.webContents.send('theme-change', 'amber');
          }
        },
        {
          label: 'Sci-fi Green',
          type: 'radio',
          click: () => {
            mainWindow.webContents.send('theme-change', 'green');
          }
        },
        {
          label: 'Sci-fi Rose',
          type: 'radio',
          click: () => {
            mainWindow.webContents.send('theme-change', 'rose');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC handlers
ipcMain.handle('window-minimize', () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window-close', () => {
  if (mainWindow) {
    mainWindow.close();
  }
});

ipcMain.handle('get-theme-data', () => {
  try {
    const themePath = path.join(__dirname, 'theme.css');
    const themeCSS = fs.readFileSync(themePath, 'utf8');
    return themeCSS;
  } catch (error) {
    console.error('Error reading theme file:', error);
    return '';
  }
});

// Vehicle management handlers
ipcMain.handle('get-vehicles', async () => {
  try {
    const vehicles = await api.getVehicles();
    return vehicles;
  } catch (error) {
    console.error('Error fetching vehicles:', error);
    return [];
  }
});

ipcMain.handle('add-vehicle', async (event, vehicleData) => {
  try {
    const result = await api.createVehicle(vehicleData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error adding vehicle:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('delete-vehicle', async (event, vehicleId) => {
  try {
    const result = await api.deleteVehicle(vehicleId);
    return result;
  } catch (error) {
    console.error('Error deleting vehicle:', error);
    return { success: false, error: error.message };
  }
});

// DTC handlers
ipcMain.handle('get-dtcs', async (event, vehicleId) => {
  try {
    const dtcs = await api.getDTCs(vehicleId);
    return dtcs;
  } catch (error) {
    console.error('Error fetching DTCs:', error);
    return [];
  }
});

ipcMain.handle('create-dtc', async (event, vehicleId, dtcData) => {
  try {
    const result = await api.createDTC(vehicleId, dtcData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating DTC:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('clear-dtc', async (event, dtcId) => {
  try {
    const result = await api.clearDTC(dtcId);
    return result;
  } catch (error) {
    console.error('Error clearing DTC:', error);
    return { success: false, error: error.message };
  }
});

// Log handlers
ipcMain.handle('get-logs', async (event, level, limit = 100) => {
  try {
    const logs = await api.getLogs(level, limit);
    return logs;
  } catch (error) {
    console.error('Error fetching logs:', error);
    return [];
  }
});

ipcMain.handle('create-log', async (event, logData) => {
  try {
    const result = await api.createLog(logData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating log:', error);
    return { success: false, error: error.message };
  }
});

// Performance run handlers
ipcMain.handle('get-performance-runs', async (event, vehicleId) => {
  try {
    const runs = await api.getPerformanceRuns(vehicleId);
    return runs;
  } catch (error) {
    console.error('Error fetching performance runs:', error);
    return [];
  }
});

ipcMain.handle('create-performance-run', async (event, vehicleId, runData) => {
  try {
    const result = await api.createPerformanceRun(vehicleId, runData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating performance run:', error);
    return { success: false, error: error.message };
  }
});

// Security event handlers
ipcMain.handle('get-security-events', async (event, eventType, limit = 100) => {
  try {
    const events = await api.getSecurityEvents(eventType, limit);
    return events;
  } catch (error) {
    console.error('Error fetching security events:', error);
    return [];
  }
});

ipcMain.handle('create-security-event', async (event, eventData) => {
  try {
    const result = await api.createSecurityEvent(eventData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating security event:', error);
    return { success: false, error: error.message };
  }
});

// AI model handlers
ipcMain.handle('get-ai-models', async () => {
  try {
    const models = await api.getAIModels();
    return models;
  } catch (error) {
    console.error('Error fetching AI models:', error);
    return [];
  }
});

ipcMain.handle('create-ai-model', async (event, modelData) => {
  try {
    const result = await api.createAIModel(modelData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating AI model:', error);
    return { success: false, error: error.message };
  }
});

// Training data handlers
ipcMain.handle('get-training-data', async (event, limit = 100) => {
  try {
    const data = await api.getTrainingData(limit);
    return data;
  } catch (error) {
    console.error('Error fetching training data:', error);
    return [];
  }
});

ipcMain.handle('create-training-data', async (event, data) => {
  try {
    const result = await api.createTrainingData(data);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating training data:', error);
    return { success: false, error: error.message };
  }
});

// Telemetry session handlers
ipcMain.handle('get-telemetry-sessions', async (event, vehicleId) => {
  try {
    const sessions = await api.getTelemetrySessions(vehicleId);
    return sessions;
  } catch (error) {
    console.error('Error fetching telemetry sessions:', error);
    return [];
  }
});

ipcMain.handle('create-telemetry-session', async (event, vehicleId, sessionData) => {
  try {
    const result = await api.createTelemetrySession(vehicleId, sessionData);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating telemetry session:', error);
    return { success: false, error: error.message };
  }
});

// User session handlers
ipcMain.handle('get-current-user', async () => {
  try {
    const user = await api.getCurrentUser();
    return user;
  } catch (error) {
    console.error('Error fetching current user:', error);
    return { username: 'Guest', role: 'Viewer' };
  }
});

ipcMain.handle('login', async (event, credentials) => {
  try {
    const result = await api.login(credentials);
    return result;
  } catch (error) {
    console.error('Login failed:', error);
    return { success: false, error: 'Login failed' };
  }
});

ipcMain.handle('logout', async () => {
  try {
    const result = await api.logout();
    return result;
  } catch (error) {
    console.error('Logout failed:', error);
    return { success: false, error: 'Logout failed' };
  }
});

// Vehicle Constants handlers
ipcMain.handle('get-constants-presets', async () => {
  return await apiService.getConstantsPresets();
});

ipcMain.handle('get-preset-hierarchy', async () => {
  return await apiService.getPresetHierarchy();
});

ipcMain.handle('get-vehicle-constants', async (event, vehicleId) => {
  return await apiService.getVehicleConstants(vehicleId);
});

ipcMain.handle('get-active-vehicle-constants', async (event, vehicleId) => {
  return await apiService.getActiveVehicleConstants(vehicleId);
});

ipcMain.handle('create-vehicle-constants', async (event, vehicleId, data) => {
  return await apiService.createVehicleConstants(vehicleId, data);
});

ipcMain.handle('activate-vehicle-constants', async (event, vehicleId, constantsId) => {
  return await apiService.activateVehicleConstants(vehicleId, constantsId);
});

ipcMain.handle('restore-default-constants', async (event, vehicleId) => {
  return await apiService.restoreDefaultConstants(vehicleId);
});

// Dyno handlers
ipcMain.handle('create-dyno-run', async (event, vehicleId, telemetrySessionId, tuningProfileId) => {
  try {
    const result = await api.createDynoRun(vehicleId, telemetrySessionId, tuningProfileId);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error creating dyno run:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('process-dyno-run', async (event, runId) => {
  try {
    const result = await api.processDynoRun(runId);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error processing dyno run:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-dyno-runs', async (event, vehicleId) => {
  try {
    const runs = await api.getDynoRuns(vehicleId);
    return runs;
  } catch (error) {
    console.error('Error fetching dyno runs:', error);
    return [];
  }
});

ipcMain.handle('get-dyno-run', async (event, runId) => {
  try {
    const run = await api.getDynoRun(runId);
    return run;
  } catch (error) {
    console.error('Error fetching dyno run:', error);
    return null;
  }
});

ipcMain.handle('compare-dyno-runs', async (event, run1Id, run2Id) => {
  try {
    const comparison = await api.compareDynoRuns(run1Id, run2Id);
    return { success: true, data: comparison };
  } catch (error) {
    console.error('Error comparing dyno runs:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-dyno-samples', async (event, runId) => {
  try {
    const samples = await api.getDynoSamples(runId);
    return samples;
  } catch (error) {
    console.error('Error fetching dyno samples:', error);
    return [];
  }
});

// App event handlers
app.whenReady().then(async () => {
  // Try to start backend but don't block on it
  console.log('Starting MUTS backend...');
  try {
    startBackend();
    // Check if backend comes up, but don't wait forever (reduced retries, non-blocking)
    checkAPIServer(5).then(backendReady => {
      if (!backendReady) {
        console.log('Backend not available - running in frontend-only mode');
      }
    });
  } catch (error) {
    console.log('Could not start backend, running in frontend-only mode:', error.message);
  }

  // Create window immediately (don't wait for backend)
  createWindow();
  createMenu();
});

app.on('window-all-closed', () => {
  // Kill backend when all windows closed
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }

  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Ensure backend is killed on quit
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
});

// Security settings
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
  });
});
