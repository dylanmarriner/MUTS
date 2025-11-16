# MUTS Product Spec

**Vehicle focus:** 2011 Mazdaspeed 3 (VIN 7AT0C13JX20200064)  
**Goal:** Dealer-level diagnostics + pro-tuning in a desktop PyQt app.

## Core modules

- Diagnostics: DTC read/clear (Engine/ABS/SRS/BCM), live data, health checks.
- Tuning: SWAS toggle, per-gear torque limits, safe 1st/2nd boost-cut relief.
- Security: Valet mode (PIN), future immobilizer/seed-key.
- Dyno: Virtual pulls to preview tuning effects.
- Transport: Simulation now; J2534/ISO-15765 later.

## Non-negotiable guardrails

- All writes go through the ECU queue and must fail soft.
- Future temperature/knock overlays clamp torque automatically.
- Immobilizer/valet/locks must be honoured at executor level.
