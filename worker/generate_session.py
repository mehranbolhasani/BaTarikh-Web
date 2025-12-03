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
import asyncio
import sys

# CRITICAL: Set up event loop BEFORE Pyrogram import (Python 3.10+ compatibility)
# Pyrogram's sync module calls asyncio.get_event_loop() during import
# In Python 3.10+, this requires an event loop to exist first

# For Python 3.10+, we need to create the loop before importing
if sys.version_info >= (3, 10):
    # Create and set event loop
    try:
        # Try to get existing loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except (RuntimeError, AttributeError):
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

# Now import Pyrogram (it will find the event loop we just created)
from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

if not API_ID or not API_HASH:
    print("ERROR: API_ID and API_HASH must be set!")
    print("Set them as environment variables or edit this script.")
    sys.exit(1)

async def generate_session():
    """Generate session string asynchronously."""
    print("=" * 80)
    print("Telegram Session String Generator")
    print("=" * 80)
    print()
    print("This will create a NEW session string for Railway deployment.")
    print("Make sure you're NOT running the worker locally or on Railway while doing this.")
    print()
    # Only prompt if running interactively (has a TTY)
    if sys.stdin.isatty():
        input("Press Enter to continue...")
    
    # Use a unique session name with timestamp to avoid conflicts
    import time
    session_name = f"session_generator_{int(time.time())}"
    app = Client(session_name, api_id=API_ID, api_hash=API_HASH)
    
    try:
        print("\nStarting client...")
        await app.start()
        print("✓ Client started successfully")
        
        print("\nExporting session string...")
        session_string = await app.export_session_string()
        
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
        sys.exit(1)
    finally:
        try:
            await app.stop()
        except:
            pass

if __name__ == "__main__":
    try:
        # Use the loop we created earlier
        if sys.version_info >= (3, 10):
            loop.run_until_complete(generate_session())
        else:
            asyncio.run(generate_session())
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)

