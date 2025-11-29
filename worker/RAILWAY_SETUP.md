# Railway Deployment Setup

## Current Issue
Railway is not installing Python dependencies from `requirements.txt`, causing `ModuleNotFoundError: No module named 'dotenv'`.

## Solution

### Option 1: Configure Railway Service Settings (Recommended)

1. **Set Root Directory**:
   - Go to your Railway service settings
   - Under "Settings" → "Root Directory"
   - Set it to: `worker`
   - This ensures Railway looks in the correct directory for `requirements.txt`

2. **Set Build Command** (if available):
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python ingest.py`

3. **Set Python Version**:
   - Railway should auto-detect from `runtime.txt`
   - Or set environment variable: `PYTHON_VERSION=3.11.9`

### Option 2: Remove package.json (if not needed)

If the `package.json` is not needed, you can delete it to prevent Railway from detecting it as a Node.js project:

```bash
rm worker/package.json
```

### Option 3: Use Railway CLI

If you have Railway CLI installed:

```bash
railway link
railway variables set PYTHON_VERSION=3.11.9
railway up
```

## Verification

After deploying, check the build logs to ensure you see:
```
Installing dependencies from requirements.txt
Successfully installed python-dotenv-...
Successfully installed pyrogram-...
```

If you still see `ModuleNotFoundError`, the dependencies are not being installed during the build phase.

## Manual Build Command

If Railway doesn't auto-detect, you can set a custom build command in Railway settings:
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

## Environment Variables

Make sure all required environment variables are set in Railway:
- `API_ID`
- `API_HASH`
- `SESSION_STRING`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `R2_ENDPOINT`
- `R2_BUCKET`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_PUBLIC_BASE_URL`
- `TARGET_CHANNEL` (optional, defaults to "batarikh")

