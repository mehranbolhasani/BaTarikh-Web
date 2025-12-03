#!/bin/bash
set -e

echo "Checking Python dependencies..."

# Check if dotenv is installed, if not, install all requirements
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "Dependencies not found. Installing from requirements.txt..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    echo "Dependencies installed successfully!"
else
    echo "Dependencies already installed."
fi

echo "Starting worker..."
exec python3 ingest.py

