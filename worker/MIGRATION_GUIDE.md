# Migration from media.batarikh.xyz to batarikhmedia.stream

## The Problem

You previously used `media.batarikh.xyz` (likely a Vercel proxy) to serve R2 files. Now you have a direct R2 custom domain `batarikhmedia.stream`. This caused a conflict where:

1. **Worker** was trying to use the old URL or wrong URL
2. **Web app** was configured for `media.batarikh.xyz` but receiving URLs with `batarikhmedia.stream`
3. **Next.js Image optimization** was rejecting images (hostname mismatch)
4. **Download route** was rejecting PDFs (hostname mismatch)

## What I Fixed

### Code Changes
- ✅ Updated `DEFAULT_MEDIA_HOST` in `web/src/lib/constants.ts` to `batarikhmedia.stream`
- ✅ Updated `next.config.ts` default hostname to `batarikhmedia.stream`
- ✅ Worker now validates URLs before sending to Supabase

### What You Need to Do

#### 1. Update Railway Environment Variables

Go to Railway → Your Worker Service → Variables:

```
R2_PUBLIC_BASE_URL=https://batarikhmedia.stream
```

**Important**: No trailing slash!

#### 2. Update Vercel Environment Variables

Go to Vercel → Your Web App → Settings → Environment Variables:

```
NEXT_PUBLIC_MEDIA_HOST=batarikhmedia.stream
```

#### 3. Verify R2 Custom Domain

In Cloudflare Dashboard → R2 → Your Bucket:
- Custom Domain `batarikhmedia.stream` should show:
  - Status: **Active** ✅
  - Access: **Enabled** ✅

#### 4. Test the Setup

**Test R2 URL directly:**
```bash
curl -I https://batarikhmedia.stream/
```
Should return `200 OK`, not `401 Unauthorized`.

**Test in browser:**
- Open `https://batarikhmedia.stream/` 
- Should NOT show "Error 401 - This bucket cannot be viewed"

#### 5. Redeploy

After updating environment variables:
- **Railway**: Will auto-restart, or manually restart
- **Vercel**: Will auto-redeploy, or manually redeploy

#### 6. Verify Everything Works

1. **Check Railway logs**:
   - Should see: `Upserted post id=... type=image media_url=set`
   - Should NOT see: `R2 bucket access issue` or `Invalid media_url`

2. **Check web app**:
   - Images should load (Next.js Image optimization working)
   - PDFs should download (download route working)
   - No console errors about hostname mismatches

## Migration Checklist

- [ ] Set `R2_PUBLIC_BASE_URL=https://batarikhmedia.stream` in Railway
- [ ] Set `NEXT_PUBLIC_MEDIA_HOST=batarikhmedia.stream` in Vercel
- [ ] Verify R2 custom domain is Active and Enabled
- [ ] Test R2 URL directly (should return 200, not 401)
- [ ] Restart Railway worker
- [ ] Redeploy Vercel web app
- [ ] Check Railway logs - should see successful upserts
- [ ] Check web app - images and media should load
- [ ] Test PDF download - should work

## If You Want to Keep Using media.batarikh.xyz

If you prefer to keep using `media.batarikh.xyz` as a proxy:

1. **Configure Vercel Rewrite**:
   - Go to Vercel → Your Project → Settings → Rewrites
   - Add rewrite: `media.batarikh.xyz/*` → `https://batarikhmedia.stream/*`

2. **Keep environment variables**:
   - Railway: `R2_PUBLIC_BASE_URL=https://media.batarikh.xyz`
   - Vercel: `NEXT_PUBLIC_MEDIA_HOST=media.batarikh.xyz`

3. **Update DNS**:
   - Point `media.batarikh.xyz` to Vercel (if not already)

**However**, using the direct R2 domain (`batarikhmedia.stream`) is simpler and more efficient (no proxy layer).

## Troubleshooting

### Images Not Loading in Web App

1. Check browser console for errors
2. Verify `NEXT_PUBLIC_MEDIA_HOST` is set correctly in Vercel
3. Check Next.js Image remotePatterns in `next.config.ts`
4. Verify the media URL in Supabase matches the hostname

### PDF Downloads Not Working

1. Check `NEXT_PUBLIC_MEDIA_HOST` in Vercel
2. Check download route validation in `web/src/app/download/route.ts`
3. Verify media URLs in Supabase use the correct hostname

### Still Getting 401 Errors

1. Check Railway logs for `R2_PUBLIC_BASE_URL is set to: ...`
2. Verify R2 bucket has public access enabled
3. Test R2 URL directly in browser
4. Check Cloudflare R2 custom domain status

