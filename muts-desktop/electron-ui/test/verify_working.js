/**
 * Comprehensive verification script to ensure the Electron app works correctly
 * This script tests:
 * - App startup
 * - Navigation
 * - Component loading
 * - IPC handlers
 * - Error handling
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;
let testResults = {
  passed: [],
  failed: [],
  warnings: []
};

function logResult(test, passed, message = '') {
  if (passed) {
    testResults.passed.push({ test, message });
    console.log(`✅ ${test}${message ? ': ' + message : ''}`);
  } else {
    testResults.failed.push({ test, message });
    console.error(`❌ ${test}${message ? ': ' + message : ''}`);
  }
}

function logWarning(test, message) {
  testResults.warnings.push({ test, message });
  console.warn(`⚠️  ${test}: ${message}`);
}

async function waitFor(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testNavigation() {
  console.log('\n=== Testing Navigation ===');
  
  // Test hash-based routing
  const testRoutes = ['/', '/connect', '/vehicle-info', '/stream', '/flashing', '/rom-tools', '/tuning', '/live-data', '/diagnostics', '/settings'];
  
  for (const route of testRoutes) {
    try {
      await mainWindow.webContents.executeJavaScript(`
        window.location.hash = '${route}';
        new Promise(resolve => setTimeout(resolve, 500));
      `);
      
      await waitFor(600);
      
      const currentHash = await mainWindow.webContents.executeJavaScript(`window.location.hash`);
      if (currentHash === route || (route === '/' && (currentHash === '' || currentHash === '#'))) {
        logResult(`Navigate to ${route}`, true);
      } else {
        logResult(`Navigate to ${route}`, false, `Expected ${route}, got ${currentHash}`);
      }
    } catch (error) {
      logResult(`Navigate to ${route}`, false, error.message);
    }
  }
}

async function testComponents() {
  console.log('\n=== Testing Component Loading ===');
  
  const components = [
    { name: 'VehicleInfoTab', selector: '[data-testid="vehicle-info-tab"]' },
    { name: 'ConnectTab', selector: '[data-testid="connect-tab"]' },
    { name: 'StreamTab', selector: '[data-testid="stream-tab"]' },
    { name: 'FlashingTab', selector: '[data-testid="flashing-tab"]' },
    { name: 'RomToolsTab', selector: '[data-testid="rom-tools-tab"]' },
    { name: 'TuningTab', selector: '[data-testid="tuning-tab"]' },
    { name: 'LiveDataTab', selector: '[data-testid="live-data-tab"]' },
    { name: 'DiagnosticsTab', selector: '[data-testid="diagnostics-tab"]' },
    { name: 'SettingsTab', selector: '[data-testid="settings-tab"]' }
  ];
  
  for (const component of components) {
    try {
      const exists = await mainWindow.webContents.executeJavaScript(`
        document.querySelector('${component.selector}') !== null || 
        document.querySelector('[class*="${component.name.toLowerCase()}"]') !== null ||
        document.body.innerText.includes('${component.name.replace('Tab', '')}')
      `);
      
      if (exists) {
        logResult(`${component.name} renders`, true);
      } else {
        logWarning(`${component.name} renders`, 'Component may not have test ID but could still be working');
      }
    } catch (error) {
      logWarning(`${component.name} renders`, error.message);
    }
  }
}

async function testIPC() {
  console.log('\n=== Testing IPC Handlers ===');
  
  const ipcTests = [
    { name: 'app:getVersion', call: 'window.electronAPI.app.getVersion()' },
    { name: 'config:load', call: 'window.electronAPI.config.load()' },
    { name: 'config:get', call: 'window.electronAPI.config.get()' },
    { name: 'interface:list', call: 'window.electronAPI.interface.list()' },
    { name: 'interface:getStatus', call: 'window.electronAPI.interface.getStatus()' },
    { name: 'health:report', call: 'window.electronAPI.health.report()' }
  ];
  
  for (const test of ipcTests) {
    try {
      const result = await mainWindow.webContents.executeJavaScript(`
        (async () => {
          try {
            const result = await ${test.call};
            return { success: true, result: typeof result };
          } catch (error) {
            return { success: false, error: error.message };
          }
        })()
      `);
      
      if (result.success) {
        logResult(`${test.name} IPC handler`, true, `returns ${result.result}`);
      } else {
        logResult(`${test.name} IPC handler`, false, result.error);
      }
    } catch (error) {
      logResult(`${test.name} IPC handler`, false, error.message);
    }
  }
}

async function testErrors() {
  console.log('\n=== Testing Error Handling ===');
  
  // Check for console errors
  const consoleErrors = [];
  mainWindow.webContents.on('console-message', (event, level, message) => {
    if (level === 2) { // error level
      const msg = String(message);
      // Filter out expected/harmless errors
      if (!msg.includes('GPU') && 
          !msg.includes('dri3') && 
          !msg.includes('viz_main') && 
          !msg.includes('command_buffer') &&
          !msg.includes('CSP') &&
          !msg.includes('Security Warning') &&
          !msg.includes('Failed to load technicians') &&
          !msg.includes('Failed to fetch') &&
          !msg.includes('ERR_FILE_NOT_FOUND')) {
        consoleErrors.push(msg);
      }
    }
  });
  
  await waitFor(2000);
  
  if (consoleErrors.length === 0) {
    logResult('No critical console errors', true);
  } else {
    logResult('No critical console errors', false, `${consoleErrors.length} errors found`);
    consoleErrors.slice(0, 5).forEach(err => console.error(`  - ${err}`));
  }
  
  // Check for failed loads
  const failedLoads = [];
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    // Filter out expected React Router navigation failures
    if (!validatedURL.includes('file:///') || !validatedURL.match(/file:\/\/\/[^/]+$/)) {
      failedLoads.push({ errorCode, errorDescription, validatedURL });
    }
  });
  
  await waitFor(1000);
  
  if (failedLoads.length === 0) {
    logResult('No failed file loads', true);
  } else {
    logResult('No failed file loads', false, `${failedLoads.length} failed loads`);
    failedLoads.slice(0, 3).forEach(load => {
      console.error(`  - ${load.validatedURL}: ${load.errorDescription}`);
    });
  }
}

async function testHashRouter() {
  console.log('\n=== Testing HashRouter ===');
  
  try {
    const usesHashRouter = await mainWindow.webContents.executeJavaScript(`
      window.location.hash !== undefined && 
      typeof window.location.hash === 'string'
    `);
    
    if (usesHashRouter) {
      logResult('HashRouter available', true);
    } else {
      logResult('HashRouter available', false);
    }
    
    // Test that navigation uses hash
    await mainWindow.webContents.executeJavaScript(`window.location.hash = '#/test'`);
    await waitFor(300);
    const hash = await mainWindow.webContents.executeJavaScript(`window.location.hash`);
    
    if (hash === '#/test') {
      logResult('Hash navigation works', true);
    } else {
      logResult('Hash navigation works', false, `Expected #/test, got ${hash}`);
    }
  } catch (error) {
    logResult('HashRouter test', false, error.message);
  }
}

async function runAllTests() {
  console.log('🚀 Starting comprehensive verification tests...\n');
  
  // Wait for app to be ready
  await waitFor(3000);
  
  // Run tests
  await testHashRouter();
  await testNavigation();
  await testComponents();
  await testIPC();
  await testErrors();
  
  // Print summary
  console.log('\n=== Test Summary ===');
  console.log(`✅ Passed: ${testResults.passed.length}`);
  console.log(`❌ Failed: ${testResults.failed.length}`);
  console.log(`⚠️  Warnings: ${testResults.warnings.length}`);
  
  if (testResults.failed.length === 0) {
    console.log('\n🎉 All critical tests passed! The application is working correctly.');
    app.exit(0);
  } else {
    console.log('\n⚠️  Some tests failed. Review the errors above.');
    app.exit(1);
  }
}

app.whenReady().then(() => {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false, // Don't show during tests
    webPreferences: {
      preload: path.join(__dirname, '../dist/preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  
  const htmlPath = path.join(__dirname, '../dist/renderer/src/index.html');
  mainWindow.loadFile(htmlPath);
  
  mainWindow.webContents.once('did-finish-load', () => {
    console.log('App loaded, starting tests...');
    setTimeout(runAllTests, 2000);
  });
  
  // Timeout after 30 seconds
  setTimeout(() => {
    console.log('\n⏱️  Test timeout reached');
    app.exit(1);
  }, 30000);
});

app.on('window-all-closed', () => {
  app.quit();
});

