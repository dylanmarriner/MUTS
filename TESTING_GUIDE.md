# MUTS Testing and Debugging Guide

## Overview

This guide explains how to run and debug tests in the MUTS project using the IDE (VS Code/Cursor).

## Test Configuration

### VS Code Configuration

The project includes IDE configurations in `.vscode/`:

- **`launch.json`**: Debug configurations for running tests
- **`settings.json`**: Python test settings for pytest

### Available Debug Configurations

1. **Python: Current File** - Debug the currently open Python file
2. **Python: Pytest - Current File** - Run pytest on the current test file with debugging
3. **Python: Pytest - All Tests** - Run all tests in the `tests/` directory with debugging
4. **Python: Test Core System** - Run the comprehensive core system test
5. **Python: Test Integration** - Run integration tests

## Running Tests

### From Terminal

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_live_data_service.py -v

# Run with coverage
pytest tests/ --cov=muts --cov-report=html

# Run core system test
python3 test_core_system.py
```

### From IDE

1. **Using Test Explorer**:
   - Open the Test Explorer sidebar (beaker icon)
   - Click the play button next to any test
   - Or right-click on a test file/folder to run all tests in it

2. **Using Debug Panel**:
   - Press `F5` or go to Run > Start Debugging
   - Select a debug configuration from the dropdown
   - Set breakpoints in your code as needed

3. **Using Command Palette**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Run Tests"
   - Select the test framework (pytest)

## Test Results Summary

### Current Test Status

✅ **Pytest Tests**: 1/1 passing
- `test_live_data_service.py` - ✅ PASSING

✅ **Core System Tests**: 6/7 passing (85.7%)
- ✅ Core Architecture - PASSING
- ✅ Safety Systems - PASSING
- ✅ Connection Monitoring - PASSING
- ✅ ROM Verification - PASSING
- ❌ GUI Integration - FAILING (PyQt5 not installed - optional dependency)
- ✅ Working Platforms - PASSING
- ✅ End-to-End Safety - PASSING

### Known Issues

1. **GUI Test Failure**: PyQt5 is not installed due to disk space constraints. This is an optional dependency and doesn't affect core functionality.

2. **Missing Module**: `tests/test_queue.py` references `muts.services.queue` which doesn't exist. This test is currently skipped.

## Bugs Fixed

### 1. SecurityManager Initialization Bug
- **Issue**: `key_derivation_iterations` was accessed before being initialized
- **Fix**: Moved attribute initialization before it's used in `__init__`
- **File**: `muts/utils/security.py`

### 2. Boost Pressure Conversion Bug
- **Issue**: Boost pressure was not being divided by 10, causing incorrect PSI values
- **Fix**: Added division by 10 before converting kPa to PSI
- **File**: `diagnostics/live_data_service.py`

## Dependencies

### Required for Testing
- pytest>=6.2.0
- pytest-cov>=2.12.0
- python-can>=4.0.0
- SQLAlchemy>=1.4.0
- cryptography>=3.4.0
- torch>=1.12.0 (CPU version is sufficient)
- scikit-learn>=1.0.0
- numpy>=1.21.0
- pandas>=1.3.0
- PyYAML>=6.0

### Optional (for GUI tests)
- PyQt5>=5.15.0

## Debugging Tips

1. **Set Breakpoints**: Click in the gutter next to line numbers to set breakpoints
2. **Step Through Code**: Use F10 (step over), F11 (step into), Shift+F11 (step out)
3. **Inspect Variables**: Hover over variables or use the Variables panel
4. **Watch Expressions**: Add expressions to the Watch panel to monitor values
5. **Debug Console**: Use the Debug Console to evaluate expressions in the current context

## Test Structure

```
tests/
├── test_comms.py          # Communication tests (stub)
├── test_diagnostics.py    # Diagnostic tests (stub)
├── test_live_data_service.py  # Live data service tests ✅
├── test_queue.py          # Queue tests (missing module - skipped)
├── test_security.py       # Security tests
├── test_tuning.py         # Tuning tests
└── test_ui_smoke.py       # UI smoke tests
```

## Continuous Integration

The project is configured with pytest.ini in `pyproject.toml`:
- Minimum pytest version: 6.0
- Test paths: `tests/`
- Coverage reports: HTML and terminal

## Coverage Reports

Coverage reports are generated in `htmlcov/` when running with `--cov`. Open `htmlcov/index.html` in a browser to view detailed coverage information.

## Next Steps

1. Implement missing `muts.services.queue` module or update `test_queue.py`
2. Install PyQt5 for GUI tests (if GUI functionality is needed)
3. Add more comprehensive test coverage
4. Set up CI/CD pipeline integration

