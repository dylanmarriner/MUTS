# Safety Model

## Overview

MUTS is designed to make ECU write operations explicit, deliberate, and defensible.

Safety is enforced through:

- Operator mode gating (DEV vs. WORKSHOP/LAB)
- Parameter validation against hard limits
- Clear failure behavior (block unsafe writes, log why)

## Safety limits

There are two primary sources of safety constraints:

- `safety_limits.yml`
  - Project-level configuration for high-level boundaries.
- `core/safety_validator.py`
  - Runtime enforcement in `SafetyValidator` using:
    - `SafetyLimits` (hard caps)
    - `mode_limits` (stricter limits per `PerformanceMode`)

## Validation model

### Severity levels

Safety violations are classified as:

- `SAFE`
- `WARNING`
- `DANGEROUS`
- `CRITICAL`

The validator returns both:

- Whether the operation is safe enough to proceed
- The list of violations explaining what failed and why

### Parameter validation

`SafetyValidator.validate_tuning_parameters(params)` checks tuning parameters like:

- `boost_target`
- `timing_base`
- `afr_target`
- `rev_limit`

Mode-specific limits may generate `DANGEROUS` violations even if the parameter is still below the global hard cap.

### Live data validation

`SafetyValidator.validate_live_data(ecu_data)` checks for unsafe live conditions such as:

- Coolant temperature
- Oil pressure
- EGT
- RPM

This is intended for runtime protection workflows (clamping, warnings, or fail-safe behavior).

## Where safety is enforced in the write path

The main integration point is:

- `core/ecu_communication.py`
  - `ECUCommunicator.send_request()` calls `_validate_safety_before_write()`
  - Write-like services are checked before any message is sent
  - Unsafe writes are blocked and recorded in stats (`safety_blocks`)

## Extending the safety model

If you add new ECU write paths, the non-negotiable rule is:

- All writes must be validated against safety constraints before transmitting.

Practical follow-ups usually include:

- Decoding write payloads into explicit parameters (avoid opaque “bytes-only” validation)
- Adding new limit checks (torque, load, fuel pressure, etc.)
- Adding audit logging for any operation that can change ECU state
