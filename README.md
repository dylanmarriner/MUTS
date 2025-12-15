# MUTS - Mazda Universal Tuning System

[![Build Status](https://github.com/dylanmarriner/MUTS/workflows/CI/badge.svg)](https://github.com/dylanmarriner/MUTS/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/dylanmarriner/MUTS)](https://github.com/dylanmarriner/MUTS/releases)

A professional tuning and diagnostic system for Mazda vehicles, built with safety and transparency as core principles.

## What MUTS IS

- **Professional Diagnostic Tool**: Read and clear DTCs, view live data, and monitor vehicle systems
- **Tuning Platform**: Safe tuning map editing and application with full audit trails
- **AI-Assisted Learning**: ADD (Adaptive Decision) system learns from vehicle data to provide recommendations
- **Multi-Protocol Support**: VERSA, MDS, and COBB tuning protocols
- **Cross-Platform**: Windows, macOS, and Linux support

## What MUTS is NOT

- **NOT an OEM Tool**: Not affiliated with Mazda Corporation
- **NOT a "Chip Tune"**: No magic fixes - requires professional knowledge
- **NOT a Toy**: Real ECU write capabilities with safety controls
- **NOT a Data Faker**: Never shows fake data as real - see Safety Philosophy

## Safety Philosophy

MUTS operates under strict safety principles:

1. **No Fake Data**: The system never displays fake or placeholder values as real data
   - When no interface is connected: Shows `NOT_CONNECTED`
   - When data is stale (>2s): Shows `STALE`
   - All values are either real or explicitly marked as invalid

2. **Intentional Writes Only**: All ECU write operations require:
   - WORKSHOP or LAB operator mode (never in DEV)
   - Authenticated technician
   - Active job tracking
   - Explicit ARM confirmation
   - Connected interface with vehicle present

3. **Full Audit Trail**: Every operation is logged with:
   - Technician ID
   - Job ID
   - Timestamp
   - Operation details
   - Success/failure status

## Operator Modes

### 🔧 DEV MODE (Default)
- Safe for development and exploration
- All ECU writes blocked
- No authentication required
- Perfect for learning the system

### 🏭 WORKSHOP MODE
- Professional tuning and diagnostics
- ECU writes allowed with full authorization
- Requires technician authentication
- Complete audit trail

### 🔬 LAB MODE
- Development and testing
- Similar to WORKSHOP with debug features
- ECU writes allowed with proper authorization
- Enhanced logging

#### Configuration
Set the operator mode in your `.env` file:
```bash
OPERATOR_MODE=dev  # Options: dev, workshop, lab
```

The mode is locked at startup and requires a restart to change.

## Supported Use Cases

- **Diagnostics**: Read/clear DTCs, view live data, freeze frames
- **Data Logging**: Record telemetry for analysis
- **Tuning**: Safe map editing and application
- **Learning**: ADD system analyzes data and provides recommendations
- **Flashing**: ECU firmware updates with rollback capability

## Hardware Requirements

### Minimum
- J2534 compatible interface
- OBD-II cable
- Computer with USB 2.0+
- 4GB RAM
- 500MB disk space

### Recommended
- VERSA J2534 interface
- High-quality OBD-II cable
- SSD for better performance
- 8GB RAM
- 2GB disk space

## Installation

### Download Installer
1. Go to [Releases](https://github.com/dylanmarriner/MUTS/releases)
2. Download for your platform:
   - Windows: `.exe` installer
   - macOS: `.dmg` disk image
   - Linux: `.AppImage` or `.deb`

### Verify Installation
Check the SHA256 checksum:
```bash
sha256sum MUTS-1.0.0-Installer.exe
```

### First Run
See [docs/FIRST_RUN.md](docs/FIRST_RUN.md) for detailed setup instructions.

## Quick Start

1. Launch MUTS
2. Select Operator Mode (DEV for testing)
3. Connect J2534 interface
4. Identify vehicle
5. Start with diagnostics

## Documentation

- [First Run Guide](docs/FIRST_RUN.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Security Policy](docs/SECURITY.md)
- [CHANGELOG](CHANGELOG.md)

## Development

Built with:
- Backend: Node.js + TypeScript + Prisma
- Desktop: Electron + React
- Core: Rust
- Database: SQLite

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

MUTS is not affiliated with Mazda Corporation. All trademarks are property of their respective owners.

Use at your own risk. Always follow proper tuning procedures and ensure you have the necessary expertise and permissions.

## Support

- Issues: [GitHub Issues](https://github.com/dylanmarriner/MUTS/issues)
- Security: See [docs/SECURITY.md](docs/SECURITY.md)
- Discussions: [GitHub Discussions](https://github.com/dylanmarriner/MUTS/discussions)

---

**Made with ❤️ by Dylan Marriner**
