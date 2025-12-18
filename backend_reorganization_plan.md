# Backend Reorganization Plan

## Current State Analysis

### Files in Root Directory (Need Reorganization)

- **MUTS modules**: muts1.py through muts16.py (security, tuning, diagnostics)
- **MDS modules**: mds1.py through mds15.py (diagnostic protocols)
- **ADD modules**: add1.py through add24.py (auxiliary diagnostic drivers)
- **COBB modules**: cobb1.py through cobb12.py (compatibility/definitions)
- **Versa modules**: versa1.py through versa19.py (tuning interface)
- **MPS modules**: mps*.py, "mps tune.py", "mps safe tune.py" (ROM tuning)
- **Other**: run_muts.py, Sci-fi-Dylan-Custom-Theme.js

### Already Organized

- app/muts/ - Already structured with proper modules
- app/mds/ - Already structured
- app/mps/ - Already structured
- app/versa/ - Already structured
- app/cobb/ - Already structured
- src/muts/ - Partial structure

## Target Structure (backend/)

```
backend/
├── core/
│   ├── bootstrap/
│   │   ├── __init__.py
│   │   └── application.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py
│   └── lifecycle/
│       ├── __init__.py
│       └── manager.py
│
├── vehicles/
│   └── mazda/
│       └── mazdaspeed3_2011/
│           ├── profiles/
│           │   ├── __init__.py
│           │   └── vehicle_profile.py
│           ├── vin/
│           │   ├── __init__.py
│           │   └── decoder.py
│           └── calibration/
│               ├── __init__.py
│               └── data.py
│
├── diagnostics/
│   ├── mds/
│   │   ├── __init__.py
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   └── protocols.py
│   │   ├── abs/
│   │   │   ├── __init__.py
│   │   │   └── abs_diagnostics.py
│   │   ├── srs/
│   │   │   ├── __init__.py
│   │   │   └── airbag.py
│   │   └── body/
│   │       ├── __init__.py
│   │       └── body_control.py
│   ├── muts/
│   │   ├── __init__.py
│   │   ├── scanner/
│   │   │   ├── __init__.py
│   │   │   └── main_scanner.py
│   │   ├── dtc/
│   │   │   ├── __init__.py
│   │   │   └── dtc_reader.py
│   │   ├── live_data/
│   │   │   ├── __init__.py
│   │   │   └── data_stream.py
│   │   └── service_functions/
│   │       ├── __init__.py
│   │       └── services.py
│   └── add/
│       ├── __init__.py
│       ├── sensors/
│       │   ├── __init__.py
│       │   └── sensor_drivers.py
│       ├── pid_extensions/
│       │   ├── __init__.py
│       │   └── extended_pids.py
│       └── experimental/
│           ├── __init__.py
│           └── research.py
│
├── tuning/
│   ├── ai/
│   │   ├── __init__.py
│   │   └── optimization.py
│   ├── maps/
│   │   ├── __init__.py
│   │   ├── fuel_maps.py
│   │   ├── ignition_maps.py
│   │   └── boost_maps.py
│   ├── safety/
│   │   ├── __init__.py
│   │   └── limits.py
│   └── profiles/
│       ├── __init__.py
│       └── tune_profiles.py
│
├── interfaces/
│   ├── can/
│   │   ├── __init__.py
│   │   ├── can_interface.py
│   │   └── can_protocol.py
│   ├── obd/
│   │   ├── __init__.py
│   │   ├── obd_interface.py
│   │   └── obd_protocols.py
│   └── j2534/
│       ├── __init__.py
│       ├── j2534_interface.py
│       └── passthru.py
│
├── compatibility/
│   └── cobb/
│       ├── __init__.py
│       ├── definitions/
│       │   ├── __init__.py
│       │   └── cobb_defs.py
│       ├── translators/
│       │   ├── __init__.py
│       │   └── format_converters.py
│       └── validators/
│           ├── __init__.py
│           └── cobb_validation.py
│
├── api/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── diagnostic_routes.py
│   │   └── tuning_routes.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── diagnostic_controller.py
│   │   └── tuning_controller.py
│   └── schemas/
│       ├── __init__.py
│       ├── diagnostic_schema.py
│       └── tuning_schema.py
│
├── persistence/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── connection.py
│   ├── telemetry/
│   │   ├── __init__.py
│   │   └── data_logger.py
│   └── logs/
│       ├── __init__.py
│       └── log_manager.py
│
├── security/
│   ├── seed_key/
│   │   ├── __init__.py
│   │   └── algorithms.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── authentication.py
│   └── permissions/
│       ├── __init__.py
│       └── access_control.py
│
└── tests/
    ├── smoke/
    │   ├── __init__.py
    │   └── basic_tests.py
    ├── integration/
    │   ├── __init__.py
    │   └── system_tests.py
    └── hardware_guard/
        ├── __init__.py
        └── safety_tests.py
```

## File Mapping Plan

### Root Directory Files → Backend Structure

