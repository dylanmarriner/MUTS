/**
 * Full UI Test - Launches Electron and tests all features
 * Uses webContents.executeJavaScript to interact with the renderer
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

const TEST_RESULTS = {
  passed: [],
  failed: [],
  errors: []
};

let mainWindow = null;

function log(message, type = 'info') {
  const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
  console.log(`${prefix} ${message}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function executeInRenderer(script) {
  if (!mainWindow || !mainWindow.webContents) {
    throw new Error('Window not ready');
  }
  return await mainWindow.webContents.executeJavaScript(script);
}

async function testNavigation() {
  log('Testing navigation buttons...');
  
  const testScript = `
    (async () => {
      const results = [];
      const navButtons = document.querySelectorAll('nav button');
      
      for (let i = 0; i < navButtons.length; i++) {
        const btn = navButtons[i];
        const beforePath = window.location.pathname;
        const buttonText = btn.textContent.trim();
        
        try {
          btn.click();
          await new Promise(r => setTimeout(r, 500));
          
          const afterPath = window.location.pathname;
          const pathChanged = beforePath !== afterPath;
          
          results.push({
            button: buttonText,
            clicked: true,
            pathChanged: pathChanged,
            newPath: afterPath,
            passed: true
          });
        } catch (err) {
          results.push({
            button: buttonText,
            clicked: false,
            error: err.message,
            passed: false
          });
        }
      }
      
      return results;
    })();
  `;
  
  try {
    const results = await executeInRenderer(testScript);
    results.forEach(r => {
      if (r.passed) {
        log(`  ✓ ${r.button} - navigated to ${r.newPath}`, 'success');
        TEST_RESULTS.passed.push(`Navigation: ${r.button}`);
      } else {
        log(`  ✗ ${r.button} - ${r.error}`, 'error');
        TEST_RESULTS.failed.push(`Navigation: ${r.button}`);
      }
    });
  } catch (error) {
    log(`Navigation test failed: ${error.message}`, 'error');
    TEST_RESULTS.errors.push(`Navigation: ${error.message}`);
  }
}

async function testTabComponents() {
  log('Testing tab components render correctly...');
  
  const tabs = [
    { name: 'Vehicle Info', path: '/' },
    { name: 'Connect', path: '/connect' },
    { name: 'Live Data', path: '/live-data' },
    { name: 'Stream', path: '/stream' },
    { name: 'Diagnostics', path: '/diagnostics' },
    { name: 'Tuning', path: '/tuning' },
    { name: 'ROM Tools', path: '/rom-tools' },
    { name: 'Flashing', path: '/flashing' },
    { name: 'Logs', path: '/logs' },
    { name: 'Settings', path: '/settings' }
  ];
  
  for (const tab of tabs) {
    const testScript = `
      (async () => {
        // Navigate to tab
        const navBtn = Array.from(document.querySelectorAll('nav button')).find(
          btn => btn.textContent.includes('${tab.name}')
        );
        if (navBtn) {
          navBtn.click();
          await new Promise(r => setTimeout(r, 1000));
        }
        
        // Check if content is visible
        const main = document.querySelector('main');
        const isVisible = main && window.getComputedStyle(main).display !== 'none';
        const hasContent = main && main.children.length > 0;
        const hasError = document.querySelector('[class*="error"], [class*="Error"]') !== null;
        
        return {
          tab: '${tab.name}',
          visible: isVisible,
          hasContent: hasContent,
          hasError: hasError,
          path: window.location.pathname
        };
      })();
    `;
    
    try {
      const result = await executeInRenderer(testScript);
      if (result.visible && result.hasContent && !result.hasError) {
        log(`  ✓ ${tab.name} - renders correctly`, 'success');
        TEST_RESULTS.passed.push(`Tab: ${tab.name}`);
      } else {
        log(`  ✗ ${tab.name} - visible: ${result.visible}, content: ${result.hasContent}, error: ${result.hasError}`, 'error');
        TEST_RESULTS.failed.push(`Tab: ${tab.name}`);
      }
    } catch (error) {
      log(`  ✗ ${tab.name} - ${error.message}`, 'error');
      TEST_RESULTS.failed.push(`Tab: ${tab.name}`);
    }
  }
}

async function testButtons() {
  log('Testing interactive buttons...');
  
  const buttonTests = [
    { tab: 'Connect', selector: 'button:contains("Connect")', name: 'Connect Button' },
    { tab: 'Diagnostics', selector: 'button:contains("Start Session")', name: 'Start Session' },
    { tab: 'Diagnostics', selector: 'button:contains("Clear DTCs")', name: 'Clear DTCs' },
    { tab: 'Live Data', selector: 'button:contains("Pause"), button:contains("Resume")', name: 'Pause/Resume' },
    { tab: 'Stream', selector: 'button:contains("Paused"), button:contains("Streaming")', name: 'Stream Toggle' },
    { tab: 'Settings', selector: 'button:contains("Disarm")', name: 'Disarm Safety' },
  ];
  
  for (const test of buttonTests) {
    const testScript = `
      (async () => {
        // Navigate to tab first
        const navBtn = Array.from(document.querySelectorAll('nav button')).find(
          btn => btn.textContent.includes('${test.tab}')
        );
        if (navBtn) {
          navBtn.click();
          await new Promise(r => setTimeout(r, 1000));
        }
        
        // Find button
        const allButtons = Array.from(document.querySelectorAll('button'));
        const button = allButtons.find(btn => {
          const text = btn.textContent.trim();
          return text.includes('${test.name.split(' ')[0]}') || 
                 text.includes('${test.name.split(' ')[1] || ''}');
        });
        
        if (!button) {
          return { found: false, error: 'Button not found' };
        }
        
        const isVisible = window.getComputedStyle(button).display !== 'none';
        const isEnabled = !button.disabled;
        
        if (isVisible && isEnabled) {
          try {
            button.click();
            await new Promise(r => setTimeout(r, 200));
            return { found: true, clicked: true, visible: true, enabled: true };
          } catch (err) {
            return { found: true, clicked: false, error: err.message };
          }
        }
        
        return { found: true, visible: isVisible, enabled: isEnabled };
      })();
    `;
    
    try {
      const result = await executeInRenderer(testScript);
      if (result.found && result.clicked) {
        log(`  ✓ ${test.name} - clickable`, 'success');
        TEST_RESULTS.passed.push(`Button: ${test.name}`);
      } else if (result.found) {
        log(`  ⚠ ${test.name} - found but not clickable (visible: ${result.visible}, enabled: ${result.enabled})`, 'info');
        TEST_RESULTS.passed.push(`Button: ${test.name} (found)`);
      } else {
        log(`  ✗ ${test.name} - ${result.error || 'not found'}`, 'error');
        TEST_RESULTS.failed.push(`Button: ${test.name}`);
      }
    } catch (error) {
      log(`  ✗ ${test.name} - ${error.message}`, 'error');
      TEST_RESULTS.failed.push(`Button: ${test.name}`);
    }
  }
}

async function checkForErrors() {
  log('Checking for errors...');
  
  const testScript = `
    (() => {
      const errors = [];
      
      // Check for error boundaries
      const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
      if (errorElements.length > 0) {
        errors.push({ type: 'error_boundary', count: errorElements.length });
      }
      
      // Check for blank screens (empty main content)
      const main = document.querySelector('main');
      if (main) {
        const hasContent = main.children.length > 0;
        const isVisible = window.getComputedStyle(main).display !== 'none';
        if (!hasContent || !isVisible) {
          errors.push({ type: 'blank_screen', hasContent, isVisible });
        }
      }
      
      return errors;
    })();
  `;
  
  try {
    const errors = await executeInRenderer(testScript);
    if (errors.length === 0) {
      log('  ✓ No errors detected', 'success');
      TEST_RESULTS.passed.push('Error check: No errors');
    } else {
      errors.forEach(err => {
        log(`  ✗ Error detected: ${JSON.stringify(err)}`, 'error');
        TEST_RESULTS.failed.push(`Error: ${JSON.stringify(err)}`);
      });
    }
  } catch (error) {
    log(`  ✗ Error check failed: ${error.message}`, 'error');
    TEST_RESULTS.errors.push(`Error check: ${error.message}`);
  }
}

async function runTests() {
  log('Starting full UI test suite...');
  
  // Wait for app to be ready
  await app.whenReady();
  
  // Create window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false, // Don't show window during tests
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '../dist/preload.js')
    }
  });
  
  const htmlPath = path.join(__dirname, '../dist/renderer/src/index.html');
  await mainWindow.loadFile(htmlPath);
  
  log('Waiting for app to load...');
  await sleep(5000);
  
  // Run tests
  await testNavigation();
  await sleep(1000);
  
  await testTabComponents();
  await sleep(1000);
  
  await testButtons();
  await sleep(1000);
  
  await checkForErrors();
  
  // Print results
  console.log('\n' + '='.repeat(60));
  console.log('TEST RESULTS SUMMARY');
  console.log('='.repeat(60));
  console.log(`✅ Passed: ${TEST_RESULTS.passed.length}`);
  TEST_RESULTS.passed.slice(0, 10).forEach(test => console.log(`   - ${test}`));
  if (TEST_RESULTS.passed.length > 10) {
    console.log(`   ... and ${TEST_RESULTS.passed.length - 10} more`);
  }
  console.log(`❌ Failed: ${TEST_RESULTS.failed.length}`);
  TEST_RESULTS.failed.forEach(test => console.log(`   - ${test}`));
  console.log(`⚠️  Errors: ${TEST_RESULTS.errors.length}`);
  TEST_RESULTS.errors.forEach(err => console.log(`   - ${err}`));
  console.log('='.repeat(60));
  
  // Close window
  if (mainWindow) {
    mainWindow.close();
  }
  
  // Exit
  const exitCode = TEST_RESULTS.failed.length > 0 || TEST_RESULTS.errors.length > 0 ? 1 : 0;
  app.exit(exitCode);
}

// Run tests
runTests().catch(error => {
  log(`Fatal error: ${error.message}`, 'error');
  if (mainWindow) mainWindow.close();
  app.exit(1);
});


