# Fixing AUTH_KEY_DUPLICATED Error

## The Problem

You're seeing `AUTH_KEY_DUPLICATED` errors because the same Telegram session string is being used in multiple places simultaneously. Telegram only allows **ONE active connection per session** at a time.

## Common Causes

1. **Running locally AND on Railway** - Most common cause
2. **Multiple Railway deployments** - Using the same session string
3. **Previous deployment still running** - Old instance didn't shut down properly
4. **Another application** - Using the same session string

## Solution: Generate a New Session for Railway

### Step 1: Stop All Other Instances

**Check locally:**
```bash
# Check if worker is running locally
ps aux | grep ingest.py
# If found, stop it:
pkill -f ingest.py
```

**Check Railway:**
- Go to Railway dashboard
- Check if there are multiple deployments running
- Stop any old/duplicate deployments

### Step 2: Generate a New Session String

**Option A: Using the provided script (Recommended)**

```bash
cd worker
python3 generate_session.py
```

This will:
1. Prompt you to press Enter
2. Start the Telegram client
3. Ask you to log in (if needed)
4. Generate a new session string
5. Display it in the terminal

**Option B: Manual generation**

```python
from pyrogram import Client

API_ID = YOUR_API_ID
API_HASH = "YOUR_API_HASH"

app = Client("railway_session", api_id=API_ID, api_hash=API_HASH)
app.start()
session_string = app.export_session_string()
print(f"Session string: {session_string}")
app.stop()
```

### Step 3: Update Railway Environment Variable

1. Go to Railway Dashboard → Your Service → Variables
2. Find `SESSION_STRING`
3. Replace it with the NEW session string from Step 2
4. Save

### Step 4: Redeploy

1. Railway will auto-redeploy when you save the variable, OR
2. Push a new commit to trigger deployment, OR
3. Manually trigger redeploy from Railway dashboard

## Verification

After redeploying, check the logs:

**✅ Success looks like:**
```
Starting Telegram worker...
Telegram client started
Successfully connected to channel: @batarikh
Listening for messages from channel: @batarikh
```

**❌ Still failing?**
- Check that you stopped ALL local instances
- Verify the new session string is correct
- Check Railway logs for other errors
- Make sure no other Railway deployments are using the same session

## Prevention

**Best Practice:**
- Use **separate sessions** for different environments:
  - One session for local development
  - One session for Railway production
  - Never use the same session in two places

**How to manage multiple sessions:**

1. **Local development:**
   ```bash
   # Use a local session file
   python3 generate_session.py
   # Save to .env.local
   ```

2. **Railway production:**
   ```bash
   # Generate a separate session
   python3 generate_session.py
   # Copy to Railway SESSION_STRING variable
   ```

## Troubleshooting

### Error persists after generating new session

1. **Wait 1-2 minutes** - Telegram might need time to release the old session
2. **Check Railway logs** - Look for other error messages
3. **Verify session string** - Make sure it's copied correctly (no extra spaces)
4. **Check for multiple Railway services** - You might have duplicate services

### Session string is very long

This is normal! Session strings can be 300+ characters. Make sure you copy the ENTIRE string.

### Can't generate session locally

Make sure:
- `API_ID` and `API_HASH` are set correctly
- You have internet connection
- No firewall blocking Telegram
- You're not already logged in elsewhere with the same credentials

## Quick Checklist

- [ ] Stopped all local instances
- [ ] Stopped duplicate Railway deployments
- [ ] Generated NEW session string
- [ ] Updated `SESSION_STRING` in Railway
- [ ] Redeployed
- [ ] Verified logs show successful connection

## Still Having Issues?

If the error persists:
1. Double-check that NO other instance is running
2. Generate a completely fresh session string
3. Wait 5 minutes after stopping old instances
4. Check Railway logs for other errors
5. Verify all environment variables are set correctly

