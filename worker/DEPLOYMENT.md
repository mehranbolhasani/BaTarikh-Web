# Deployment Guide - Docker-based Setup

## Overview

The worker now uses **Docker** for deployment, which provides:
- ✅ Reliable, reproducible builds
- ✅ Full control over the environment
- ✅ No dependency on Railway's buildpack detection
- ✅ Consistent behavior across environments

## What Changed

1. **Added `Dockerfile`** - Standard Python 3.11 image with all dependencies
2. **Removed `nixpacks.toml`** - No longer needed with Docker
3. **Updated `railway.json`** - Now uses Docker builder
4. **Added `.dockerignore`** - Optimizes Docker build context

## Railway Configuration

### Required Settings

1. **Root Directory**: Set to `worker` (not `/worker`)
2. **Builder**: Automatically uses Docker (from `railway.json`)
3. **Dockerfile Path**: `Dockerfile` (default, in root directory)

### Environment Variables

Make sure these are set in Railway:
- `API_ID` - Telegram API ID
- `API_HASH` - Telegram API Hash
- `SESSION_STRING` - Telegram session string
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `R2_ENDPOINT` - Cloudflare R2 endpoint
- `R2_BUCKET` - R2 bucket name
- `R2_ACCESS_KEY_ID` - R2 access key
- `R2_SECRET_ACCESS_KEY` - R2 secret key
- `R2_PUBLIC_BASE_URL` - R2 public URL base
- `TARGET_CHANNEL` - Telegram channel (optional, defaults to "batarikh")
- `PORT` - Port for health checks (optional, defaults to 8000)

### Optional Configuration Variables

- `MAX_MESSAGE_RETRIES` - Max retries per message (default: 5)
- `MAX_IMAGE_SIZE_BYTES` - Max image size (default: 50MB)
- `MAX_IMAGE_DIMENSION` - Max image dimensions (default: 8K)
- `HEARTBEAT_SECS` - Heartbeat interval (default: 60)
- `BACKFILL_ON_START` - Run backfill on startup (default: 0)
- `BACKFILL_LIMIT` - Number of messages to backfill (default: 0)

## Deployment Process

1. **Push to GitHub** - Railway auto-deploys on push
2. **Docker Build** - Railway builds the Docker image
3. **Deploy** - Railway starts the container
4. **Health Check** - Worker exposes `/status` endpoint

## Verification

After deployment, check:

1. **Build Logs**: Should show Docker build steps
   ```
   Step 1/7 : FROM python:3.11-slim
   Step 2/7 : WORKDIR /app
   Step 3/7 : RUN apt-get update...
   Step 4/7 : COPY requirements.txt .
   Step 5/7 : RUN pip install...
   ```

2. **Runtime Logs**: Should show worker starting
   ```
   Starting Telegram worker...
   Starting Telegram worker...
   Telegram client started
   ```

3. **Health Endpoint**: `curl https://your-app.railway.app/status`
   ```json
   {
     "ok": true,
     "stats": {
       "connected": true,
       "processed": 0
     }
   }
   ```

## Troubleshooting

### Build Fails

1. **Check Dockerfile syntax**: `docker build -t test .` locally
2. **Verify requirements.txt**: All packages should be valid
3. **Check Railway logs**: Look for specific error messages

### Worker Crashes

1. **Check environment variables**: All required vars must be set
2. **Check logs**: Look for Python errors or missing modules
3. **Verify session string**: Must be valid and not duplicated

### Connection Issues

1. **Check `/status` endpoint**: `connected` should be `true`
2. **Verify channel access**: Account must be member of channel
3. **Check session**: Must not be used elsewhere

## Local Testing

Test the Docker build locally:

```bash
cd worker
docker build -t telegram-worker .
docker run --env-file .env telegram-worker
```

## Advantages Over Nixpacks

1. **Predictable**: Docker images are consistent
2. **Debuggable**: Can test locally with exact same image
3. **Reliable**: No dependency on Railway's buildpack detection
4. **Fast**: Better layer caching
5. **Standard**: Uses industry-standard Docker

## Migration Notes

- Old deployments using Nixpacks will be replaced
- No data loss - all functionality remains the same
- Environment variables remain unchanged
- Health endpoint unchanged

## Support

If deployment fails:
1. Check Railway build logs
2. Verify `railway.json` configuration
3. Ensure root directory is set to `worker`
4. Check Dockerfile syntax
5. Verify all environment variables are set

