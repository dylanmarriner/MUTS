# Database-to-UI Coverage Audit

## Database Entities (from app/muts/models/database_models.py)

### 1. Vehicle
- **Table**: vehicles
- **Fields**: id (VIN), user_id, model, ecu_type, created_at
- **Relationships**: ecu_data, dtcs, tuning_profiles
- **UI Status**: ❌ NO DEDICATED PANEL
- **Current UI**: Only basic info in dashboard (VIN, ECU, Software, Hardware)
- **Missing**: Full vehicle list, vehicle selection, vehicle management

### 2. ECUData
- **Table**: ecu_data
- **Fields**: id, vehicle_id, timestamp, rpm, boost_psi, throttle_position, ignition_timing, fuel_trim_long, fuel_trim_short, maf_voltage, afr, coolant_temp, intake_temp, knock_count, vvt_advance, calculated_load
- **UI Status**: ⚠️ PARTIAL
- **Current UI**: Dashboard shows live data (RPM, Speed, Throttle, Boost, AFR, IAT)
- **Missing**: Historical data view, data export, full parameter list, timestamps, source indication

### 3. DiagnosticTroubleCode
- **Table**: trouble_codes
- **Fields**: id, vehicle_id, code, description, severity, detected_at, cleared_at
- **UI Status**: ❌ NO DEDICATED PANEL
- **Current UI**: Diagnostics section exists but content not defined
- **Missing**: DTC list, code details, severity indicators, clear history

### 4. TuningProfile
- **Table**: tuning_profiles
- **Fields**: id, vehicle_id, name, mode, boost_maps, fuel_maps, timing_maps, vvt_maps, created_at, is_active
- **UI Status**: ⚠️ PARTIAL
- **Current UI**: Tuning and Maps sections exist
- **Missing**: Profile list, profile switching, map visualization, active profile indicator

### 5. LogEntry
- **Table**: log_entries
- **Fields**: id, vehicle_id, timestamp, level, module, message, data
- **UI Status**: ❌ NO DEDICATED PANEL
- **Current UI**: Data Logging section exists but empty
- **Missing**: Log viewer, filter by level/module, timestamps, data inspection

### 6. PerformanceRun
- **Table**: performance_runs
- **Fields**: id, vehicle_id, run_type, start_time, end_time, duration, ambient_temp, humidity, altitude, barometric_pressure, fuel_type, tire_pressure, modification_notes, created_at
- **UI Status**: ❌ MISSING ENTIRELY
- **Current UI**: No performance tracking UI
- **Missing**: Performance runs list, run details, timing interface

### 7. FlashHistory
- **Table**: flash_history
- **Fields**: id, vehicle_id, flash_type, calibration_id, software_version, status, error_message, started_at, completed_at, duration, notes, backup_path
- **UI Status**: ⚠️ PARTIAL
- **Current UI**: Flash ECU section exists
- **Missing**: Flash history list, status tracking, error details, backup verification

## Additional Required Database Entities (Not Found in Models)

### 8. User/Session State
- **Required**: users table, sessions table
- **UI Status**: ❌ MISSING
- **Current UI**: No user management
- **Missing**: Login, user selection, session tracking

### 9. Hardware Connection State
- **Required**: connection_status, hardware_config
- **UI Status**: ⚠️ PARTIAL
- **Current UI**: Connection status in title bar
- **Missing**: Connection details, hardware config, interface selection

### 10. AI Learning Data
- **Required**: ai_models, training_data, learning_history
- **UI Status**: ❌ MISSING
- **Current UI**: No AI visibility
- **Missing**: Model status, training data counts, learning insights

### 11. Security/Access Logs
- **Required**: security_events, access_attempts, permissions
- **UI Status**: ⚠️ PARTIAL
- **Current UI**: Security section exists
- **Missing**: Security logs, access history, permission management

### 12. Telemetry History
- **Required**: telemetry_sessions, telemetry_data
- **UI Status**: ❌ MISSING
- **Current UI**: No telemetry storage
- **Missing**: Session management, historical playback

## UI Panels Identified (from index.html)

1. Dashboard - Partial ECU data display
2. Tuning - Exists but incomplete
3. Maps - Exists but incomplete
4. Diagnostics - Exists but empty
5. Data Logging - Exists but empty
6. Flash ECU - Partial implementation
7. Security - Exists but incomplete
8. Preferences - Theme settings only

## Coverage Matrix

| Database Entity | UI Panel | Status | Missing Elements |
|----------------|----------|---------|------------------|
| Vehicle | None | ❌ 0% | Vehicle list, management |
| ECUData | Dashboard | ⚠️ 40% | History, export, full params |
| DiagnosticTroubleCode | Diagnostics | ❌ 0% | DTC list, details |
| TuningProfile | Tuning/Maps | ⚠️ 30% | Profile list, visualization |
| LogEntry | Data Logging | ❌ 0% | Log viewer, filters |
| PerformanceRun | None | ❌ 0% | Entire UI missing |
| FlashHistory | Flash ECU | ⚠️ 50% | History list, details |
| User/Session | None | ❌ 0% | User management |
| Hardware State | Title bar | ⚠️ 20% | Config, details |
| AI Data | None | ❌ 0% | AI visibility |
| Security Logs | Security | ⚠️ 20% | Log viewer |
| Telemetry | None | ❌ 0% | Session management |

## Critical Issues Found

1. **No Vehicle Management**: Cannot select or manage multiple vehicles
2. **Missing Historical Data**: Only live data shown, no history
3. **Empty Sections**: Diagnostics, Data Logging panels are empty
4. **No User System**: No multi-user support or session management
5. **AI Hidden**: No visibility into AI learning or models
6. **Performance Tracking Missing**: No performance run UI
7. **Incomplete Security**: Security section lacks log viewing

## Immediate Actions Required

1. Create Vehicle Management panel
2. Implement DTC viewer in Diagnostics
3. Build Log viewer for Data Logging
4. Add Performance Run interface
5. Create User/Session management
6. Implement AI visibility panel
7. Add historical data views for all entities
8. Enhance existing panels with missing features
