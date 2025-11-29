#!/bin/bash
set -e

echo "Checking Python dependencies..."

# Check if dotenv is installed, if not, install all requirements
if ! python -c "import dotenv" 2>/dev/null; then
    echo "Dependencies not found. Installing from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Dependencies installed successfully!"
else
    echo "Dependencies already installed."
fi

echo "Starting worker..."
exec python ingest.py

