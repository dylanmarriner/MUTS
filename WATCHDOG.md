# Single Shared Watchdog

## Core Principle (NON-NEGOTIABLE)

**There is ONE authority on whether the app is healthy.**

That authority is: `/watchdog/self_check.ts` (or `self_check.js`)

- **NO IDE-specific logic**
- **NO duplicate checks**
- **NO guessing**

Cursor, Windsurf, and CI all use this same watchdog. If the watchdog says FAIL, development stops. No exceptions.

## Quick Start

```bash
# Run the watchdog
pnpm run watchdog
```

The watchdog will:
1. Build the Electron app
2. Launch Electron in headless mode
3. Check all health checkpoints
4. Write status to `/build_artifacts/watchdog_status.json`
5. Exit with code 0 (PASS) or 1 (FAIL)

## Status File

The watchdog always writes to:

`/build_artifacts/watchdog_status.json`

Format:
```json
{
  "status": "PASS | FAIL",
  "failed_stage": "string | null",
  "reason": "string | null",
  "timestamp": "ISO 8601 string",
  "details": {
    "electron": {
      "main_started": boolean,
      "window_created": boolean,
      "renderer_loaded": boolean,
      "preload_ok": boolean,
      "ipc_ready": boolean,
      "ui_visible": boolean,
      "dom_has_content": boolean
    },
    "backend": {
      "started": boolean,
      "env_loaded": boolean,
      "db_initialized": boolean,
      "state": "HEALTHY | DEGRADED | FAILED | null"
    },
    "rust_core": {
      "loaded": boolean,
      "failed_gracefully": boolean,
      "panic_detected": boolean
    },
    "safety": {
      "dev_mode_default": boolean,
      "ecu_writes_disabled": boolean,
      "no_mock_data": boolean
    }
  }
}
```

## Health Checkpoints

The watchdog validates ALL of the following:

### Electron
- ✅ Main process started
- ✅ BrowserWindow created
- ✅ Renderer HTML loaded
- ✅ Preload executed without throwing
- ✅ Renderer sent READY signal
- ✅ DOM contains visible content (not empty)

### Renderer
- ✅ index.html exists at runtime
- ✅ Renderer JS loaded
- ✅ No fatal console errors

### IPC
- ✅ IPC bridge initialized
- ✅ Required handlers registered
- ✅ No blocking IPC calls on startup

### Backend
- ✅ Backend process started (or DEGRADED if not running - OK for standalone)
- ✅ Environment loaded
- ✅ DB initialized (SQLite fallback)
- ✅ Backend state = HEALTHY or DEGRADED
- ✅ No fatal crash

### Rust Core
- ✅ Native module loads OR
- ✅ Fails gracefully with NOT_CONNECTED
- ✅ No panic or abort

### Safety
- ✅ DEV mode default
- ✅ ECU writes disabled
- ✅ No mock data presented as live

## Cursor Integration

Cursor Tasks are configured to call ONLY the watchdog:

1. **Watchdog Verify** (default test task)
   - Command: `pnpm run watchdog`
   - FAILS if watchdog exits non-zero
   - Shows error inline in Cursor

2. **Watchdog Dev (Auto)**
   - Same command
   - Runs on file change (with debounce)
   - Fails immediately if broken

Cursor NEVER runs its own checks. It only runs the watchdog.

## Windsurf Integration

**Windsurf MUST:**

1. Read `/build_artifacts/watchdog_status.json` before coding
2. If `status = "FAIL"`:
   - **STOP coding new features**
   - **Only attempt fixes related to `failed_stage`**
   - Show error message from `reason` field
3. If `status = "PASS"`:
   - Continue normally

**Example Windsurf Rule:**
```
Before implementing any feature:
1. Check /build_artifacts/watchdog_status.json
2. If status != "PASS", only fix the failed_stage
3. Never add features when watchdog says FAIL
```

## CI Integration

CI must:
1. Run `pnpm run watchdog`
2. Fail build if `status != "PASS"`
3. Upload `watchdog_status.json` as artifact

Example GitHub Actions:
```yaml
- name: Run Watchdog
  run: pnpm run watchdog

- name: Upload Watchdog Status
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: watchdog-status
    path: build_artifacts/watchdog_status.json
```

## Fail Visibly, Never Silently

The watchdog treats these as **CRITICAL FAILURES**:

- ❌ Electron launches blank (empty DOM)
- ❌ Preload throws
- ❌ Backend crashes
- ❌ White screens
- ❌ Missing critical checkpoints

**White screens are treated as CRITICAL FAILURE.**

The watchdog will:
- Print failure to stdout with clear error markers
- Write detailed failure to status file
- Exit with non-zero code

## Running the Watchdog

### Manual
```bash
pnpm run watchdog
```

### In Cursor
- Press `Ctrl+Shift+P` → "Tasks: Run Task" → "Watchdog Verify"
- Or use the default test task shortcut

### In CI
```bash
CI=true pnpm run watchdog
```

## Troubleshooting

### Watchdog fails with "Electron app not built"
```bash
pnpm run build:desktop
pnpm run watchdog
```

### Watchdog fails with "Health report not generated"
- Check that Electron actually started
- Look for errors in Electron process output
- Verify health probe is running in Electron

### Watchdog timeout
- Increase `TIMEOUT_MS` in `watchdog/self_check.js`
- Check if Electron is hanging on startup
- Verify no blocking operations in main process

### Status file not found
- Check that `build_artifacts` directory exists
- Verify watchdog completed (didn't crash)
- Check file permissions

## Architecture

```
┌─────────────────┐
│   Cursor        │
│   Windsurf      │──┐
│   CI            │  │
└─────────────────┘  │
                     │
                     ▼
         ┌───────────────────────┐
         │  /watchdog/self_check │  ← SINGLE SOURCE OF TRUTH
         └───────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                        │
         ▼                        ▼
  ┌─────────────┐        ┌──────────────┐
  │  Electron   │        │   Backend    │
  │  Health     │        │   Health     │
  │  Probe      │        │   Check      │
  └─────────────┘        └──────────────┘
         │                        │
         └───────────┬────────────┘
                     ▼
         ┌───────────────────────┐
         │ watchdog_status.json  │
         └───────────────────────┘
```

## Rules

1. **ONE watchdog** - No duplicate health checks
2. **IDE-agnostic** - No Cursor-specific or Windsurf-specific logic
3. **Fail fast** - Exit immediately on critical failure
4. **Fail loud** - Print clear error messages
5. **Never silent** - White screens are failures
6. **Status file** - Always write status, even on failure
7. **Exit codes** - 0 = PASS, non-zero = FAIL

## Adding New Checkpoints

To add a new health checkpoint:

1. Add to Electron health probe (`muts-desktop/electron-ui/src/utils/healthProbe.ts`)
2. Update watchdog to read the checkpoint (`watchdog/self_check.js`)
3. Add to watchdog status details structure
4. Document in this file

## Final Rule

**If the watchdog says FAIL, development stops.**

Cursor shows a failed task.
Windsurf stops coding.
CI fails the build.

No exceptions.

