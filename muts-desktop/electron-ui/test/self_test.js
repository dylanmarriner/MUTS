/**
 * Self-Test Runner for MUTS Desktop Application
 * Launches Electron in headless mode and validates health checkpoints
 * 
 * FAIL FAST, FAIL LOUD - Exits with non-zero code on ANY failure
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ELECTRON_PATH = require('electron');
const APP_PATH = path.join(__dirname, '../dist/main.js');
const REPORT_PATH = path.join(__dirname, '../../build_artifacts/self_test_report.json');
const TRACE_PATH = path.join(__dirname, '../../build_artifacts/startup_trace.log');
const TEST_TIMEOUT = 20000; // 20 seconds max

// Ensure build_artifacts exists
const artifactsDir = path.dirname(REPORT_PATH);
if (!fs.existsSync(artifactsDir)) {
  fs.mkdirSync(artifactsDir, { recursive: true });
}

// Clear previous reports
if (fs.existsSync(REPORT_PATH)) {
  fs.unlinkSync(REPORT_PATH);
}
if (fs.existsSync(TRACE_PATH)) {
  fs.unlinkSync(TRACE_PATH);
}

function runSelfTest() {
  return new Promise((resolve, reject) => {
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('MUTS SELF-TEST - Starting automated health verification');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`Electron: ${ELECTRON_PATH}`);
    console.log(`App: ${APP_PATH}`);
    console.log(`Timeout: ${TEST_TIMEOUT}ms`);
    console.log('');
    
    // Pre-flight checks
    if (!fs.existsSync(APP_PATH)) {
      const error = `❌ CRITICAL: App not built. Run 'npm run build' first.\n   Missing: ${APP_PATH}`;
      console.error(error);
      reject(new Error(error));
      return;
    }

    // Check HTML file exists
    const htmlPath = path.join(__dirname, '../dist/renderer/src/index.html');
    if (!fs.existsSync(htmlPath)) {
      const error = `❌ CRITICAL: Renderer HTML not found.\n   Missing: ${htmlPath}`;
      console.error(error);
      reject(new Error(error));
      return;
    }

    // Check assets directory
    const assetsDir = path.join(__dirname, '../dist/renderer/assets');
    if (!fs.existsSync(assetsDir)) {
      const error = `❌ CRITICAL: Renderer assets not found.\n   Missing: ${assetsDir}`;
      console.error(error);
      reject(new Error(error));
      return;
    }

    console.log('✓ Pre-flight checks passed');
    console.log('Launching Electron in headless mode...\n');

    const electronProcess = spawn(ELECTRON_PATH, [APP_PATH], {
      env: { 
        ...process.env, 
        CI: 'true',
        ELECTRON_DISABLE_SANDBOX: '1', // Allow headless operation
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';
    let exited = false;
    let fatalError = false;

    const timeout = setTimeout(() => {
      if (!exited) {
        console.error('\n❌ TIMEOUT: Test exceeded maximum duration');
        console.error(`   Timeout: ${TEST_TIMEOUT}ms`);
        fatalError = true;
        electronProcess.kill('SIGKILL');
        checkResults(-1, 'TIMEOUT');
      }
    }, TEST_TIMEOUT);

    electronProcess.stdout.on('data', (data) => {
      stdout += data.toString();
      // Only show important output
      const text = data.toString();
      if (text.includes('ERROR') || text.includes('FAILED') || text.includes('Health check failed')) {
        process.stdout.write(data);
      }
    });

    electronProcess.stderr.on('data', (data) => {
      stderr += data.toString();
      const text = data.toString();
      
      // Check for fatal errors (not GPU warnings)
      if (text.includes('FATAL') || 
          (text.includes('Error') && !text.includes('GPU') && !text.includes('dri3') && !text.includes('viz_main_impl'))) {
        fatalError = true;
        process.stderr.write(`❌ FATAL ERROR: ${text}`);
      }
    });

    electronProcess.on('exit', (code, signal) => {
      exited = true;
      clearTimeout(timeout);
      
      if (code === null) {
        console.error(`\n❌ Process terminated by signal: ${signal}`);
      } else if (code !== 0 && code !== 1) {
        // Code 1 is expected if health check fails, but other codes are errors
        fatalError = true;
        console.error(`\n❌ Process exited with unexpected code: ${code}`);
      }
      
      checkResults(code || -1, signal);
    });

    function checkResults(exitCode, signal) {
      // Wait for report to be written
      setTimeout(() => {
        // Check for fatal errors first
        if (fatalError) {
          console.error('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.error('❌ SELF-TEST FAILED - FATAL ERROR DETECTED');
          console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          if (stderr) {
            console.error('\nSTDERR Output:');
            console.error(stderr);
          }
          reject(new Error('Fatal error during startup'));
          return;
        }

        if (!fs.existsSync(REPORT_PATH)) {
          console.error('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.error('❌ SELF-TEST FAILED - Health report not generated');
          console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.error(`   Expected: ${REPORT_PATH}`);
          console.error('   This indicates the app failed before health probes could run.');
          if (stderr) {
            console.error('\nSTDERR Output:');
            console.error(stderr);
          }
          reject(new Error('Health report not found - app may have crashed'));
          return;
        }

        let report;
        try {
          report = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf-8'));
        } catch (parseError) {
          console.error('\n❌ Failed to parse health report:', parseError.message);
          reject(new Error('Invalid health report format'));
          return;
        }
        
        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('SELF-TEST RESULTS');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log(`Overall Status: ${report.overall}`);
        console.log(`Startup Time: ${((report.endTime - report.startTime) / 1000).toFixed(2)}s`);
        console.log(`Checkpoints: ${report.checkpoints.length}`);
        console.log(`Errors: ${report.errors.length}`);
        console.log(`Warnings: ${report.warnings.length}`);
        console.log('');
        
        // Critical checkpoints that MUST pass
        const critical = [
          'MAIN_STARTED',
          'PRELOAD_OK', 
          'RENDERER_LOADED', 
          'IPC_READY', 
          'UI_VISIBLE'
        ];
        
        let allCriticalPassed = true;
        const failedCheckpoints = [];

        console.log('Checkpoint Status:');
        for (const checkpoint of report.checkpoints) {
          const isCritical = critical.includes(checkpoint.id);
          const icon = checkpoint.status === 'PASS' ? '✓' : 
                      checkpoint.status === 'DEGRADED' ? '⚠' : '✗';
          const marker = isCritical ? '🔴' : '  ';
          const statusColor = checkpoint.status === 'PASS' ? '' : 
                             checkpoint.status === 'DEGRADED' ? '⚠' : '❌';
          
          console.log(`  ${icon} ${marker} ${checkpoint.id}: ${checkpoint.name}`);
          console.log(`      Status: ${statusColor} ${checkpoint.status}`);
          
          if (checkpoint.error) {
            console.log(`      Error: ${checkpoint.error}`);
            if (checkpoint.metadata) {
              console.log(`      Metadata: ${JSON.stringify(checkpoint.metadata)}`);
            }
          }
          
          if (isCritical && checkpoint.status !== 'PASS') {
            allCriticalPassed = false;
            failedCheckpoints.push({
              id: checkpoint.id,
              name: checkpoint.name,
              error: checkpoint.error || 'Unknown error'
            });
          }
        }

        if (report.errors.length > 0) {
          console.log('\n❌ Errors:');
          report.errors.forEach(err => console.log(`  • ${err}`));
        }

        if (report.warnings.length > 0) {
          console.log('\n⚠ Warnings:');
          report.warnings.forEach(warn => console.log(`  • ${warn}`));
        }

        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

        // FAIL FAST, FAIL LOUD
        if (report.overall === 'FAILED' || !allCriticalPassed) {
          console.error('\n❌ SELF-TEST FAILED');
          console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.error('Critical checkpoints did not pass:');
          failedCheckpoints.forEach(cp => {
            console.error(`  ❌ ${cp.id}: ${cp.name}`);
            console.error(`     ${cp.error}`);
          });
          console.error('\nFull report:', REPORT_PATH);
          if (fs.existsSync(TRACE_PATH)) {
            console.error('Trace log:', TRACE_PATH);
          }
          console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          reject(new Error(`Self-test failed: ${failedCheckpoints.map(cp => cp.id).join(', ')}`));
        } else if (report.overall === 'DEGRADED') {
          console.warn('\n⚠ SELF-TEST PASSED WITH WARNINGS');
          console.warn('Some non-critical systems are degraded. See report:', REPORT_PATH);
          resolve(report);
        } else {
          console.log('\n✓ SELF-TEST PASSED');
          console.log('All critical systems operational.');
          resolve(report);
        }
      }, 2500); // Increased wait time for report generation
    }
  });
}

// Run if called directly
if (require.main === module) {
  runSelfTest()
    .then(() => {
      process.exit(0);
    })
    .catch((error) => {
      console.error('Self-test failed:', error.message);
      process.exit(1);
    });
}

module.exports = { runSelfTest };

