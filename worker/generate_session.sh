#!/bin/bash
# Helper script to generate Telegram session string
# This activates the virtual environment and runs the Python script

cd "$(dirname "$0")"
source venv/bin/activate
python3 generate_session.py

