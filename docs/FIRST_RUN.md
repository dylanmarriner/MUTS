# MUTS First Run Guide

Welcome to MUTS (Mazda Universal Tuning System)!

## Initial Setup

1. **Install Dependencies**
   ```bash
   # Backend
   cd backend
   npm install
   npx prisma generate
   
   # Rust Core (if building from source)
   cd muts
   cargo build --release
   
   # Desktop UI
   cd muts-desktop/electron-ui
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Initialize Database**
   ```bash
   cd backend
   npx prisma db push
   ```

## Operator Modes

### DEV Mode (Default)
- Safe for development
- ECU writes blocked
- No authentication required
- Perfect for first run without hardware

### WORKSHOP Mode
- For professional use
- ECU writes allowed with proper authorization
- Requires technician authentication
- Requires active job tracking

### LAB Mode
- For testing and development
- Similar to WORKSHOP but with debug features
- ECU writes allowed with proper authorization

## Safety First

- **No Fake Data**: MUTS never shows fake data as real
- **NOT_CONNECTED**: When no interface is connected, all gauges show "--"
- **STALE Data**: Data older than 2 seconds is marked as "STALE"
- **Write Protection**: All ECU writes require explicit authorization

## Hardware Requirements

### Minimum
- J2534 compatible interface
- OBD-II cable
- Computer with USB port

### Recommended
- VERSA J2534 interface
- High-quality OBD-II cable
- SSD for better performance

## Getting Started

1. Launch MUTS Desktop Application
2. Select Operator Mode (DEV by default)
3. Connect your J2534 interface (optional for DEV mode)
4. Identify vehicle (VIN read)
5. Start with diagnostics to verify connection

## Support

- Documentation: See README.md
- Issues: Report on GitHub Issues
- Security: See SECURITY.md

## Disclaimer

MUTS is not affiliated with Mazda Corporation.
Use at your own risk.
Always follow proper tuning procedures.
