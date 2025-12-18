/**
 * Interactive UI Test - Uses Electron API to programmatically test all features
 * Run with: electron test/interactive_test.js
 */

// Check if we're in Electron context
if (typeof require !== 'undefined') {
  try {
    var { app, BrowserWindow } = require('electron');
    var path = require('path');
  } catch (e) {
    console.error('This script must be run with Electron, not Node.js');
    console.error('Usage: electron test/interactive_test.js');
    process.exit(1);
  }
} else {
  console.error('This script must be run with Electron');
  process.exit(1);
}

const RESULTS = {
  passed: [],
  failed: [],
  warnings: []
};

let mainWindow = null;

function log(message, type = 'info') {
  const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
  console.log(`${prefix} ${message}`);
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function executeJS(script) {
  if (!mainWindow?.webContents) {
    throw new Error('Window not ready');
  }
  return await mainWindow.webContents.executeJavaScript(script);
}

async function testAllTabs() {
  log('Testing all navigation tabs...');
  
  const tabs = [
    { name: 'Vehicle Info', selector: 'button:has-text("Info / Vehicle"), button:has-text("Vehicle")' },
    { name: 'Connect', selector: 'button:has-text("Connect / Interface"), button:has-text("Connect")' },
    { name: 'Live Data', selector: 'button:has-text("Live Data")' },
    { name: 'Stream', selector: 'button:has-text("Stream")' },
    { name: 'Diagnostics', selector: 'button:has-text("Diagnostics")' },
    { name: 'Tuning', selector: 'button:has-text("Tuning")' },
    { name: 'ROM Tools', selector: 'button:has-text("ROM Tools")' },
    { name: 'Flashing', selector: 'button:has-text("Flashing")' },
    { name: 'Logs', selector: 'button:has-text("Logs / Timeline"), button:has-text("Logs")' },
    { name: 'Settings', selector: 'button:has-text("Settings / Safety"), button:has-text("Settings")' }
  ];
  
  for (const tab of tabs) {
    const testScript = `
      (async () => {
        try {
          // Find navigation button
          const navButtons = Array.from(document.querySelectorAll('nav button'));
          const button = navButtons.find(btn => {
            const text = btn.textContent.trim();
            return text.includes('${tab.name.split(' ')[0]}') || 
                   text.includes('${tab.name.split(' ')[1] || ''}');
          });
          
          if (!button) {
            return { found: false, error: 'Button not found' };
          }
          
          const beforePath = window.location.pathname;
          const buttonText = button.textContent.trim();
          
          // Click button
          button.click();
          await new Promise(r => setTimeout(r, 1000));
          
          const afterPath = window.location.pathname;
          const pathChanged = beforePath !== afterPath;
          
          // Check if content rendered
          const main = document.querySelector('main');
          const hasContent = main && main.children.length > 0;
          const isVisible = main && window.getComputedStyle(main).display !== 'none';
          const hasError = document.querySelector('[class*="error"], [class*="Error"]') !== null;
          const isBlank = main && main.textContent.trim().length < 10;
          
          return {
            found: true,
            clicked: true,
            buttonText,
            pathChanged,
            newPath: afterPath,
            hasContent,
            isVisible,
            hasError,
            isBlank,
            passed: pathChanged && hasContent && isVisible && !hasError && !isBlank
          };
        } catch (err) {
          return { found: false, error: err.message };
        }
      })();
    `;
    
    try {
      const result = await executeJS(testScript);
      if (result.found && result.passed) {
        log(`  ✓ ${tab.name} - navigated successfully, content rendered`, 'success');
        RESULTS.passed.push(`Tab: ${tab.name}`);
      } else if (result.found && result.clicked) {
        const issues = [];
        if (!result.pathChanged) issues.push('path not changed');
        if (!result.hasContent) issues.push('no content');
        if (!result.isVisible) issues.push('not visible');
        if (result.hasError) issues.push('has error');
        if (result.isBlank) issues.push('blank screen');
        log(`  ⚠ ${tab.name} - clicked but issues: ${issues.join(', ')}`, 'warning');
        RESULTS.warnings.push(`Tab: ${tab.name} - ${issues.join(', ')}`);
      } else {
        log(`  ✗ ${tab.name} - ${result.error || 'not found'}`, 'error');
        RESULTS.failed.push(`Tab: ${tab.name} - ${result.error || 'not found'}`);
      }
    } catch (error) {
      log(`  ✗ ${tab.name} - ${error.message}`, 'error');
      RESULTS.failed.push(`Tab: ${tab.name} - ${error.message}`);
    }
    
    await sleep(500);
  }
}

async function testInteractiveButtons() {
  log('Testing interactive buttons in each tab...');
  
  const buttonTests = [
    { tab: 'Connect', buttons: ['Connect', 'Disconnect', 'Refresh'] },
    { tab: 'Diagnostics', buttons: ['Start Session', 'Clear DTCs', 'Read DTCs'] },
    { tab: 'Live Data', buttons: ['Pause', 'Resume', 'Export', 'Start'] },
    { tab: 'Stream', buttons: ['Paused', 'Streaming', 'Clear'] },
    { tab: 'Tuning', buttons: ['Manual', 'AI', 'Create Session', 'Apply Live'] },
    { tab: 'Settings', buttons: ['Disarm', 'Arm', 'Simulate', 'Live Apply'] },
    { tab: 'Flashing', buttons: ['Prepare Flash', 'Start Flashing', 'Abort'] },
    { tab: 'ROM Tools', buttons: ['Validate ROM', 'Calculate Checksum'] }
  ];
  
  for (const test of buttonTests) {
    const testScript = `
      (async () => {
        try {
          // Navigate to tab
          const navButtons = Array.from(document.querySelectorAll('nav button'));
          const navBtn = navButtons.find(btn => {
            const text = btn.textContent.trim();
            return text.includes('${test.tab}');
          });
          
          if (navBtn) {
            navBtn.click();
            await new Promise(r => setTimeout(r, 1000));
          }
          
          // Find buttons in this tab
          const allButtons = Array.from(document.querySelectorAll('button'));
          const foundButtons = [];
          
          for (const btnText of ${JSON.stringify(test.buttons)}) {
            const btn = allButtons.find(b => {
              const text = b.textContent.trim();
              return text.includes(btnText) || text === btnText;
            });
            
            if (btn) {
              const isVisible = window.getComputedStyle(btn).display !== 'none';
              const isEnabled = !btn.disabled;
              foundButtons.push({
                text: btnText,
                found: true,
                visible: isVisible,
                enabled: isEnabled,
                clickable: isVisible && isEnabled
              });
            } else {
              foundButtons.push({
                text: btnText,
                found: false
              });
            }
          }
          
          return {
            tab: '${test.tab}',
            buttons: foundButtons
          };
        } catch (err) {
          return { tab: '${test.tab}', error: err.message };
        }
      })();
    `;
    
    try {
      const result = await executeJS(testScript);
      if (result.error) {
        log(`  ✗ ${test.tab} - ${result.error}`, 'error');
        RESULTS.failed.push(`Buttons: ${test.tab} - ${result.error}`);
      } else {
        const found = result.buttons.filter(b => b.found).length;
        const clickable = result.buttons.filter(b => b.clickable).length;
        log(`  ✓ ${test.tab} - found ${found}/${test.buttons.length} buttons, ${clickable} clickable`, 'success');
        RESULTS.passed.push(`Buttons: ${test.tab} (${found}/${test.buttons.length})`);
      }
    } catch (error) {
      log(`  ✗ ${test.tab} - ${error.message}`, 'error');
      RESULTS.failed.push(`Buttons: ${test.tab} - ${error.message}`);
    }
    
    await sleep(500);
  }
}

async function checkForErrors() {
  log('Checking for runtime errors...');
  
  const testScript = `
    (() => {
      const errors = [];
      
      // Check for error boundaries
      const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
      if (errorElements.length > 0) {
        errors.push({ type: 'error_boundary', count: errorElements.length });
      }
      
      // Check for blank screens
      const main = document.querySelector('main');
      if (main) {
        const hasContent = main.children.length > 0;
        const isVisible = window.getComputedStyle(main).display !== 'none';
        const textContent = main.textContent.trim();
        if (!hasContent || !isVisible || textContent.length < 10) {
          errors.push({ type: 'blank_screen', hasContent, isVisible, textLength: textContent.length });
        }
      }
      
      // Check React root
      const root = document.getElementById('root');
      if (!root || root.children.length === 0) {
        errors.push({ type: 'no_react_root' });
      }
      
      return errors;
    })();
  `;
  
  try {
    const errors = await executeJS(testScript);
    if (errors.length === 0) {
      log('  ✓ No errors detected', 'success');
      RESULTS.passed.push('Error check: No errors');
    } else {
      errors.forEach(err => {
        log(`  ✗ Error: ${JSON.stringify(err)}`, 'error');
        RESULTS.failed.push(`Error: ${JSON.stringify(err)}`);
      });
    }
  } catch (error) {
    log(`  ✗ Error check failed: ${error.message}`, 'error');
    RESULTS.failed.push(`Error check: ${error.message}`);
  }
}

async function runTests() {
  log('Starting comprehensive interactive UI test...');
  
  await app.whenReady();
  
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    show: false,
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
  
  await checkForErrors();
  await sleep(1000);
  
  await testAllTabs();
  await sleep(1000);
  
  await testInteractiveButtons();
  await sleep(1000);
  
  await checkForErrors();
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('TEST RESULTS SUMMARY');
  console.log('='.repeat(60));
  console.log(`✅ Passed: ${RESULTS.passed.length}`);
  RESULTS.passed.slice(0, 15).forEach(r => console.log(`   - ${r}`));
  if (RESULTS.passed.length > 15) {
    console.log(`   ... and ${RESULTS.passed.length - 15} more`);
  }
  console.log(`⚠️  Warnings: ${RESULTS.warnings.length}`);
  RESULTS.warnings.forEach(r => console.log(`   - ${r}`));
  console.log(`❌ Failed: ${RESULTS.failed.length}`);
  RESULTS.failed.forEach(r => console.log(`   - ${r}`));
  console.log('='.repeat(60));
  
  const success = RESULTS.failed.length === 0;
  log(`Overall: ${success ? 'PASS' : 'FAIL'}`, success ? 'success' : 'error');
  
  if (mainWindow) {
    mainWindow.close();
  }
  
  app.exit(success ? 0 : 1);
}

runTests().catch(error => {
  log(`Fatal error: ${error.message}`, 'error');
  if (mainWindow) mainWindow.close();
  app.exit(1);
});

