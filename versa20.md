# VersaTuner API Reference

## Overview

VersaTuner provides a comprehensive Python API for tuning Mazdaspeed 3 vehicles. This reference covers all public classes, methods, and interfaces.

## Core Modules

### ECU Communication (`src.core.ecu_communication`)

#### `ECUCommunicator`

Main class for ECU communication via CAN bus.

**Methods:**

- `connect() -> bool` - Connect to ECU
- `disconnect()` - Disconnect from ECU
- `send_request(service: int, subfunction: int, data: bytes = b'') -> ECUResponse` - Send diagnostic request
- `read_vin() -> Optional[str]` - Read Vehicle Identification Number
- `read_dtcs() -> List[Dict]` - Read Diagnostic Trouble Codes
- `clear_dtcs() -> bool` - Clear all DTCs
- `read_live_data(pid: int) -> Optional[float]` - Read live data parameter

**Properties:**

- `is_connected: bool` - Connection status
- `interface: str` - CAN interface name

#### `ECUResponse`

Container for ECU response data.

**Attributes:**

- `success: bool` - Request success status
- `data: bytes` - Response data
- `timestamp: float` - Response timestamp
- `error_code: Optional[int]` - Error code if failed

### Security Access (`src.core.security_access`)

#### `SecurityManager`

Manages ECU security access and authentication.

**Methods:**

- `unlock_ecu(target_level: int = 3) -> bool` - Unlock ECU security
- `enter_programming_mode() -> bool` - Enter programming mode
- `exit_programming_mode() -> bool` - Exit programming mode
- `check_security_status() -> Dict` - Get security status

### ROM Operations (`src.core.rom_operations`)

#### `ROMOperations`

Handles ROM reading, writing, and verification.

**Methods:**

- `read_complete_rom(progress_callback: Optional[Callable] = None) -> Optional[bytes]` - Read complete ROM
- `write_complete_rom(rom_data: bytes, progress_callback: Optional[Callable] = None) -> bool` - Write complete ROM
- `verify_rom_integrity(rom_data: bytes) -> Dict` - Verify ROM integrity
- `patch_checksums(rom_data: bytes) -> bytes` - Patch checksums after modifications
- `read_ecu_info() -> Dict` - Read ECU information

## Tuning Modules

### Map Definitions (`src.tuning.map_definitions`)

#### `MapDefinitionManager`

Manages all tuning map definitions.

**Methods:**

- `get_map(map_name: str) -> Optional[MapDefinition]` - Get map definition by name
- `get_maps_by_category(category: str) -> List[MapDefinition]` - Get maps by category
- `validate_map_value(map_name: str, value: float) -> bool` - Validate value against map limits

#### `MapDefinition`

Dataclass containing map definition.

**Attributes:**

- `name: str` - Map name
- `address: int` - ROM address
- `size: int` - Size in bytes
- `type: str` - Map type ('2D_16x16', '1D', etc.)
- `units: str` - Physical units
- `conversion_factor: float` - Conversion to physical units
- `min_value: float` - Minimum allowed value
- `max_value: float` - Maximum allowed value

### Map Editor (`src.tuning.map_editor`)

#### `MapEditor`

Advanced map editing and manipulation.

**Methods:**

- `load_map_from_rom(map_name: str, rom_data: bytes) -> Optional[MapData]` - Load map from ROM
- `modify_map_value(map_name: str, x_index: int, y_index: int, new_value: float, validate: bool = True) -> bool` - Modify single value
- `apply_global_adjustment(map_name: str, adjustment: float, condition: Optional[Callable] = None) -> bool` - Apply global adjustment
- `generate_patch_rom(rom_data: bytes) -> bytes` - Generate patched ROM
- `create_performance_tune(rom_data: bytes, power_target: int) -> bytes` - Create performance tune

#### `MapData`

Container for map data and metadata.

**Attributes:**

- `definition: MapDefinition` - Map definition
- `data: np.ndarray` - Map data array
- `raw_bytes: bytes` - Raw ROM data

## Vehicle Modules

### Mazdaspeed 3 Implementation (`src.vehicle.mazdaspeed3_2011`)

#### `Mazdaspeed32011`

Vehicle-specific implementation for 2011 Mazdaspeed 3.

**Methods:**

- `get_vehicle_info() -> Dict` - Get vehicle information
- `validate_tune_parameters(tune_data: Dict) -> Dict` - Validate tuning parameters
- `calculate_safe_power_gains(modifications: List[str]) -> Dict` - Calculate power gains
- `get_recommended_tunes(power_target: int) -> Dict` - Get recommended tunes

### Diagnostics (`src.vehicle.diagnostic_services`)

#### `DiagnosticManager`

Comprehensive diagnostic service management.

**Methods:**

- `execute_diagnostic_routine(routine_name: str, parameters: Dict = None) -> Dict` - Execute diagnostic routine
- `perform_comprehensive_diagnostic() -> Dict` - Perform full diagnostic
- `read_adaptive_values() -> Dict` - Read adaptive learning values
- `reset_adaptive_memory() -> bool` - Reset adaptive memory

#### `DTCHandler`

Complete DTC management.

**Methods:**

- `read_all_dtcs() -> List[DTCInfo]` - Read all DTCs
- `clear_all_dtcs() -> bool` - Clear all DTCs
- `clear_specific_dtc(dtc_code: str) -> bool` - Clear specific DTC
- `generate_dtc_report() -> Dict` - Generate DTC report

## Utility Modules

### File Operations (`src.utils.file_operations`)

#### `FileManager`

Professional file management.

**Methods:**

- `save_rom_file(rom_data: bytes, filename: str, metadata: Dict = None) -> str` - Save ROM file
- `load_rom_file(filename: str) -> tuple[bytes, Dict]` - Load ROM file
- `create_backup(rom_data: bytes, backup_name: str = None) -> str` - Create backup
- `export_tune_package(rom_data: bytes, tune_data: Dict, export_name: str) -> str` - Export tune package

### Compression (`src.utils.compression`)

#### `CompressionManager`

Data compression and decompression.

**Methods:**

- `compress_data(data: bytes, method: str = 'zlib', level: int = 6) -> bytes` - Compress data
- `decompress_data(compressed_data: bytes, method: str = 'zlib') -> bytes` - Decompress data
- `optimize_rom_storage(rom_data: bytes) -> bytes` - Optimize ROM storage

## Interface Modules

### GUI Interface (`src.interfaces.gui_main`)

#### `VersaTunerGUI`

Main GUI application.

**Methods:**

- `run()` - Start GUI application

### Console Interface (`src.interfaces.tuning_console`)

#### `TuningConsole`

Command-line interface.

**Methods:**

- `cmdloop()` - Start console interface

## Configuration

### Vehicle Profiles (`config/vehicle_profiles.json`)

Contains vehicle-specific parameters and limits.

**Structure:**
```json
{
  "vehicle_info": { ... },
  "engine_specifications": { ... },
  "performance_limits": { ... },
  "tuning_parameters": { ... }
}