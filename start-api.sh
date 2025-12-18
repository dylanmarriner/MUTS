#!/bin/bash
# Startup script for MUTS API server

echo "Starting MUTS API server..."
cd /mnt/excite/developing/MUTS
python -m app.api.main

# Alternative: uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
