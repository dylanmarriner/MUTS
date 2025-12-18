#!/bin/bash
# Launch script for VersaTuner Electron App

echo "Starting VersaTuner Electron App..."
echo "=================================="

# Check if electron is installed
if ! command -v ./node_modules/.bin/electron &> /dev/null; then
    echo "Electron not found. Installing dependencies..."
    npm install
fi

# Set environment variables
export NODE_ENV=development

# Launch the app
echo "Launching app..."
./node_modules/.bin/electron .
