# CRITICAL Railway Fix

## The Problem
Railway is **NOT** installing Python dependencies, causing the worker to crash immediately.

## What You MUST Do in Railway Dashboard

### 1. Fix Root Directory (CRITICAL!)

**Current (WRONG):** `/worker`  
**Should be:** `worker` (without the leading slash)

**Steps:**
1. Go to Railway Dashboard → Your Service → Settings → Source
2. Find "Root Directory" field
3. Change from `/worker` to `worker` (remove the leading slash)
4. Save

**Why:** `/worker` is an absolute path that doesn't exist. `worker` is a relative path from the repo root.

### 2. Verify Build Command

In Settings → Build:
- **Custom Build Command** should be: `pip install --upgrade pip && pip install -r requirements.txt`

### 3. Verify Start Command

In Settings → Deploy:
- **Start Command** should be: `python ingest.py`

## What I've Done

I've added a **runtime dependency installer** directly in `ingest.py` that will:
1. Check if `dotenv` is installed
2. If not, automatically install all dependencies from `requirements.txt`
3. Then continue with normal startup

This ensures the worker will work **even if Railway doesn't install dependencies during build**.

## After Making Changes

1. **Save all Railway settings**
2. **Redeploy** (or push a new commit to trigger deployment)
3. **Check logs** - you should see:
   - Either: "Dependencies already installed" (if build worked)
   - Or: "Dependencies not found. Installing from requirements.txt..." (runtime install)
   - Then: "Starting Telegram worker..."
   - Then: "Telegram client started"

## If It Still Doesn't Work

Check the build logs in Railway. You should see:
```
Installing dependencies from requirements.txt
Successfully installed python-dotenv-...
Successfully installed pyrogram-...
```

If you DON'T see this in build logs, but the worker starts anyway, the runtime installer will handle it.

## Most Common Issue

The root directory being `/worker` instead of `worker` is the #1 cause of Railway not finding `requirements.txt`. Fix this first!

