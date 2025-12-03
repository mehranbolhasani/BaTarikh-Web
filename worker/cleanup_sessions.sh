#!/bin/bash
# Cleanup script to remove old session files

cd "$(dirname "$0")"

echo "Cleaning up old session files..."
rm -f *.session
rm -f gen.session
rm -f session_generator*.session
rm -f telegram_worker.session

echo "✓ Session files cleaned up"
echo ""
echo "You can now run ./generate_session.sh to create a new session"

