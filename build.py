#!/usr/bin/env python3
"""
Build script for MUTS application
Creates a standalone installer with bundled Python backend
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Configuration
ROOT_DIR = Path(__file__).parent
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"
BACKEND_DIST = ROOT_DIR / "dist-backend"

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning previous builds...")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR, BACKEND_DIST]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_path}")
    
    # Clean electron build artifacts
    electron_dist = ROOT_DIR / "electron-app" / "dist"
    if electron_dist.exists():
        shutil.rmtree(electron_dist)
        print(f"  Removed {electron_dist}")

def build_backend():
    """Build Python backend with PyInstaller"""
    print("\nBuilding Python backend...")
    
    # Check if PyInstaller is installed
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: PyInstaller not found. Install with: pip install pyinstaller")
        return False
    
    # Run PyInstaller
    spec_file = BUILD_DIR / "backend.spec"
    cmd = ["pyinstaller", "--clean", str(spec_file)]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)
    
    if result.returncode != 0:
        print("ERROR: PyInstaller build failed")
        return False
    
    # Move the executable to dist-backend
    backend_exe = DIST_DIR / "muts-backend.exe"
    if backend_exe.exists():
        BACKEND_DIST.mkdir(exist_ok=True)
        shutil.move(str(backend_exe), str(BACKEND_DIR / "muts-backend.exe"))
        print(f"  Backend executable: {BACKEND_DIR / 'muts-backend.exe'}")
        return True
    else:
        print("ERROR: Backend executable not found")
        return False

def build_frontend():
    """Build Electron frontend"""
    print("\nBuilding Electron frontend...")
    
    # Install dependencies if needed
    node_modules = ROOT_DIR / "electron-app" / "node_modules"
    if not node_modules.exists():
        print("Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=ROOT_DIR / "electron-app", check=True)
    
    # Build with electron-builder
    cmd = ["npm", "run", "electron:build"]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=ROOT_DIR / "electron-app")
    
    if result.returncode != 0:
        print("ERROR: Electron build failed")
        return False
    
    return True

def create_portable_package():
    """Create a portable package without installer"""
    print("\nCreating portable package...")
    
    portable_dir = DIST_DIR / "MUTS-Portable"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir()
    
    # Copy built electron app
    electron_dist = ROOT_DIR / "electron-app" / "dist-electron"
    for item in electron_dist.iterdir():
        if item.is_dir() and "win-unpacked" in item.name:
            shutil.copytree(item, portable_dir / "MUTS", ignore=shutil.ignore_patterns("*.pdb"))
            break
    
    # Ensure backend is in place
    backend_dest = portable_dir / "MUTS" / "resources" / "backend"
    backend_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BACKEND_DIR / "muts-backend.exe", backend_dest / "muts-backend.exe")
    
    # Create startup script
    startup_script = portable_dir / "MUTS" / "START_MUTS.bat"
    with open(startup_script, 'w') as f:
        f.write('@echo off\n')
        f.write('cd /d "%~dp0"\n')
        f.write('echo Starting MUTS Vehicle Diagnostics...\n')
        f.write('MUTS.exe\n')
        f.write('pause\n')
    
    print(f"  Portable package created: {portable_dir}")
    return True

def main():
    """Main build process"""
    print("="*60)
    print("MUTS Vehicle Diagnostics - Build Script")
    print("="*60 + "\n")
    
    # Check platform
    if platform.system() != "Windows":
        print("WARNING: Build script optimized for Windows")
        print("For Linux/Mac, adjust the paths and executable names")
    
    # Step 1: Clean
    clean_build()
    
    # Step 2: Build backend
    if not build_backend():
        sys.exit(1)
    
    # Step 3: Build frontend
    if not build_frontend():
        sys.exit(1)
    
    # Step 4: Create portable package
    if not create_portable_package():
        sys.exit(1)
    
    # Success
    print("\n" + "="*60)
    print("BUILD COMPLETE!")
    print("="*60)
    print(f"\nInstaller location: {ROOT_DIR}/electron-app/dist-electron")
    print(f"Portable package: {DIST_DIR}/MUTS-Portable")
    print("\nThe application includes:")
    print("  • Complete offline functionality")
    print("  • Auto-starting Python backend")
    print("  • Vehicle profiles for Holden VF and VW Golf")
    print("  • All diagnostics and dyno features")
    print("="*60)

if __name__ == "__main__":
    main()
