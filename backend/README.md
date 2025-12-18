# VersaTuner Backend

Clean, professional backend structure for automotive diagnostics and tuning.

## Structure

- `core/` - Application bootstrap, configuration, logging, lifecycle
- `vehicles/` - Vehicle-specific profiles and calibration data
- `diagnostics/` - Diagnostic protocols (MDS, MUTS, ADD)
- `tuning/` - Map editing, AI optimization, safety limits
- `interfaces/` - CAN, OBD, J2534 communication
- `compatibility/` - Third-party tool support (COBB)
- `api/` - REST endpoints, controllers, schemas
- `persistence/` - Database, telemetry, logging
- `security/` - Seed-key algorithms, authentication
- `tests/` - Smoke, integration, hardware guard tests

## Usage

```python
from backend import diagnostics, tuning, security
```

## Notes

- No mock data or stubs
- All ECU write paths preserved
- No behavior changes from reorganization
