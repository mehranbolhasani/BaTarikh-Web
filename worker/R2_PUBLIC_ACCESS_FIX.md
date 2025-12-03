# R2 Public Access Issue - Fix Guide

## The Problem

The logs show:
```
ERROR Failed to upsert post id=1259: {'message': 'JSON could not be generated', 'code': 401, ...}
Error 401 - This bucket cannot be viewed
You are not authorized to view this bucket
```

This means your R2 bucket is **not publicly accessible**. The worker uploads files successfully, but when Supabase tries to process the `media_url`, it gets a 401 error because the bucket requires authentication.

## Solutions

### Option 1: Enable Public Access on R2 Bucket (Recommended)

1. **Go to Cloudflare Dashboard** → R2 → Your Bucket
2. **Enable Public Access**:
   - Go to "Settings" → "Public Access"
   - Enable "Allow Access"
   - Configure CORS if needed
3. **Get Public URL**:
   - The public URL format is usually: `https://<account-id>.r2.cloudflarestorage.com/<bucket-name>`
   - Or if you have a custom domain: `https://your-domain.com`
4. **Update Railway Variable**:
   - Set `R2_PUBLIC_BASE_URL` to the public URL
   - Make sure it matches your bucket's public access URL

### Option 2: Use Custom Domain (Better for Production)

1. **Set up Custom Domain** in Cloudflare R2
2. **Update `R2_PUBLIC_BASE_URL`** to use your custom domain
3. **Configure CORS** for your web app domain

### Option 3: Current Workaround (Already Implemented)

I've updated the code to:
- **Detect R2 401 errors**
- **Save posts without `media_url`** if R2 access fails
- **Continue processing** other posts

This means:
- ✅ Posts will be saved to Supabase (without media URLs)
- ✅ Posts will appear in your web app (but media won't load)
- ⚠️ You need to fix R2 public access for media to work

## Verification

After enabling public access:

1. **Test R2 URL directly**:
   ```bash
   curl https://your-r2-public-url.com/path/to/file.jpg
   ```
   Should return the file, not a 401 error

2. **Check Railway logs**:
   - Should see: `Upserted post id=... type=image media_url=set`
   - Should NOT see: `R2 bucket access issue` warnings

3. **Check web app**:
   - Posts should appear
   - Media should load (if R2 is public)

## Current Status

The worker will now:
- ✅ Process messages successfully
- ✅ Save posts to Supabase (even if R2 fails)
- ✅ Continue working despite R2 issues
- ⚠️ Media URLs will be `null` until R2 is fixed

## Next Steps

1. **Enable R2 public access** (Option 1 or 2 above)
2. **Update `R2_PUBLIC_BASE_URL`** in Railway
3. **Restart worker** (or it will auto-restart)
4. **New posts** will have working media URLs
5. **Old posts** can be fixed by re-processing (backfill again)

## Quick Fix Checklist

- [ ] Go to Cloudflare R2 → Your Bucket → Settings
- [ ] Enable "Public Access"
- [ ] Copy the public URL
- [ ] Update `R2_PUBLIC_BASE_URL` in Railway
- [ ] Test a media URL in browser (should load, not 401)
- [ ] Check logs - should see successful upserts
- [ ] Check web app - media should load

