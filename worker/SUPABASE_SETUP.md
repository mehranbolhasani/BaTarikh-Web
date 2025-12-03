# Supabase Configuration for Worker

## The Problem

Posts are being processed by the worker but not appearing in the web app because they're not being saved to Supabase.

## Required Environment Variables

The worker needs **TWO** Supabase variables:

1. **`SUPABASE_URL`** ⚠️ **MISSING**
   - The Supabase project URL
   - Same value as `NEXT_PUBLIC_SUPABASE_URL`
   - Used by worker to connect to Supabase

2. **`SUPABASE_SERVICE_ROLE_KEY`** ✅ (you have this)
   - The service role key (has admin privileges)
   - Used by worker to write to database

## How to Fix

### Step 1: Add SUPABASE_URL

1. Go to Railway Dashboard → Your Service → Variables
2. Click "+ New Variable"
3. Set:
   - **Name**: `SUPABASE_URL`
   - **Value**: Copy the value from `NEXT_PUBLIC_SUPABASE_URL`
4. Save

### Step 2: Verify Both Variables

You should have:
- ✅ `SUPABASE_URL` (for worker)
- ✅ `SUPABASE_SERVICE_ROLE_KEY` (for worker)
- ✅ `NEXT_PUBLIC_SUPABASE_URL` (for web app)
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY` (for web app)

### Step 3: Check Logs

After adding `SUPABASE_URL`, restart the service and check logs. You should see:
```
INFO Supabase client initialized successfully
INFO Upserted post id=1257 type=image
```

Instead of:
```
WARNING SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; will skip DB upserts
```

## Why Two Different Variables?

- **Worker** uses `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (admin access to write)
- **Web App** uses `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` (read-only access)

They point to the same Supabase project, but use different authentication methods.

## After Adding SUPABASE_URL

1. **Restart the service** (or it will auto-restart)
2. **Check logs** - Should see "Supabase client initialized successfully"
3. **New posts** will automatically be saved
4. **To backfill the 3 posts**, set `BACKFILL_LIMIT=3` and `BACKFILL_ON_START=1`, then redeploy

## Verification

After fixing, check Railway logs for:
- ✅ "Supabase client initialized successfully"
- ✅ "Upserted post id=..." messages
- ✅ Posts appear in your web app

