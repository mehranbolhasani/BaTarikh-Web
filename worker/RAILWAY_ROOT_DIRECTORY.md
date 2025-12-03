# Railway Root Directory Configuration

## The Problem

Railway is not detecting the Dockerfile because the root directory is not set correctly. The logs show:
```
skipping 'Dockerfile' at 'worker/Dockerfile' as it is not rooted at a valid path
```

## Solution: Set Root Directory in Railway

### Option 1: Set Root Directory to `worker` (Recommended)

1. Go to Railway Dashboard → Your Service → **Settings**
2. Find **"Root Directory"** or **"Source"** section
3. Set it to: `worker` (without leading slash, just `worker`)
4. Save
5. Redeploy

This tells Railway that the `worker` directory is the root for this service.

### Option 2: Use railway.json at Repo Root

I've created a `railway.json` at the repo root that points to `worker/Dockerfile`. This should work if Railway's root directory is set to the repo root (empty/default).

## Verification

After setting the root directory, check the build logs. You should see:
- ✅ `using build driver dockerfile` (not railpack)
- ✅ `Building Docker image...`
- ✅ Docker build steps

## Current Configuration

- **Dockerfile location**: `worker/Dockerfile`
- **railway.json location**: 
  - `worker/railway.json` (if root dir = `worker`)
  - `railway.json` (if root dir = repo root)

## If Still Not Working

1. **Check Railway Settings**:
   - Root Directory must be `worker` (relative path, no slash)
   - NOT `/worker` (absolute path - wrong)
   - NOT empty (will look in repo root)

2. **Verify Files Exist**:
   ```bash
   ls -la worker/Dockerfile
   ls -la worker/railway.json
   ```

3. **Check Build Logs**:
   - Should see "using build driver dockerfile"
   - Should NOT see "using build driver railpack"

