#!/bin/bash

echo "Installing MUTS Desktop dependencies..."

# Install Node backend dependencies
echo "Installing Node backend dependencies..."
cd node-backend
npm install

# Install Electron UI dependencies
echo "Installing Electron UI dependencies..."
cd ../electron-ui
npm install

# Build Rust core (requires rustc and cargo)
echo "Building Rust core..."
cd ../rust-core
cargo build --release

echo "Installation complete!"
echo ""
echo "To run the application:"
echo "1. cd node-backend && npm run dev"
echo "2. cd electron-ui && npm run dev"
