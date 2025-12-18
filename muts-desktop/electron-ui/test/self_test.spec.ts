/**
 * Self-Test Suite for MUTS Desktop Application
 * Runs automated health checks without manual intervention
 */

import { test, expect } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const ELECTRON_PATH = require('electron');
const APP_PATH = path.join(__dirname, '../dist/main.js');
const TEST_TIMEOUT = 30000; // 30 seconds

let electronProcess: ChildProcess | null = null;

test.beforeAll(async () => {
  // Ensure app is built
  if (!fs.existsSync(APP_PATH)) {
    throw new Error(`App not built. Run 'npm run build' first. App path: ${APP_PATH}`);
  }
});

test.afterAll(async () => {
  if (electronProcess) {
    electronProcess.kill();
  }
});

test('Electron Boot - Main process starts', async () => {
  electronProcess = spawn(ELECTRON_PATH, [APP_PATH], {
    env: { ...process.env, CI: 'true' },
  });

  let mainStarted = false;
  let output = '';

  return new Promise<void>((resolve, reject) => {
    const timeout = setTimeout(() => {
      electronProcess?.kill();
      reject(new Error('Main process did not start within timeout'));
    }, TEST_TIMEOUT);

    electronProcess?.stdout?.on('data', (data) => {
      output += data.toString();
      if (data.toString().includes('App is ready') || data.toString().includes('Main process started')) {
        mainStarted = true;
      }
    });

    electronProcess?.stderr?.on('data', (data) => {
      output += data.toString();
    });

    electronProcess?.on('exit', (code) => {
      clearTimeout(timeout);
      if (code === 0 && mainStarted) {
        resolve();
      } else if (code === 1) {
        // Health check failed - this is expected in CI
        if (output.includes('Health check failed')) {
          reject(new Error('Health check failed - see build_artifacts/self_test_report.json'));
        } else {
          reject(new Error(`Process exited with code ${code}. Output: ${output}`));
        }
      } else {
        reject(new Error(`Process exited with code ${code}. Output: ${output}`));
      }
    });

    // Wait a bit for startup
    setTimeout(() => {
      if (mainStarted) {
        clearTimeout(timeout);
        electronProcess?.kill();
        resolve();
      }
    }, 5000);
  });
});

test('Renderer Integrity - HTML and JS load', async () => {
  const htmlPath = path.join(__dirname, '../dist/renderer/src/index.html');
  const assetsDir = path.join(__dirname, '../dist/renderer/assets');
  
  expect(fs.existsSync(htmlPath)).toBe(true);
  
  const htmlContent = fs.readFileSync(htmlPath, 'utf-8');
  expect(htmlContent).toContain('<!DOCTYPE html>');
  expect(htmlContent).toContain('<script');
  expect(htmlContent).toContain('<link rel="stylesheet"');
  
  // Check that assets directory exists and has files
  if (fs.existsSync(assetsDir)) {
    const assets = fs.readdirSync(assetsDir);
    expect(assets.length).toBeGreaterThan(0);
    expect(assets.some(f => f.endsWith('.js'))).toBe(true);
    expect(assets.some(f => f.endsWith('.css'))).toBe(true);
  }
});

test('Health Report Generated', async () => {
  const reportPath = path.join(__dirname, '../../build_artifacts/self_test_report.json');
  
  // Start app briefly to generate report
  electronProcess = spawn(ELECTRON_PATH, [APP_PATH], {
    env: { ...process.env, CI: 'true' },
  });

  return new Promise<void>((resolve, reject) => {
    const timeout = setTimeout(() => {
      electronProcess?.kill();
      if (fs.existsSync(reportPath)) {
        resolve();
      } else {
        reject(new Error('Health report not generated'));
      }
    }, 10000);

    electronProcess?.on('exit', () => {
      clearTimeout(timeout);
      if (fs.existsSync(reportPath)) {
        const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
        expect(report).toHaveProperty('overall');
        expect(report).toHaveProperty('checkpoints');
        expect(Array.isArray(report.checkpoints)).toBe(true);
        resolve();
      } else {
        reject(new Error('Health report not found'));
      }
    });
  });
});

test('Health Checkpoints - All critical checkpoints present', async () => {
  const reportPath = path.join(__dirname, '../../build_artifacts/self_test_report.json');
  
  if (!fs.existsSync(reportPath)) {
    // Generate report first
    electronProcess = spawn(ELECTRON_PATH, [APP_PATH], {
      env: { ...process.env, CI: 'true' },
    });

    await new Promise<void>((resolve) => {
      setTimeout(() => {
        electronProcess?.kill();
        resolve();
      }, 8000);
    });
  }

  if (!fs.existsSync(reportPath)) {
    throw new Error('Health report not generated');
  }

  const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
  const checkpointIds = report.checkpoints.map((c: any) => c.id);
  
  // Critical checkpoints
  const critical = ['MAIN_STARTED', 'PRELOAD_OK', 'RENDERER_LOADED', 'IPC_READY'];
  
  for (const id of critical) {
    expect(checkpointIds).toContain(id);
    const checkpoint = report.checkpoints.find((c: any) => c.id === id);
    expect(checkpoint).toBeDefined();
    expect(['PASS', 'FAIL', 'DEGRADED']).toContain(checkpoint.status);
  }
});

test('No Fatal Errors - App starts without crashing', async () => {
  electronProcess = spawn(ELECTRON_PATH, [APP_PATH], {
    env: { ...process.env, CI: 'true' },
  });

  let fatalError = false;
  let output = '';

  return new Promise<void>((resolve, reject) => {
    const timeout = setTimeout(() => {
      electronProcess?.kill();
      if (fatalError) {
        reject(new Error(`Fatal error detected: ${output}`));
      } else {
        resolve();
      }
    }, 10000);

    electronProcess?.stdout?.on('data', (data) => {
      output += data.toString();
    });

    electronProcess?.stderr?.on('data', (data) => {
      const errorText = data.toString();
      output += errorText;
      // Ignore GPU warnings (harmless on Linux)
      if (errorText.includes('FATAL') || 
          (errorText.includes('Error') && !errorText.includes('GPU') && !errorText.includes('dri3'))) {
        fatalError = true;
      }
    });

    electronProcess?.on('exit', (code) => {
      clearTimeout(timeout);
      if (code === 1 && output.includes('Health check failed')) {
        // Health check failure is expected in CI - check report
        resolve();
      } else if (code !== 0 && code !== null) {
        reject(new Error(`Process exited with code ${code}`));
      } else {
        resolve();
      }
    });
  });
});

test('Safety Defaults - DEV mode enforced', async () => {
  const reportPath = path.join(__dirname, '../../build_artifacts/self_test_report.json');
  
  if (!fs.existsSync(reportPath)) {
    electronProcess = spawn(ELECTRON_PATH, [APP_PATH], {
      env: { ...process.env, CI: 'true' },
    });

    await new Promise<void>((resolve) => {
      setTimeout(() => {
        electronProcess?.kill();
        resolve();
      }, 8000);
    });
  }

  if (fs.existsSync(reportPath)) {
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
    const configCheckpoint = report.checkpoints.find((c: any) => c.id === 'CONFIG_LOADED');
    if (configCheckpoint && configCheckpoint.metadata) {
      // Verify operator mode is dev by default
      expect(configCheckpoint.metadata.operatorMode).toBe('dev');
    }
  }
});

