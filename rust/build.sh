#!/bin/bash
# Build script for MUTS Versa Core Rust library

set -e

echo "Building MUTS Versa Core Rust library..."

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(dirname "$SCRIPT_DIR")}"
TARGET_DIR="${TARGET_DIR:-$SCRIPT_DIR/target}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_ROOT/core}"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "Target directory: $TARGET_DIR"
echo "Output directory: $OUTPUT_DIR"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "Error: Rust/Cargo not found. Please install Rust first."
    echo "Visit: https://rustup.rs/"
    exit 1
fi

# Check if Python development headers are available
python3 -c "import sysconfig; print(sysconfig.get_paths()['include'])" > /dev/null

# Install maturin if not present
if ! command -v maturin &> /dev/null; then
    echo "Installing maturin (Python-Rust build tool)..."
    pip install maturin
fi

# Build the library in release mode
echo "Building Rust library..."
cd "$SCRIPT_DIR"

# Build with maturin for Python integration
maturin build --release --target-dir "$TARGET_DIR"

# Copy the built library to the output directory
echo "Copying library to output directory..."
if [ -f "$TARGET_DIR/release/libmuts_versa_core.so" ]; then
    cp "$TARGET_DIR/release/libmuts_versa_core.so" "$OUTPUT_DIR/"
    echo "✓ Library copied to $OUTPUT_DIR/libmuts_versa_core.so"
elif [ -f "$TARGET_DIR/release/muts_versa_core.dll" ]; then
    cp "$TARGET_DIR/release/muts_versa_core.dll" "$OUTPUT_DIR/"
    echo "✓ Library copied to $OUTPUT_DIR/muts_versa_core.dll"
elif [ -f "$TARGET_DIR/release/libmuts_versa_core.dylib" ]; then
    cp "$TARGET_DIR/release/libmuts_versa_core.dylib" "$OUTPUT_DIR/"
    echo "✓ Library copied to $OUTPUT_DIR/libmuts_versa_core.dylib"
else
    echo "Warning: Could not find built library"
fi

# Test Python import
echo "Testing Python import..."
cd "$OUTPUT_DIR"
python3 -c "
try:
    import muts_versa_core
    print('✓ Rust core successfully imported!')
    print(f'Available functions: {dir(muts_versa_core)}')
except ImportError as e:
    print(f'✗ Failed to import Rust core: {e}')
    print('Using fallback implementations')
"

echo "Build complete!"
