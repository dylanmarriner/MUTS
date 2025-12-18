const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Window controls
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  
  // Theme management
  getThemeCSS: () => ipcRenderer.invoke('get-theme-css'),
  
  // Vehicle management
  getVehicles: () => ipcRenderer.invoke('get-vehicles'),
  addVehicle: (vehicleData) => ipcRenderer.invoke('add-vehicle', vehicleData),
  deleteVehicle: (vehicleId) => ipcRenderer.invoke('delete-vehicle', vehicleId),
  
  // DTC management
  getDTCs: (vehicleId) => ipcRenderer.invoke('get-dtcs', vehicleId),
  createDTC: (vehicleId, dtcData) => ipcRenderer.invoke('create-dtc', vehicleId, dtcData),
  clearDTC: (dtcId) => ipcRenderer.invoke('clear-dtc', dtcId),
  
  // Log management
  getLogs: (level, limit) => ipcRenderer.invoke('get-logs', level, limit),
  createLog: (logData) => ipcRenderer.invoke('create-log', logData),
  
  // Performance runs
  getPerformanceRuns: (vehicleId) => ipcRenderer.invoke('get-performance-runs', vehicleId),
  createPerformanceRun: (vehicleId, runData) => ipcRenderer.invoke('create-performance-run', vehicleId, runData),
  
  // Security events
  getSecurityEvents: (eventType, limit) => ipcRenderer.invoke('get-security-events', eventType, limit),
  createSecurityEvent: (eventData) => ipcRenderer.invoke('create-security-event', eventData),
  
  // AI models
  getAIModels: () => ipcRenderer.invoke('get-ai-models'),
  createAIModel: (modelData) => ipcRenderer.invoke('create-ai-model', modelData),
  
  // Training data
  getTrainingData: (limit) => ipcRenderer.invoke('get-training-data', limit),
  createTrainingData: (data) => ipcRenderer.invoke('create-training-data', data),
  
  // Telemetry sessions
  getTelemetrySessions: (vehicleId) => ipcRenderer.invoke('get-telemetry-sessions', vehicleId),
  createTelemetrySession: (vehicleId, sessionData) => ipcRenderer.invoke('create-telemetry-session', vehicleId, sessionData),
  
  // User sessions
  getCurrentUser: () => ipcRenderer.invoke('get-current-user'),
  login: (credentials) => ipcRenderer.invoke('login', credentials),
  logout: () => ipcRenderer.invoke('logout'),
  
  // Vehicle Constants API
  getConstantsPresets: () => ipcRenderer.invoke('get-constants-presets'),
  getVehicleConstants: (vehicleId) => ipcRenderer.invoke('get-vehicle-constants', vehicleId),
  getActiveVehicleConstants: (vehicleId) => ipcRenderer.invoke('get-active-vehicle-constants', vehicleId),
  createVehicleConstants: (vehicleId, data) => ipcRenderer.invoke('create-vehicle-constants', vehicleId, data),
  activateVehicleConstants: (constantsId) => ipcRenderer.invoke('activate-vehicle-constants', constantsId),
  restoreDefaultConstants: (vehicleId) => ipcRenderer.invoke('restore-default-constants', vehicleId),
  getPresetHierarchy: () => ipcRenderer.invoke('get-preset-hierarchy'),

  // Dyno operations
  createDynoRun: (vehicleId, telemetrySessionId, tuningProfileId) => 
    ipcRenderer.invoke('create-dyno-run', vehicleId, telemetrySessionId, tuningProfileId),
  processDynoRun: (runId) => ipcRenderer.invoke('process-dyno-run', runId),
  getDynoRuns: (vehicleId) => ipcRenderer.invoke('get-dyno-runs', vehicleId),
  getDynoRun: (runId) => ipcRenderer.invoke('get-dyno-run', runId),
  compareDynoRuns: (run1Id, run2Id) => ipcRenderer.invoke('compare-dyno-runs', run1Id, run2Id),
  getDynoSamples: (runId) => ipcRenderer.invoke('get-dyno-samples', runId),
  
  // Theme change event
  onThemeChange: (callback) => ipcRenderer.on('theme-changed', callback),
  removeThemeListener: (callback) => ipcRenderer.removeListener('theme-changed', callback),
  
  // File operations
  openFile: () => ipcRenderer.invoke('dialog-open-file'),
  saveFile: (data) => ipcRenderer.invoke('dialog-save-file', data),
  
  // System info
  getPlatform: () => process.platform,
  
  // App version
  getVersion: () => ipcRenderer.invoke('app-version')
});

// Theme management
let currentTheme = 'cyan';

// Apply theme to document
function applyTheme(themeName) {
  // Check if document is available
  if (typeof document === 'undefined') return;
  
  const root = document.documentElement;
  
  // Remove existing theme class
  root.classList.remove('theme-cyan', 'theme-violet', 'theme-red', 
                      'theme-amber', 'theme-green', 'theme-rose');
  
  // Add new theme class
  root.classList.add(`theme-${themeName}`);
  
  // Store current theme
  currentTheme = themeName;
  localStorage.setItem('versatuner-theme', themeName);
  
  // Update meta theme-color
  const themeColors = {
    cyan: '#06b6d4',
    violet: '#d946ef',
    red: '#ef4444',
    amber: '#f59e0b',
    green: '#22c55e',
    rose: '#f43f5e'
  };
  
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) {
    metaTheme.content = themeColors[themeName];
  }
}

// Initialize theme when DOM is ready
function initializeTheme() {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      const savedTheme = localStorage.getItem('versatuner-theme') || 'cyan';
      applyTheme(savedTheme);
    });
  } else {
    const savedTheme = localStorage.getItem('versatuner-theme') || 'cyan';
    applyTheme(savedTheme);
  }
}

// Listen for theme changes from main process
ipcRenderer.on('theme-change', (event, themeName) => {
  applyTheme(themeName);
});

// Export theme functions through contextBridge
contextBridge.exposeInMainWorld('themeAPI', {
  applyTheme: applyTheme,
  getCurrentTheme: () => currentTheme
});

// Initialize theme
initializeTheme();
