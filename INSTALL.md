# MUTS Vehicle Diagnostics - Installation Guide

## Overview
MUTS (Multi-User Tuning System) is a comprehensive vehicle diagnostics and tuning platform with offline capabilities. This guide explains how to build and install the standalone application.

## System Requirements

### Minimum Requirements
- Windows 10/11 (64-bit)
- 4 GB RAM
- 2 GB free disk space
- Administrator rights for installation

### Supported Vehicles
- Holden Commodore VF (2013-2017)
- Volkswagen Golf Mk6 (2009-2013)
- Extensible framework for additional vehicles

## Build Instructions

### Prerequisites
1. Python 3.9+ with pip
2. Node.js 16+ with npm
3. Git

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/muts.git
cd muts
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Step 3: Install Frontend Dependencies
```bash
cd electron-app
npm install
cd ..
```

### Step 4: Build Application
```bash
# Run the build script
python build.py
```

This will:
1. Build the Python backend into a standalone executable
2. Package the Electron frontend
3. Create both installer and portable versions

## Installation

### Option 1: Installer (Recommended)
1. Navigate to `electron-app/dist-electron`
2. Run `MUTS Setup X.X.X.exe`
3. Follow the installation wizard
4. Launch from Start Menu or Desktop shortcut

### Option 2: Portable
1. Navigate to `dist/MUTS-Portable`
2. Extract to desired location
3. Run `START_MUTS.bat` or `MUTS.exe`

## First Run Setup

### Database Initialization
On first launch, the application will:
1. Create the SQLite database
2. Run migrations
3. Seed OEM vehicle data
4. Create default admin user

### Vehicle Profiles
The application includes pre-configured profiles for:
- **Holden Commodore VF Evoke Wagon V6 3.0 6AT (2015)**
  - VIN: 6G1FA8E53FL100333
  - Plate: JBG175
  - Engine: LFW142510158

- **Volkswagen Golf Mk6 TSI 90kW 1.4 7DSG (2011)**
  - VIN: WVWZZZ1KZBW232050
  - Plate: GBF28
  - Engine: CAX767625

## Usage

### Starting the Application
- **Installed Version**: Use Start Menu shortcut
- **Portable Version**: Run `MUTS.exe`
- The Python backend starts automatically

### Adding Vehicles
1. Click "My Vehicles" tab
2. Click "Add Vehicle"
3. Enter VIN and vehicle details
4. Save profile

### Diagnostics
1. Select vehicle from "My Vehicles"
2. Navigate to Diagnostics module
3. Supported modules will be enabled
4. Unsupported modules show "Not supported"

### Virtual Dyno
1. Connect to vehicle
2. Record telemetry session
3. Process in Virtual Dyno
4. View torque/power curves
5. DSG vehicles show gear shifts

## Troubleshooting

### Backend Failed to Start
- Check Windows Defender isn't blocking the executable
- Run as Administrator if needed
- Check logs in `%APPDATA%/muts/logs`

### Database Errors
- Delete `database.db` and restart
- Ensure write permissions to app directory
- Check disk space

### Communication Errors
- Verify backend is running (check Task Manager)
- Restart the application
- Check firewall settings

## Development

### Running in Development Mode
```bash
# Terminal 1: Start backend
python -m app.api.main

# Terminal 2: Start frontend
cd electron-app
npm run dev
```

### Adding New Vehicles
1. Create OEM constants in `VehicleConstantsPreset`
2. Add diagnostics template
3. Update vehicle selector
4. Run smoke tests

## File Structure

```
MUTS/
├── app/                    # Python backend
│   ├── muts/             # Core modules
│   ├── api/              # Flask API endpoints
│   └── migrations/       # Database migrations
├── electron-app/          # Electron frontend
│   ├── main.js          # Main process
│   ├── renderer.js      # Renderer process
│   └── build/           # Build assets
├── build/                # Build configuration
├── docs/                 # Documentation
└── dist/                 # Build output
```

## Support

For issues and support:
1. Check the troubleshooting guide
2. Review logs in `%APPDATA%/muts/logs`
3. Submit issues to GitHub repository
4. Contact support team

## License

MUTS Vehicle Diagnostics - Copyright © 2025
Licensed under MIT License - see LICENSE file for details
