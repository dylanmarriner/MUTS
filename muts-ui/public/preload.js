const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Hardware access methods
  getSerialPorts: () => ipcRenderer.invoke('get-serial-ports'),
  connectDevice: (deviceInfo) => ipcRenderer.invoke('connect-device', deviceInfo),
  
  // App control
  quitApp: () => ipcRenderer.invoke('quit-app'),
  minimizeApp: () => ipcRenderer.invoke('minimize-app'),
  
  // File system access
  selectFile: (filters) => ipcRenderer.invoke('select-file', filters),
  saveFile: (data, filename) => ipcRenderer.invoke('save-file', data, filename),
  
  // Development helpers
  openDevTools: () => ipcRenderer.invoke('open-dev-tools'),
  
  // Events
  onHardwareStatus: (callback) => {
    ipcRenderer.on('hardware-status', callback);
    return () => ipcRenderer.removeListener('hardware-status', callback);
  }
});
