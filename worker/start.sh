#!/bin/bash
set -e

echo "Starting Telegram worker..."

# Fallback: Check if dotenv is installed (should already be installed in Docker)
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "WARNING: Dependencies not found. Installing from requirements.txt..."
    python3 -m pip install --quiet --upgrade pip
    python3 -m pip install --quiet -r requirements.txt
    echo "Dependencies installed successfully!"
fi

# Start the worker
exec python3 ingest.py

