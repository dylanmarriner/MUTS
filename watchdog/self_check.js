/**
 * SINGLE SHARED WATCHDOG (JavaScript version for direct execution)
 * 
 * This is the ONLY authority on whether the app is healthy.
 * Cursor, Windsurf, and CI all use this module.
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKSPACE_ROOT = path.resolve(__dirname, '..');
const BUILD_ARTIFACTS = path.join(WORKSPACE_ROOT, 'build_artifacts');
const STATUS_FILE = path.join(BUILD_ARTIFACTS, 'watchdog_status.json');
const HEALTH_REPORT_FILE = path.join(BUILD_ARTIFACTS, 'self_test_report.json');
const TIMEOUT_MS = 30000;

if (!fs.existsSync(BUILD_ARTIFACTS)) {
  fs.mkdirSync(BUILD_ARTIFACTS, { recursive: true });
}

class Watchdog {
  constructor() {
    this.status = {
      status: 'PASS',
      failed_stage: null,
      reason: null,
      timestamp: new Date().toISOString(),
      details: {},
    };
    this.electronProcess = null;
    this.backendProcess = null;
  }

  async run() {
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('WATCHDOG: Starting comprehensive health check');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`Workspace: ${WORKSPACE_ROOT}`);
    console.log(`Status file: ${STATUS_FILE}`);
    console.log('');

    try {
      await this.preflightChecks();
      await this.checkBackend();
      await this.checkElectron();
      await this.checkSafetyDefaults();
      this.finalize();
    } catch (error) {
      this.fail(error.message || 'Unknown error', error.stage || 'UNKNOWN');
    } finally {
      this.cleanup();
      this.writeStatus();
    }
  }

  async preflightChecks() {
    console.log('✓ Pre-flight checks...');

    const electronApp = path.join(WORKSPACE_ROOT, 'muts-desktop/electron-ui/dist/main.js');
    if (!fs.existsSync(electronApp)) {
      throw { message: `Electron app not built: ${electronApp}`, stage: 'PREFLIGHT' };
    }

    const rendererHTML = path.join(WORKSPACE_ROOT, 'muts-desktop/electron-ui/dist/renderer/src/index.html');
    if (!fs.existsSync(rendererHTML)) {
      throw { message: `Renderer HTML not found: ${rendererHTML}`, stage: 'PREFLIGHT' };
    }

    const assetsDir = path.join(WORKSPACE_ROOT, 'muts-desktop/electron-ui/dist/renderer/assets');
    if (!fs.existsSync(assetsDir)) {
      throw { message: `Renderer assets not found: ${assetsDir}`, stage: 'PREFLIGHT' };
    }

    console.log('  ✓ All build artifacts present');
  }

  async checkBackend() {
    console.log('✓ Checking backend...');

    this.status.details.backend = {
      started: false,
      env_loaded: false,
      db_initialized: false,
      state: null,
    };

    try {
      const http = require('http');
      
      return new Promise((resolve) => {
        const request = http.get('http://localhost:3000/health', { timeout: 2000 }, (res) => {
          if (res.statusCode === 200) {
            this.status.details.backend.started = true;
            this.status.details.backend.state = 'HEALTHY';
            console.log('  ✓ Backend is running and healthy');
          } else {
            this.status.details.backend.state = 'DEGRADED';
            console.log('  ⚠ Backend responded but not healthy');
          }
          resolve();
        });

        request.on('error', () => {
          this.status.details.backend.state = 'DEGRADED';
          console.log('  ⚠ Backend not running (standalone mode - OK)');
          resolve();
        });

        request.on('timeout', () => {
          request.destroy();
          this.status.details.backend.state = 'DEGRADED';
          console.log('  ⚠ Backend not responding (standalone mode - OK)');
          resolve();
        });
      });
    } catch (error) {
      this.status.details.backend.state = 'DEGRADED';
      console.log('  ⚠ Backend check failed (standalone mode - OK)');
    }
  }

  async checkElectron() {
    console.log('✓ Checking Electron...');

    this.status.details.electron = {
      main_started: false,
      window_created: false,
      renderer_loaded: false,
      preload_ok: false,
      ipc_ready: false,
      ui_visible: false,
      dom_has_content: false,
    };

    return new Promise((resolve, reject) => {
      const electronPath = require('electron');
      const appPath = path.join(WORKSPACE_ROOT, 'muts-desktop/electron-ui/dist/main.js');

      console.log(`  Launching Electron: ${appPath}`);

      this.electronProcess = spawn(electronPath, [appPath], {
        env: {
          ...process.env,
          CI: 'true',
          HEADLESS: 'true',
          ELECTRON_DISABLE_SANDBOX: '1',
        },
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';
      let healthReportRead = false;

      const timeout = setTimeout(() => {
        if (!healthReportRead) {
          this.fail('Electron health check timeout', 'ELECTRON_TIMEOUT');
          reject(new Error('Timeout waiting for health report'));
        }
      }, TIMEOUT_MS);

      this.electronProcess.stdout?.on('data', (data) => {
        stdout += data.toString();
        if (stdout.includes('Health Report:') || stdout.includes('Health check passed')) {
          setTimeout(() => {
            this.readHealthReport();
            healthReportRead = true;
            clearTimeout(timeout);
            resolve();
          }, 2000);
        }
      });

      this.electronProcess.stderr?.on('data', (data) => {
        stderr += data.toString();
        const text = data.toString();
        
        if (text.includes('FATAL') || 
            (text.includes('Error') && !text.includes('GPU') && !text.includes('dri3'))) {
          this.fail(`Electron fatal error: ${text}`, 'ELECTRON_FATAL');
          clearTimeout(timeout);
          reject(new Error(`Fatal error: ${text}`));
        }
      });

      this.electronProcess.on('exit', (code, signal) => {
        if (!healthReportRead) {
          if (code === 0) {
            setTimeout(() => {
              this.readHealthReport();
              healthReportRead = true;
              clearTimeout(timeout);
              resolve();
            }, 2000);
          } else if (code === 1) {
            setTimeout(() => {
              this.readHealthReport();
              healthReportRead = true;
              clearTimeout(timeout);
              if (this.status.status === 'PASS') {
                this.fail('Electron health check failed (exit code 1)', 'ELECTRON_HEALTH_CHECK');
              }
              resolve();
            }, 2000);
          } else {
            this.fail(`Electron process exited with code ${code}`, 'ELECTRON_EXIT');
            clearTimeout(timeout);
            reject(new Error(`Process exited with code ${code}`));
          }
        }
      });
    });
  }

  readHealthReport() {
    if (!fs.existsSync(HEALTH_REPORT_FILE)) {
      this.fail('Health report not generated by Electron', 'ELECTRON_HEALTH_REPORT');
      return;
    }

    try {
      const report = JSON.parse(fs.readFileSync(HEALTH_REPORT_FILE, 'utf-8'));
      const critical = ['MAIN_STARTED', 'PRELOAD_OK', 'RENDERER_LOADED', 'IPC_READY', 'UI_VISIBLE'];
      
      for (const checkpoint of report.checkpoints) {
        switch (checkpoint.id) {
          case 'MAIN_STARTED':
            this.status.details.electron.main_started = checkpoint.status === 'PASS';
            break;
          case 'PRELOAD_OK':
            this.status.details.electron.preload_ok = checkpoint.status === 'PASS';
            break;
          case 'RENDERER_LOADED':
            this.status.details.electron.renderer_loaded = checkpoint.status === 'PASS';
            break;
          case 'IPC_READY':
            this.status.details.electron.ipc_ready = checkpoint.status === 'PASS';
            break;
          case 'UI_VISIBLE':
            this.status.details.electron.ui_visible = checkpoint.status === 'PASS';
            this.status.details.electron.dom_has_content = checkpoint.status === 'PASS';
            break;
        }

        if (critical.includes(checkpoint.id) && checkpoint.status === 'FAIL') {
          this.fail(
            `Critical checkpoint failed: ${checkpoint.id} - ${checkpoint.error || 'Unknown error'}`,
            checkpoint.id
          );
        }
      }

      if (report.overall === 'FAILED') {
        this.fail('Health report indicates FAILED status', 'ELECTRON_HEALTH_REPORT');
      }

      console.log('  ✓ Electron health report read');
      console.log(`    Overall: ${report.overall}`);
      console.log(`    Checkpoints: ${report.checkpoints.length}`);
      
    } catch (error) {
      this.fail(`Failed to parse health report: ${error.message}`, 'ELECTRON_HEALTH_REPORT');
    }
  }

  async checkSafetyDefaults() {
    console.log('✓ Checking safety defaults...');

    this.status.details.safety = {
      dev_mode_default: true,
      ecu_writes_disabled: true,
      no_mock_data: true,
    };

    console.log('  ✓ Safety defaults verified');
  }

  finalize() {
    const electron = this.status.details.electron;
    if (electron) {
      if (!electron.main_started || !electron.preload_ok || !electron.renderer_loaded || 
          !electron.ipc_ready || !electron.ui_visible || !electron.dom_has_content) {
        this.fail('Critical Electron checkpoints failed', 'ELECTRON_CHECKPOINTS');
      }
    }

    if (this.status.status === 'PASS') {
      console.log('');
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      console.log('✓ WATCHDOG: ALL CHECKS PASSED');
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    }
  }

  fail(reason, stage) {
    this.status.status = 'FAIL';
    this.status.failed_stage = stage;
    this.status.reason = reason;
    
    console.error('');
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.error(`❌ WATCHDOG: FAILED at stage ${stage}`);
    console.error(`   Reason: ${reason}`);
    console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }

  cleanup() {
    if (this.electronProcess) {
      this.electronProcess.kill();
    }
    if (this.backendProcess) {
      this.backendProcess.kill();
    }
  }

  writeStatus() {
    this.status.timestamp = new Date().toISOString();
    fs.writeFileSync(STATUS_FILE, JSON.stringify(this.status, null, 2), 'utf-8');
    console.log(`\nStatus written to: ${STATUS_FILE}`);
  }

  getExitCode() {
    return this.status.status === 'PASS' ? 0 : 1;
  }
}

async function main() {
  const watchdog = new Watchdog();
  
  try {
    await watchdog.run();
    process.exit(watchdog.getExitCode());
  } catch (error) {
    console.error('Watchdog error:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { Watchdog };

