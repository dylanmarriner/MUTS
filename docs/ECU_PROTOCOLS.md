# ECU Protocols

## Overview

MUTS communicates with Mazda ECUs and modules over a layered stack:

- J2534 PassThru (hardware interface)
- ISO-TP / ISO 15765-2 (transport over CAN)
- UDS (ISO 14229) and (where applicable) KWP2000-style services

The current implementation is intentionally minimal and focused on typical request/response diagnostics and controlled write flows.

## Where the code lives

- `comms/j2534_manager.py`
  - Loads device definitions from `config/j2534_devices.yml` and attempts to auto-connect.
- `comms/j2534_device.py` / `comms/j2534_api.py`
  - Thin wrappers around the PassThru API and message structures.
- `comms/iso15765_transport.py`
  - Minimal ISO-TP reassembly (single frame + multi-frame) over ISO15765.
- `comms/uds_protocol.py`
  - `UdsClient` helper for common UDS services.
- `comms/kwp2000_protocol.py`
  - Minimal `KwpClient` helper for modules that still behave like KWP.

## Typical flow

1. Find and connect to a PassThru device
   - `J2534Manager.auto_connect_first()`
2. Create an ISO-TP transport with the correct TX/RX CAN IDs
   - `IsoTpTransport(dev, tx_id, rx_id)`
3. Use a protocol client
   - `UdsClient(transport)` or `KwpClient(transport)`

## UDS services implemented

The `UdsClient` helper currently includes a small set of common services:

- Diagnostic Session Control (`0x10`)
- ECU Reset (`0x11`)
- Read Data By Identifier (`0x22`)
- Write Data By Identifier (`0x2E`)
- Security Access (`0x27`)
- Routine Control (`0x31`)
- Request Download / Transfer Data / Transfer Exit (`0x34` / `0x36` / `0x37`)
- Tester Present (`0x3E`)

## Safety note

All write-capable operations must be gated by operator mode and validated against safety limits before the request is sent. The write path should always flow through the safety enforcement layer (see `core/safety_validator.py`).
