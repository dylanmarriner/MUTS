import { BrowserWindow, app } from 'electron';

export function createWindow(): BrowserWindow {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: __dirname + '/preload.js'
    }
  });

  // Note: This function is not used - main.ts has its own window creation logic
  return mainWindow;
}
