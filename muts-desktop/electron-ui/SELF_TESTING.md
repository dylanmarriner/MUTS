# Self-Testing and Self-Debugging System

## Overview

The MUTS desktop application includes an automated self-testing and self-debugging system that validates application health on every startup without requiring manual intervention.

## Quick Start

```bash
# Run self-test (builds app first)
pnpm run self-test

# Or just test
pnpm test

# Verify in dev mode
pnpm run dev:verify
```

## Cursor Tasks Integration

The self-test is integrated into Cursor Tasks for automatic verification:

### Available Tasks

1. **Verify App (Self-Test)** - Default test task
   - Runs on demand via Cursor Tasks
   - Shows ❌ on failure with clear error messages
   - Exits with non-zero code on failure

2. **Dev Verify (Watch)** - Development verification
   - Re-runs self-test on file changes
   - Fails immediately if broken

3. **CI Verify** - CI/CD verification
   - Same as self-test but with CI environment
   - Used by GitHub Actions

### Running Tasks in Cursor

- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "Tasks: Run Task"
- Select "Verify App (Self-Test)"

Or use the keyboard shortcut if configured.

## What Gets Tested

### 1. Electron Boot
- ✅ Main process starts successfully
- ✅ BrowserWindow created
- ✅ Preload script exists and loads
- ✅ Renderer HTML file exists

### 2. Renderer Integrity
- ✅ HTML file loads
- ✅ JavaScript bundle loads
- ✅ CSS file loads
- ✅ No fatal console errors
- ✅ React renders successfully
- ✅ UI is ready (visible or headless)

### 3. IPC Wiring
- ✅ IPC handlers registered
- ✅ IPC bridge initializes
- ✅ IPC calls do not block

### 4. Backend Startup
- ✅ Backend health check (graceful failure if unavailable)
- ✅ Reports DEGRADED if backend not running (standalone mode)

### 5. Configuration
- ✅ Config loads successfully
- ✅ DEV mode enforced by default
- ✅ Safe defaults applied

## Health Checkpoints

The system tracks these checkpoints during startup:

- `MAIN_STARTED` - Main process initialization
- `PRELOAD_OK` - Preload script execution
- `RENDERER_LOADED` - Renderer HTML and scripts loaded
- `IPC_READY` - IPC handlers registered
- `UI_VISIBLE` - UI rendered (visible or headless)
- `CONFIG_LOADED` - Configuration loaded
- `BACKEND_READY` - Backend availability (DEGRADED if unavailable)
- `RUST_CORE_LOADED` - Rust core availability (optional)

## Test Reports

### Generated Files

1. **`build_artifacts/self_test_report.json`**
   - Complete health report with all checkpoints
   - Overall status (HEALTHY, DEGRADED, FAILED)
   - Errors and warnings
   - Timestamps

2. **`build_artifacts/startup_trace.log`**
   - Chronological log of all checkpoints
   - Useful for debugging startup issues

### Report Format

```json
{
  "overall": "HEALTHY",
  "startTime": 1234567890,
  "endTime": 1234567895,
  "checkpoints": [
    {
      "id": "MAIN_STARTED",
      "name": "Main process started",
      "status": "PASS",
      "timestamp": 1234567890
    }
  ],
  "errors": [],
  "warnings": []
}
```

## Running Tests

### Manual Test

```bash
cd muts-desktop/electron-ui
pnpm run self-test
```

### In CI

The self-test automatically runs in CI when `CI=true` environment variable is set. The app will:
- Run in headless mode (no window)
- Generate health report
- Exit with code 1 if health check fails
- Exit with code 0 if health check passes

### Dev Mode Verification

```bash
pnpm run dev:verify
```

This builds the app and runs the self-test, useful for verifying changes before committing.

## Error Handling

### Startup Failures

If the app fails to start:
1. Health probe records the failure
2. Error UI is shown instead of blank white screen (in non-CI mode)
3. Detailed error written to health report
4. Process exits with error code (in CI)

### Graceful Degradation

The app is designed to run in **standalone mode**:
- ✅ Works without backend
- ✅ Works without database
- ✅ Works without hardware
- ✅ Shows NOT_CONNECTED state honestly
- ✅ Reports DEGRADED (not FAILED) for optional services

## Integration with CI

Add to your CI workflow:

```yaml
- name: Run self-test
  run: |
    cd muts-desktop/electron-ui
    pnpm run self-test
```

The test will:
- Build the application
- Launch Electron in headless mode
- Validate all checkpoints
- Generate health report
- Exit with error code if failed

## Debugging Failed Tests

1. Check `build_artifacts/self_test_report.json` for detailed failure information
2. Check `build_artifacts/startup_trace.log` for chronological checkpoint log
3. Look for specific checkpoint failures
4. Verify file paths and build output

## Adding New Checkpoints

To add a new health checkpoint:

1. Add checkpoint ID to `src/utils/healthProbe.ts`:
```typescript
export const CHECKPOINTS = {
  // ... existing
  NEW_CHECKPOINT: 'NEW_CHECKPOINT',
} as const;
```

2. Report checkpoint in your code:
```typescript
// In main process
healthProbe.checkpoint(CHECKPOINTS.NEW_CHECKPOINT, 'Description', 'PASS');

// In renderer process
window.electronAPI.healthCheckpoint('NEW_CHECKPOINT', 'Description', 'PASS');
```

## Safety Defaults Verified

The self-test ensures:
- ✅ DEV mode is default (no ECU writes)
- ✅ No fake data shown as live
- ✅ NOT_CONNECTED state when no hardware
- ✅ Error UI instead of blank screen

## Limitations

- Tests run without hardware (expected)
- Backend unavailability is DEGRADED, not FAILED
- Rust core unavailability is DEGRADED, not FAILED
- GPU warnings on Linux are ignored (harmless)

## Troubleshooting

### Test fails with "App not built"
```bash
pnpm run build
pnpm run self-test
```

### Health report not generated
- Check that `build_artifacts` directory exists
- Verify app actually started (check process output)
- Increase timeout in test script if needed

### Checkpoint missing
- Verify checkpoint is reported in code
- Check IPC communication is working
- Look for errors in startup_trace.log

### Cursor Tasks not showing failures
- Ensure `.cursor/tasks.json` exists
- Check task command path is correct
- Verify problem matcher regex matches error output
