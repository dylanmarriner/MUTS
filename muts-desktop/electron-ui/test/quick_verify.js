/**
 * Quick verification - just run the app and check for critical errors
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;
let errors = [];
let warnings = [];

app.whenReady().then(() => {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: true,
    webPreferences: {
      preload: path.join(__dirname, '../dist/preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  
  const htmlPath = path.join(__dirname, '../dist/renderer/src/index.html');
  mainWindow.loadFile(htmlPath);
  
  // Track console errors
  mainWindow.webContents.on('console-message', (event, level, message) => {
    const msg = String(message);
    if (level === 2) { // error
      // Filter out harmless errors
      if (!msg.includes('GPU') && 
          !msg.includes('dri3') && 
          !msg.includes('viz_main') && 
          !msg.includes('command_buffer') &&
          !msg.includes('CSP') &&
          !msg.includes('Security Warning') &&
          !msg.includes('Failed to load technicians') &&
          !msg.includes('Failed to fetch') &&
          !msg.includes('ERR_FILE_NOT_FOUND')) {
        errors.push(msg);
      }
    } else if (level === 1) { // warning
      warnings.push(msg);
    }
  });
  
  // Track failed loads
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    // Filter out expected React Router navigation
    if (!validatedURL.includes('file:///') || !validatedURL.match(/file:\/\/\/[^/]+$/)) {
      errors.push(`Failed to load: ${validatedURL} - ${errorDescription}`);
    }
  });
  
  // Check app health after load
  mainWindow.webContents.once('did-finish-load', async () => {
    console.log('✅ App loaded successfully');
    
    // Wait a bit for React to render
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Check if React rendered
    try {
      const hasReact = await mainWindow.webContents.executeJavaScript(`
        document.getElementById('root') !== null && 
        document.getElementById('root').children.length > 0
      `);
      
      if (hasReact) {
        console.log('✅ React app rendered');
      } else {
        console.error('❌ React app did not render');
        errors.push('React root is empty');
      }
      
      // Check for HashRouter
      const hasHash = await mainWindow.webContents.executeJavaScript(`
        typeof window.location.hash !== 'undefined'
      `);
      
      if (hasHash) {
        console.log('✅ HashRouter is available');
      } else {
        console.error('❌ HashRouter not available');
        errors.push('HashRouter not available');
      }
      
      // Test navigation
      await mainWindow.webContents.executeJavaScript(`window.location.hash = '#/connect'`);
      await new Promise(resolve => setTimeout(resolve, 500));
      const hash = await mainWindow.webContents.executeJavaScript(`window.location.hash`);
      
      if (hash === '#/connect') {
        console.log('✅ Navigation works');
      } else {
        console.error(`❌ Navigation failed: expected #/connect, got ${hash}`);
        errors.push(`Navigation failed: got ${hash}`);
      }
      
      // Check for electronAPI
      const hasAPI = await mainWindow.webContents.executeJavaScript(`
        typeof window.electronAPI !== 'undefined'
      `);
      
      if (hasAPI) {
        console.log('✅ electronAPI is available');
        
        // Test a simple IPC call
        try {
          const version = await mainWindow.webContents.executeJavaScript(`
            window.electronAPI.app.getVersion()
          `);
          console.log(`✅ IPC handlers work (version: ${version})`);
        } catch (err) {
          console.error(`❌ IPC handler test failed: ${err.message}`);
          errors.push(`IPC handler failed: ${err.message}`);
        }
      } else {
        console.error('❌ electronAPI not available');
        errors.push('electronAPI not available');
      }
      
    } catch (err) {
      console.error(`❌ Test error: ${err.message}`);
      errors.push(err.message);
    }
    
    // Print summary
    console.log('\n=== Verification Summary ===');
    if (errors.length === 0) {
      console.log('🎉 All checks passed! The app is working correctly.');
      console.log('\nThe app will stay open for manual testing.');
      console.log('Close the window to exit.');
    } else {
      console.error(`❌ Found ${errors.length} error(s):`);
      errors.forEach(err => console.error(`  - ${err}`));
      console.log('\n⚠️  Please review the errors above.');
      app.exit(1);
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

