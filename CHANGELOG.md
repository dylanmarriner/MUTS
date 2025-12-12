# CHANGELOG

All notable changes to MUTS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-13

### Added
- Professional diagnostic and tuning system for Mazda vehicles
- Multi-protocol support: VERSA, MDS, and COBB tuning protocols
- ADD (Adaptive Decision) AI-assisted learning system
- Live data streaming with real-time telemetry
- DTC reading and clearing capabilities
- Safe tuning map editing and application
- ECU flashing with rollback capability
- Full audit trail for all operations
- Operator modes: DEV, WORKSHOP, and LAB
- Cross-platform support (Windows, macOS, Linux)
- Comprehensive safety controls

### Safety Features
- No fake data policy - explicit NOT_CONNECTED and STALE indicators
- All ECU writes blocked in DEV mode
- Technician authentication required for writes
- Job tracking and ARM flow requirements
- Full audit logging with attribution
- 2-second TTL for data staleness

### Security
- Operator mode enforcement
- Role-based access control
- Session management
- Data validation and verification
- Checksum validation for flashing

### Documentation
- Complete README with safety philosophy
- First Run Guide
- Contributing Guidelines
- Security Policy
- Professional licensing

### Verification
- Complete feature traceability (342 features)
- Zero fake data violations
- Verified live learning capability
- Comprehensive write safety (7 gates, 0 bypasses)
- End-to-end workshop testing

### Known Limitations
- Requires J2534 compatible interface
- ECU writes require professional authorization
- No automatic tuning - requires expert knowledge
- Not affiliated with Mazda Corporation

### Disclaimer
MUTS is provided as-is for professional use. Users must have proper training and permissions for vehicle modifications.
