# Backfill Guide - Fetching Historical Messages

## What is Backfill?

Backfill allows the worker to process messages that were published **before** the worker started running. By default, the worker only processes **new** messages that arrive after it starts.

## How to Enable Backfill

### Step 1: Set Environment Variables in Railway

Go to Railway Dashboard → Your Service → Variables and add:

1. **`BACKFILL_ON_START=1`**
   - Enables backfill when the worker starts
   - Set to `1` to enable, `0` or unset to disable

2. **`BACKFILL_LIMIT=3`**
   - Number of recent messages to fetch
   - Set to `3` to get the last 3 posts
   - Set to `10` to get the last 10 posts, etc.

### Step 2: Redeploy

After setting the variables:
- Railway will auto-redeploy, OR
- Manually trigger a redeploy

### Step 3: Check Logs

After redeploy, you should see in the logs:
```
INFO Backfill progress: 1/3 messages processed
INFO Backfill progress: 2/3 messages processed
INFO Backfill progress: 3/3 messages processed
INFO Backfill completed: 3 messages processed
```

## Example Configuration

To fetch the last 5 messages on every startup:
- `BACKFILL_ON_START=1`
- `BACKFILL_LIMIT=5`

To fetch the last 10 messages once (then disable):
- `BACKFILL_ON_START=1`
- `BACKFILL_LIMIT=10`
- After it runs, set `BACKFILL_ON_START=0` to disable

## Important Notes

⚠️ **Rate Limits**: Telegram has rate limits. If you set a high `BACKFILL_LIMIT`, the worker will respect `FloodWait` errors and wait automatically.

⚠️ **One-Time vs Continuous**: 
- If `BACKFILL_ON_START=1`, it runs **every time** the worker starts
- To run it once, set the limit, let it run, then disable `BACKFILL_ON_START`

⚠️ **Processing Order**: Backfill processes messages from **newest to oldest** (most recent first)

## For Your Current Situation

To get the 3 posts that were published while the worker was down:

1. Set in Railway:
   - `BACKFILL_ON_START=1`
   - `BACKFILL_LIMIT=3`

2. Redeploy (or restart the service)

3. Check logs to confirm all 3 messages were processed

4. (Optional) After it completes, set `BACKFILL_ON_START=0` to disable future backfills

## Verifying Backfill Worked

1. **Check Railway logs** - Should see "Backfill completed: 3 messages processed"
2. **Check your web app** - The 3 posts should now appear
3. **Check Supabase** - If configured, posts should be in the database

