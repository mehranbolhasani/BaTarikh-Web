#!/usr/bin/env python3
"""
Helper script to generate a new Telegram session string for Railway deployment.

Usage:
    python3 generate_session.py
    # OR make it executable and run directly:
    chmod +x generate_session.py
    ./generate_session.py

Make sure to set API_ID and API_HASH environment variables or edit them in this script.
"""

import os
from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

if not API_ID or not API_HASH:
    print("ERROR: API_ID and API_HASH must be set!")
    print("Set them as environment variables or edit this script.")
    exit(1)

print("=" * 80)
print("Telegram Session String Generator")
print("=" * 80)
print()
print("This will create a NEW session string for Railway deployment.")
print("Make sure you're NOT running the worker locally or on Railway while doing this.")
print()
input("Press Enter to continue...")

app = Client("session_generator", api_id=API_ID, api_hash=API_HASH)

try:
    print("\nStarting client...")
    app.start()
    print("✓ Client started successfully")
    
    print("\nExporting session string...")
    session_string = app.export_session_string()
    
    print("\n" + "=" * 80)
    print("SUCCESS! Your new session string:")
    print("=" * 80)
    print()
    print(session_string)
    print()
    print("=" * 80)
    print()
    print("IMPORTANT: Copy this session string and update SESSION_STRING in Railway.")
    print("Make sure to:")
    print("  1. Stop any running instances using the old session")
    print("  2. Update SESSION_STRING environment variable in Railway")
    print("  3. Redeploy the worker")
    print()
    
except Exception as e:
    print(f"\nERROR: Failed to generate session string: {e}")
    print("\nPossible causes:")
    print("  - Invalid API_ID or API_HASH")
    print("  - Network connection issues")
    print("  - Another instance is using this session")
    exit(1)
finally:
    try:
        app.stop()
    except:
        pass

