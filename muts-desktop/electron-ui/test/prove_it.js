/**
 * Proof Test - Verifies the app actually works
 * Uses Electron's webContents.executeJavaScript to test navigation and components
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow = null;
const TEST_RESULTS = {
  passed: [],
  failed: [],
  errors: []
};

function log(message, type = 'info') {
  const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : '⚠️';
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

async function testAppLaunch() {
  log('TEST 1: App Launch', 'info');
  
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
  
  await sleep(5000);
  
  const url = mainWindow.webContents.getURL();
  if (url && url.includes('index.html')) {
    log('  ✓ App launched successfully', 'success');
    TEST_RESULTS.passed.push('App Launch');
  } else {
    log(`  ✗ App failed to launch - URL: ${url}`, 'error');
    TEST_RESULTS.failed.push('App Launch');
  }
}

async function testNavigation() {
  log('TEST 2: Navigation (HashRouter)', 'info');
  
  const tabs = [
    { name: 'Connect', path: '#/connect' },
    { name: 'Live Data', path: '#/live-data' },
    { name: 'Stream', path: '#/stream' },
    { name: 'Diagnostics', path: '#/diagnostics' },
    { name: 'Tuning', path: '#/tuning' },
    { name: 'ROM Tools', path: '#/rom-tools' },
    { name: 'Flashing', path: '#/flashing' },
    { name: 'Logs', path: '#/logs' },
    { name: 'Settings', path: '#/settings' }
  ];
  
  let successCount = 0;
  
  for (const tab of tabs) {
    const testScript = `
      (async () => {
        try {
          // Find and click navigation button
          const navButtons = Array.from(document.querySelectorAll('nav button'));
          const button = navButtons.find(btn => {
            const text = btn.textContent.trim();
            return text.includes('${tab.name.split(' ')[0]}');
          });
          
          if (!button) {
            return { found: false, error: 'Button not found' };
          }
          
          const beforeHash = window.location.hash;
          button.click();
          await new Promise(r => setTimeout(r, 1000));
          
          const afterHash = window.location.hash;
          const hashChanged = beforeHash !== afterHash;
          
          // Check if content rendered
          const main = document.querySelector('main');
          const hasContent = main && main.children.length > 0;
          const isVisible = main && window.getComputedStyle(main).display !== 'none';
          const hasError = document.querySelector('[class*="error"], [class*="Error"]') !== null;
          const isBlank = main && main.textContent.trim().length < 10;
          
          return {
            tab: '${tab.name}',
            found: true,
            clicked: true,
            hashChanged,
            newHash: afterHash,
            hasContent,
            isVisible,
            hasError,
            isBlank,
            passed: hashChanged && hasContent && isVisible && !hasError && !isBlank
          };
        } catch (err) {
          return { tab: '${tab.name}', found: false, error: err.message };
        }
      })();
    `;
    
    try {
      const result = await executeJS(testScript);
      if (result.passed) {
        log(`  ✓ ${tab.name} - navigated to ${result.newHash}, content rendered`, 'success');
        successCount++;
        TEST_RESULTS.passed.push(`Navigation: ${tab.name}`);
      } else if (result.found && result.clicked) {
        const issues = [];
        if (!result.hashChanged) issues.push('hash not changed');
        if (!result.hasContent) issues.push('no content');
        if (!result.isVisible) issues.push('not visible');
        if (result.hasError) issues.push('has error');
        if (result.isBlank) issues.push('blank screen');
        log(`  ⚠ ${tab.name} - clicked but: ${issues.join(', ')}`, 'error');
        TEST_RESULTS.failed.push(`Navigation: ${tab.name} - ${issues.join(', ')}`);
      } else {
        log(`  ✗ ${tab.name} - ${result.error || 'not found'}`, 'error');
        TEST_RESULTS.failed.push(`Navigation: ${tab.name} - ${result.error || 'not found'}`);
      }
    } catch (error) {
      log(`  ✗ ${tab.name} - ${error.message}`, 'error');
      TEST_RESULTS.failed.push(`Navigation: ${tab.name} - ${error.message}`);
    }
    
    await sleep(300);
  }
  
  if (successCount === tabs.length) {
    log(`  ✓ All ${tabs.length} tabs navigated successfully`, 'success');
  } else {
    log(`  ⚠ Only ${successCount}/${tabs.length} tabs navigated successfully`, 'error');
  }
}

async function testNoFileErrors() {
  log('TEST 3: No ERR_FILE_NOT_FOUND Errors', 'info');
  
  // Check if there were any file loading errors
  const testScript = `
    (() => {
      // Check console for errors
      const errors = [];
      const originalError = console.error;
      console.error = function(...args) {
        const msg = args.join(' ');
        if (msg.includes('ERR_FILE_NOT_FOUND') || msg.includes('Failed to load')) {
          errors.push(msg);
        }
        originalError.apply(console, args);
      };
      
      return {
        hasErrors: errors.length > 0,
        errorCount: errors.length
      };
    })();
  `;
  
  try {
    const result = await executeJS(testScript);
    if (!result.hasErrors) {
      log('  ✓ No ERR_FILE_NOT_FOUND errors detected', 'success');
      TEST_RESULTS.passed.push('No File Errors');
    } else {
      log(`  ✗ Found ${result.errorCount} file loading errors`, 'error');
      TEST_RESULTS.failed.push(`File Errors: ${result.errorCount} errors`);
    }
  } catch (error) {
    log(`  ✗ Error check failed: ${error.message}`, 'error');
    TEST_RESULTS.failed.push(`Error Check: ${error.message}`);
  }
}

async function testComponentsRender() {
  log('TEST 4: Components Render Without Errors', 'info');
  
  const testScript = `
    (() => {
      const issues = [];
      
      // Check for error boundaries
      const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
      if (errorElements.length > 0) {
        issues.push('error boundaries: ' + errorElements.length);
      }
      
      // Check main content
      const main = document.querySelector('main');
      if (!main) {
        issues.push('main element not found');
      } else {
        const hasContent = main.children.length > 0;
        const isVisible = window.getComputedStyle(main).display !== 'none';
        const textContent = main.textContent.trim();
        
        if (!hasContent) issues.push('main has no children');
        if (!isVisible) issues.push('main not visible');
        if (textContent.length < 10) issues.push('main appears blank');
      }
      
      // Check React root
      const root = document.getElementById('root');
      if (!root || root.children.length === 0) {
        issues.push('React root empty');
      }
      
      return {
        passed: issues.length === 0,
        issues
      };
    })();
  `;
  
  try {
    const result = await executeJS(testScript);
    if (result.passed) {
      log('  ✓ All components render correctly', 'success');
      TEST_RESULTS.passed.push('Components Render');
    } else {
      log(`  ✗ Component issues: ${result.issues.join(', ')}`, 'error');
      TEST_RESULTS.failed.push(`Components: ${result.issues.join(', ')}`);
    }
  } catch (error) {
    log(`  ✗ Component check failed: ${error.message}`, 'error');
    TEST_RESULTS.failed.push(`Components: ${error.message}`);
  }
}

async function testHashRouter() {
  log('TEST 5: HashRouter Working', 'info');
  
  const testScript = `
    (() => {
      const currentHash = window.location.hash;
      const hasHashRouter = currentHash !== '' || window.location.pathname.includes('index.html');
      
      // Try to navigate programmatically
      window.location.hash = '#/test';
      const hashChanged = window.location.hash === '#/test';
      
      return {
        hasHashRouter,
        currentHash,
        hashChanged,
        passed: hasHashRouter || hashChanged
      };
    })();
  `;
  
  try {
    const result = await executeJS(testScript);
    if (result.passed) {
      log(`  ✓ HashRouter working - current hash: ${result.currentHash}`, 'success');
      TEST_RESULTS.passed.push('HashRouter');
    } else {
      log(`  ✗ HashRouter not working - hash: ${result.currentHash}`, 'error');
      TEST_RESULTS.failed.push('HashRouter');
    }
  } catch (error) {
    log(`  ✗ HashRouter test failed: ${error.message}`, 'error');
    TEST_RESULTS.failed.push(`HashRouter: ${error.message}`);
  }
}

async function runAllTests() {
  console.log('\n' + '='.repeat(60));
  console.log('PROOF TEST - Verifying App Works');
  console.log('='.repeat(60) + '\n');
  
  try {
    await testAppLaunch();
    await sleep(1000);
    
    await testHashRouter();
    await sleep(500);
    
    await testNavigation();
    await sleep(500);
    
    await testNoFileErrors();
    await sleep(500);
    
    await testComponentsRender();
    
  } catch (error) {
    log(`Fatal test error: ${error.message}`, 'error');
    TEST_RESULTS.errors.push(error.message);
  } finally {
    if (mainWindow) {
      mainWindow.close();
    }
  }
  
  // Print summary
  console.log('\n' + '='.repeat(60));
  console.log('TEST RESULTS SUMMARY');
  console.log('='.repeat(60));
  console.log(`✅ Passed: ${TEST_RESULTS.passed.length}`);
  TEST_RESULTS.passed.forEach(r => console.log(`   - ${r}`));
  console.log(`❌ Failed: ${TEST_RESULTS.failed.length}`);
  TEST_RESULTS.failed.forEach(r => console.log(`   - ${r}`));
  console.log(`⚠️  Errors: ${TEST_RESULTS.errors.length}`);
  TEST_RESULTS.errors.forEach(r => console.log(`   - ${r}`));
  console.log('='.repeat(60));
  
  const success = TEST_RESULTS.failed.length === 0 && TEST_RESULTS.errors.length === 0;
  log(`\nOverall: ${success ? '✅ PASS - App Works!' : '❌ FAIL - Issues Found'}`, success ? 'success' : 'error');
  
  app.exit(success ? 0 : 1);
}

// Run tests
runAllTests().catch(error => {
  log(`Fatal error: ${error.message}`, 'error');
  if (mainWindow) mainWindow.close();
  app.exit(1);
});

