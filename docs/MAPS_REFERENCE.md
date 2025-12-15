# Maps Reference

## Overview

MUTS represents ECU calibration data as structured “maps” (tables/curves) plus limiters. These are the building blocks for diagnostics, safe tuning, and future flashing workflows.

This page describes how maps are modeled in the codebase and how they’re intended to be used.

## Map categories

- **Fueling**
  - Targets and compensation tables that influence commanded fueling.
- **Ignition**
  - Timing tables, compensations, and related control logic.
- **Boost control**
  - Wastegate duty, boost targets, and boost-related compensations.
- **VVT (cam timing)**
  - Intake/exhaust cam target tables and modifiers.
- **Limiters**
  - Hard or soft limits (torque, boost, load, RPM, etc.) that must be respected by all write paths.

## Where the data model lives

The core calibration schema is defined in:

- `muts/database/ecu_database.py`
  - Defines typed records for common calibration constructs such as ignition, fuel, boost, VVT maps, and limiters.
  - Provides a `FactoryData` helper for initializing and accessing factory/default calibration data.

Tuning metadata and supporting reference data live in:

- `muts/database/tuning_database.py`
  - Defines performance map metadata, turbo data, engine components, tuning secrets, and DTC records.

## Intended tuning workflow

1. **Select or read the current calibration**
2. **Propose changes as a patch** (never “write raw” without validation)
3. **Validate against safety rules**
   - See `docs/SAFETY_MODEL.md` and the validator in `core/safety_validator.py`
4. **Apply through the controlled executor path**
   - Safety enforcement + audit trail + operator mode gating

## Notes

- Map axes, units, and scaling are ECU-specific. MUTS stores structured data, but decoding/encoding must remain explicit.
- Any map that can impact engine safety must be guarded by mode gating and limits before write operations are attempted.
