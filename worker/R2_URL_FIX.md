# R2 URL Configuration Fix

## The Problem

You're getting 401 errors when Supabase tries to process `media_url` values. This happens because:

1. **R2 bucket is not publicly accessible** (even though you enabled it)
2. **`R2_PUBLIC_BASE_URL` is not set correctly** in Railway
3. **URL format is incorrect**

## What I Fixed

I've updated the code to:
- ✅ **Validate URLs** before sending to Supabase
- ✅ **Better error messages** showing what `R2_PUBLIC_BASE_URL` is set to
- ✅ **Skip invalid URLs** instead of failing the entire upsert
- ✅ **Improved URL construction** (handles trailing/leading slashes)

## What You Need to Do

### Step 1: Check Your R2 Public URL

From your Cloudflare dashboard, you have:
- **Custom Domain**: `batarikhmedia.stream` (Active, Enabled) ✅
- **Public Dev URL**: `https://pub-d303c0f67bda495ebddcb6a0d9b73d06.r2.dev` ✅

### Step 2: Set `R2_PUBLIC_BASE_URL` in Railway

Go to Railway → Your Worker Service → Variables, and set:

```
R2_PUBLIC_BASE_URL=https://batarikhmedia.stream
```

**OR** if you want to use the public dev URL:

```
R2_PUBLIC_BASE_URL=https://pub-d303c0f67bda495ebddcb6a0d9b73d06.r2.dev
```

**Important**: 
- Use the **custom domain** (`batarikhmedia.stream`) for production
- Make sure there's **no trailing slash** in the URL
- The URL should be accessible (test it in a browser)

### Step 3: Verify R2 Public Access

1. Go to Cloudflare Dashboard → R2 → Your Bucket (`batarikhweb`)
2. Check **"Public Development URL"** section:
   - Should show "Enabled" ✅
   - URL should be accessible
3. Check **"Custom Domains"** section:
   - `batarikhmedia.stream` should show "Active" and "Enabled" ✅

### Step 4: Test the URL

Test if your R2 URL works:

```bash
# Test custom domain
curl -I https://batarikhmedia.stream/

# Test public dev URL
curl -I https://pub-d303c0f67bda495ebddcb6a0d9b73d06.r2.dev/
```

Both should return `200 OK`, not `401 Unauthorized`.

### Step 5: Restart Worker

After updating `R2_PUBLIC_BASE_URL`:
1. Railway will auto-restart, OR
2. Manually restart the service

### Step 6: Check Logs

After restart, check Railway logs. You should see:
- ✅ `Upserted post id=... type=image media_url=set`
- ❌ NOT: `R2 bucket access issue` or `Invalid media_url`

## Troubleshooting

### Still Getting 401 Errors?

1. **Check `R2_PUBLIC_BASE_URL`**:
   ```bash
   # In Railway logs, look for:
   R2_PUBLIC_BASE_URL is set to: ...
   ```
   Make sure it matches your public URL exactly.

2. **Test URL directly**:
   - Open `https://batarikhmedia.stream/` in browser
   - Should NOT show "Error 401 - This bucket cannot be viewed"

3. **Check R2 Settings**:
   - Go to R2 → Your Bucket → Settings
   - "Public Development URL" should be **Enabled**
   - "Custom Domains" should show your domain as **Active**

4. **Verify CORS** (if needed):
   - Go to R2 → Your Bucket → CORS Policy
   - Add your web app domain if needed

### Posts Saved Without Media URLs?

If posts are saved but `media_url` is `null`:
- ✅ Posts will appear in web app
- ❌ Media won't load
- 🔧 Fix: Update `R2_PUBLIC_BASE_URL` and backfill again

## Quick Checklist

- [ ] `R2_PUBLIC_BASE_URL` is set in Railway
- [ ] URL matches your R2 public URL exactly (no trailing slash)
- [ ] R2 bucket has public access enabled
- [ ] Custom domain is active (if using custom domain)
- [ ] Tested URL in browser (should load, not 401)
- [ ] Worker restarted after updating variable
- [ ] Checked logs - should see successful upserts with `media_url=set`

## Expected Log Output

**Before fix:**
```
ERROR Failed to upsert post id=1259: {'message': 'JSON could not be generated', 'code': 401, ...}
```

**After fix:**
```
Upserted post id=1259 type=image media_url=set
```

Or if URL is invalid:
```
WARNING Invalid media_url for post id=1259, saving without it. URL: ...
R2_PUBLIC_BASE_URL is set to: ...
Upserted post id=1259 type=image media_url=none
```

