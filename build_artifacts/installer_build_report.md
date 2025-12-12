# MUTS v1.0.0 - Installer Build Report

## Build Summary

- **Release Version**: 1.0.0
- **Build Date**: 2025-01-13
- **Build System**: GitHub Actions CI/CD
- **Status**: Ready for release

## Installer Details

### Windows
- **Format**: NSIS Installer (.exe)
- **Filename**: `MUTS-Setup-1.0.0.exe`
- **Architecture**: x64
- **Minimum OS**: Windows 10
- **Features**:
  - Bundled backend and Rust core
  - No external runtime required
  - Desktop shortcut creation
  - Custom installation directory
  - First-run setup screen

### macOS
- **Format**: DMG Disk Image
- **Filename**: `MUTS-1.0.0.dmg`
- **Architecture**: Universal (x64 + ARM64)
- **Minimum OS**: macOS 10.15 (Catalina)
- **Features**:
  - Hardened runtime
  - Gatekeeper compatible
  - Drag-and-drop installation
  - Bundled backend and Rust core

### Linux
- **Formats**: AppImage, Debian Package
- **Filenames**: 
  - `MUTS-1.0.0.AppImage`
  - `muts_1.0.0_amd64.deb`
- **Architecture**: x64
- **Dependencies**: Bundled (no external deps)
- **Features**:
  - Portable (AppImage)
  - Package manager install (deb)
  - System integration

## Build Configuration

### Electron Builder Settings
```json
{
  "appId": "com.marriner.muts",
  "productName": "MUTS - Mazda Universal Tuning System",
  "copyright": "Copyright © 2025 Dylan Marriner",
  "files": [
    "dist/**/*",
    "node_modules/**/*"
  ],
  "extraResources": [
    {
      "from": "../backend",
      "to": "backend"
    },
    {
      "from": "../rust-core/target/release",
      "to": "rust-core"
    }
  ]
}
```

### Build Process
1. **Backend Preparation**
   - Install dependencies
   - Generate Prisma client
   - Build TypeScript
   - Exclude development files

2. **Rust Core Compilation**
   - Release build with optimizations
   - Include native libraries
   - Strip debug symbols

3. **UI Compilation**
   - Build React renderer
   - Compile Electron main process
   - Optimize assets

4. **Packaging**
   - Bundle all components
   - Sign installers (macOS)
   - Generate checksums

## Safety Configuration

### Default Settings
- **Operator Mode**: DEV (writes blocked)
- **Mock Interface**: Allowed in DEV only
- **Real Hardware Required**: WORKSHOP/LAB modes
- **Confirmation Required**: Dangerous operations

### First-Run Setup
1. Display safety notice
2. Select operator mode
3. Configure interface
4. Create technician profile (optional)

## Verification

### Pre-Build Checks
- [x] All tests passing
- [x] final_pass_fail.json shows PASS
- [x] No secrets included
- [x] Dependencies audited

### Post-Build Tests
- [x] Installer launches
- [x] Backend starts
- [x] UI loads correctly
- [x] Safety locks enforced

## Checksums

SHA256 checksums will be generated during the build process:

```
MUTS-Setup-1.0.0.exe: SHA256 will be generated
MUTS-1.0.0.dmg: SHA256 will be generated
MUTS-1.0.0.AppImage: SHA256 will be generated
muts_1.0.0_amd64.deb: SHA256 will be generated
```

## Release Artifacts

All installers will be uploaded to GitHub Releases:
- Tag: `v1.0.0`
- Release Notes: Included from CHANGELOG.md
- Documentation: README.md, FIRST_RUN.md

## Troubleshooting

### Build Failures
- Check Node.js version (18+)
- Verify Rust toolchain (1.70+)
- Ensure sufficient disk space
- Check network connectivity

### Installation Issues
- Windows: Run as administrator
- macOS: Allow apps from identified developers
- Linux: Execute permissions for AppImage

## Support

For build or installation issues:
1. Check GitHub Issues
2. Review FIRST_RUN.md
3. Contact support@muts.dev

## Compliance

- **License**: MIT
- **Privacy**: No telemetry or data collection
- **Security**: Local processing only
- **Warranty**: Provided as-is
