# Mazda Universal Tuning Suite (MUTS)

Complete autonomous tuning and diagnostic system for the 2011 Mazdaspeed 3.

## Features

### 🚀 Autonomous AI Tuning
- Real-time AI optimization using reinforcement learning
- Physics-based engine modeling
- Adaptive tuning algorithms
- Safety-first approach with comprehensive limits

### 🔧 Complete Diagnostic System
- Full CAN bus communication with ECU
- Diagnostic trouble code reading and clearing
- Real-time sensor data acquisition
- Dealer-level diagnostic capabilities

### ⚡ Performance Features
- Anti-lag system (ALS)
- 2-step rev limiter
- Launch control
- Performance mode switching (Street/Track/Drag)

### 🔒 Security & Safety
- Encrypted calibration storage
- Vehicle-specific tuning file validation
- Comprehensive safety limits
- Factory dealer access

### 📊 Complete Database
- Factory ECU calibration data
- K04 turbocharger specifications
- Engine component limits
- Proprietary tuning secrets

## Safety Systems

MUTS includes multiple layers of safety protection to prevent damage to the vehicle and ECU:

## Parameter Validation
- **Hard Limits**: Maximum boost (25 psi), timing (30°), minimum AFR (10.5), max RPM (7000)
- **Mode-Specific Limits**: Different safety thresholds for Stock, Street, Track, Drag, and Safe modes
- **Real-time Validation**: All tuning parameters are validated before being sent to the ECU
- **Safety Override**: Password-protected override for advanced users (password: MUTS_OVERRIDE_2024)

## Connection Health Monitoring
- **Auto-Reconnect**: Automatically reconnects if CAN bus connection is lost
- **Performance Metrics**: Tracks message rate, error rate, response times
- **Health Status**: Excellent/Good/Poor/Disconnected status indicators
- **Failure Detection**: Monitors consecutive failures and triggers recovery

## ROM Integrity Protection
- **Pre-Flash Verification**: Validates ROM size and checks for corruption before flashing
- **Checksum Verification**: Multiple checksum algorithms (CRC16/32, MD5, SHA256, Mazda proprietary)
- **Post-Flash Validation**: Complete ROM integrity verification after flashing
- **Anti-Brick Protection**: Prevents flashing corrupted or incomplete ROM files

## Emergency Protection
- **Live Data Monitoring**: Continuous monitoring of coolant temp, oil pressure, EGT
- **Automatic Shutdown**: System can prevent dangerous operations in critical conditions
- **Audit Logging**: All safety blocks and violations are logged for review

## Safety Status
The current safety system status can be checked in the GUI or via the API:
```python
from core.safety_validator import get_safety_validator
safety = get_safety_validator()
status = safety.get_safety_status()
```

# Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/muts.git
cd muts

# Install dependencies
pip install -r requirements.txt

# Initialize database
python main.py db --init
```

## Usage

### Start Autonomous Tuning
```bash
python main.py tune --start --mode street
```

### Diagnostic Functions
```bash
# Connect to vehicle
python main.py diag --connect

# Read DTCs
python main.py diag --dtc

# Clear DTCs
python main.py diag --clear
```

### Security Access
```bash
# Request dealer access
python main.py security --access dealer

# Check security status
python main.py security --status
```

### Performance Features
```bash
# Enable anti-lag system
python main.py perf --als enable

# Enable launch control
python main.py perf --launch enable

# Set track mode
python main.py perf --mode track
```

## Architecture

```
muts/
├── core/           # Main tuning system
├── services/       # AI tuner, physics engine, dealer service, performance features
├── models/         # Engine and turbo models
├── utils/          # Calculations and security utilities
├── config/         # Vehicle-specific configuration
├── comms/          # CAN bus communication
├── database/       # Complete tuning database
└── main.py         # Application entry point
```

## Safety Features

- **Comprehensive Limits**: Boost, timing, temperature, and RPM limits
- **Real-time Monitoring**: Continuous sensor data validation
- **Emergency Shutdown**: Automatic system shutdown on safety violations
- **Data Encryption**: Secure storage of calibration data
- **Vehicle Validation**: Tuning files locked to specific VINs

## Technical Specifications

### Engine Support
- 2011 Mazdaspeed 3
- MZR 2.3L DISI Turbo engine
- K04 turbocharger (Mitsubishi TD04-HL-15T-6)

### Communication
- CAN bus (500kbps)
- ISO15765-4 (CAN) protocol
- Real-time data acquisition
- Diagnostic service support

### AI & Physics
- Reinforcement learning optimization
- Real thermodynamic calculations
- Turbocharger spool physics
- Engine cycle analysis

## Requirements

- Python 3.8+
- CAN interface hardware (optional for simulation mode)
- Linux/Windows/macOS
- 4GB RAM minimum

## Dependencies

- numpy: Numerical computations
- torch: AI and machine learning
- scipy: Scientific computing
- sklearn: Machine learning algorithms
- sqlalchemy: Database operations
- cryptography: Security and encryption
- python-can: CAN bus communication

## License

This project is for educational and research purposes only. Use at your own risk.

## Disclaimer

This software is provided as-is for educational purposes. The authors are not responsible for any damage, injury, or legal consequences resulting from its use. Always consult with qualified professionals before making modifications to your vehicle.
