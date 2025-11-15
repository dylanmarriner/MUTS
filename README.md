# Mazda Ultimate Technician Suite (MUTS)

## Overview
MUTS is a full desktop diagnostic and tuning suite for the 2011 Mazdaspeed 3 (VIN 7AT0C13JX20200064).  
It includes:
- J2534-based ECU communication
- Diagnostics (ECM, ABS, SRS, BCM)
- Tuning (load, boost, ignition, fuel, torque, SWAS)
- ECU flashing with safety validation
- Dyno simulation
- Logging system
- Role-based security and valet mode
- PyQt6 GUI

## Tech Stack
- Python 3.11+
- PyQt6 UI
- SQLite via SQLAlchemy
- Numpy, Matplotlib, Pydantic
- J2534 passthrough interface
- ISO-TP, UDS, KWP2000 protocols

## Project Structure
See full layout in `/muts_project.zip` or root directories:
- `core/` – safety, state, ROM logic
- `comms/` – ECU communication and protocols
- `diagnostics/` – modules for ECM/ABS/SRS/BCM
- `tuning/` – maps, torque, performance features
- `security/` – users, valet, anti-theft
- `ui/` – PyQt6 interface
- `simulators/` – virtual ECU + dyno
- `tools/` – helper scripts
- `docs/` – architecture and protocols

## Installation
### Windows (J2534 recommended)
1. Install Python 3.11
2. Install your J2534 cable drivers (OpenPort, VCX, etc.)
3. Run:
```
pip install -r requirements.txt
```
4. Launch:
```
python main.py
```

## Flashing Disclaimer
ECU flashing is dangerous by nature. MUTS includes:
- Battery voltage detection
- Safe-session handling
- Checksum patching
- Automatic rollback
But you are still fully responsible for what you flash.

## Agents
See `agent.md` and `agents.md` for internal subsystem behavior documentation.

## License
MIT License
