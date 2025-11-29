# Railway Dependency Installation Fix

## The Problem
Railway is not installing Python dependencies from `requirements.txt`, causing `ModuleNotFoundError: No module named 'dotenv'`.

## Immediate Solution (Runtime Installation)

I've created `start.sh` which will automatically install dependencies at runtime if they're missing. This is a workaround until Railway is properly configured.

**The script will:**
1. Check if dependencies are installed
2. If not, install them from `requirements.txt`
3. Then start the worker

## Permanent Fix: Configure Railway Properly

### Step 1: Set Root Directory (CRITICAL)

1. Go to Railway Dashboard → Your Service → Settings
2. Find **"Root Directory"** or **"Source"**
3. Set it to: `worker`
4. **This is the most important step!**

### Step 2: Verify Build Logs

After setting root directory, check the build logs. You should see:
```
Installing dependencies from requirements.txt
Successfully installed python-dotenv-1.2.1
Successfully installed pyrogram-2.0.106
...
```

If you DON'T see this, Railway is not detecting it as a Python project.

### Step 3: Remove package.json (if causing issues)

If Railway is detecting it as Node.js instead of Python:

```bash
# In your local repo
rm worker/package.json
git commit -m "Remove package.json to fix Railway Python detection"
git push
```

### Step 4: Manual Build Command (if needed)

In Railway service settings, you can manually set:
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `bash start.sh` (or `python ingest.py` if dependencies are installed)

## Current Workaround

The `start.sh` script will install dependencies at runtime if they're missing. This means:
- ✅ Worker will start even if Railway doesn't install dependencies during build
- ⚠️ Slightly slower startup (installs dependencies on first run)
- ⚠️ Not ideal for production (should install during build)

## Verification

After deploying, check logs for:
1. "Dependencies not found. Installing from requirements.txt..." (if runtime install happens)
2. OR "Dependencies already installed." (if build install worked)
3. "Starting worker..."
4. "Telegram client started"

If you see the runtime installation message, Railway is still not installing during build - you need to fix the root directory setting.