#### MUTS Files:
- muts1.py → backend/security/seed_key/algorithms.py (security engine)
- muts2.py → backend/diagnostics/muts/srs/airbag.py
- muts3.py → backend/diagnostics/muts/service_functions/eeprom.py
- muts4.py → backend/core/bootstrap/application.py
- muts5.py → backend/api/controllers/tuning_controller.py
- muts6.py → backend/persistence/database/models.py
- muts7.py → backend/api/routes/tuning_routes.py (duplicate of muts5)
- muts8.py → backend/tuning/profiles/tune_profiles.py
- muts9.py → backend/persistence/database/models.py (database models)
- muts10.py → backend/diagnostics/muts/scanner/main_scanner.py
- muts11.py → backend/api/routes/diagnostic_routes.py
- muts12.py → backend/security/auth/authentication.py
- muts13.py → backend/diagnostics/muts/service_functions/ecu_exploits.py
- muts14.py → backend/tuning/ai/optimization.py
- muts15.py → backend/persistence/database/models.py (knowledge base)
- muts16.py → backend/core/config/settings.py

#### MDS Files:
- mds1.py → backend/diagnostics/mds/engine/protocols.py
- mds2.py → backend/diagnostics/mds/engine/protocols.py (protocol extensions)
- mds3.py → backend/interfaces/obd/obd_protocols.py
- mds4.py → backend/interfaces/can/can_protocol.py
- mds5.py → backend/diagnostics/mds/body/body_control.py
- mds6.py → backend/diagnostics/mds/abs/abs_diagnostics.py
- mds7.py → backend/diagnostics/mds/srs/airbag.py
- mds8.py → backend/diagnostics/mds/engine/protocols.py (engine diagnostics)
- mds9.py → backend/diagnostics/mds/engine/protocols.py (live data)
- mds10.py → backend/diagnostics/muts/dtc/dtc_reader.py
- mds11.py → backend/diagnostics/muts/live_data/data_stream.py
- mds12.py → backend/diagnostics/mds/engine/protocols.py (service functions)
- mds13.py → backend/diagnostics/mds/engine/protocols.py (advanced)
- mds14.py → backend/diagnostics/mds/engine/protocols.py (programming)
- mds15.py → backend/diagnostics/mds/engine/protocols.py (manufacturer)

#### ADD Files:
- add1.py → backend/diagnostics/add/sensors/sensor_drivers.py
- add2.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add3.py → backend/interfaces/can/can_interface.py
- add4.py → backend/diagnostics/add/experimental/research.py
- add5.py → backend/diagnostics/add/sensors/sensor_drivers.py (temperature)
- add6.py → backend/diagnostics/add/sensors/sensor_drivers.py (pressure)
- add7.py → backend/diagnostics/add/sensors/sensor_drivers.py (oxygen)
- add8.py → backend/diagnostics/add/sensors/sensor_drivers.py (MAF)
- add9.py → backend/diagnostics/add/sensors/sensor_drivers.py (throttle)
- add10.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add11.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add12.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add13.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add14.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add15.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add16.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add17.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add18.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add19.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add20.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add21.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add22.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add23.py → backend/diagnostics/add/pid_extensions/extended_pids.py
- add24.py → backend/diagnostics/add/pid_extensions/extended_pids.py

#### COBB Files:
- cobb1.py → backend/compatibility/cobb/definitions/cobb_defs.py
- cobb2.py → backend/compatibility/cobb/definitions/cobb_defs.py (maps)
- cobb3.py → backend/compatibility/cobb/translators/format_converters.py
- cobb4.py → backend/compatibility/cobb/validators/cobb_validation.py
- cobb5.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb6.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb7.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb8.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb9.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb10.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb11.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)
- cobb12.py → backend/compatibility/cobb/definitions/cobb_defs.py (tables)

#### Versa Files:
- versa1.py → backend/api/controllers/tuning_controller.py
- versa2.py → backend/tuning/maps/fuel_maps.py
- versa3.py → backend/tuning/maps/ignition_maps.py
- versa4.py → backend/tuning/maps/boost_maps.py
- versa5.py → backend/tuning/ai/optimization.py
- versa6.py → backend/tuning/safety/limits.py
- versa7.py → backend/tuning/profiles/tune_profiles.py
- versa8.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa9.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa10.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa11.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa12.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa13.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa14.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa15.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa16.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa18.py → backend/tuning/profiles/tune_profiles.py (profiles)
- versa19.py → backend/tuning/profiles/tune_profiles.py (profiles)

#### MPS Files:
- mpsrom.py → backend/tuning/maps/fuel_maps.py (ROM reader)
- mpsrom2.py → backend/tuning/maps/fuel_maps.py (advanced analyzer)
- mpsrom3.py → backend/tuning/maps/fuel_maps.py (checksum calculator)
- mpsrom4.py → backend/tuning/maps/fuel_maps.py (security bypass)
- "mps tune.py" → backend/tuning/profiles/tune_profiles.py
- "mps safe tune.py" → backend/tuning/safety/limits.py

#### Other Files:
- run_muts.py → backend/core/lifecycle/manager.py
- Sci-fi-Dylan-Custom-Theme.js → Move to electron-app (already done)

## Import Update Strategy

1. After moving files, scan for all import statements
2. Update relative imports to match new structure
3. Update app/ imports to point to backend/
4. Ensure no circular dependencies

## Validation Steps

1. Python import test for each module
2. Check for missing dependencies
3. Verify no mock data was added
4. Confirm all ECU write paths unchanged
