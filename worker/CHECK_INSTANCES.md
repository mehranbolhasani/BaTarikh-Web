# Finding and Stopping Other Instances

## The Problem

You're getting `AUTH_KEY_DUPLICATED` because another instance is using the same Telegram session. Here's how to find and stop it:

## Step 1: Check Local Processes

**On macOS/Linux:**
```bash
# Check for running Python processes
ps aux | grep python | grep -i "ingest\|pyrogram\|telegram"

# Check for any process using port 8000 (worker health check)
lsof -i :8000

# Kill any found processes
pkill -f ingest.py
pkill -f pyrogram
```

## Step 2: Check Railway

1. **Go to Railway Dashboard**: https://railway.app
2. **Check your service**: Look for "BaTarikh-Web" or your worker service
3. **Check deployments**: See if there are multiple active deployments
4. **Stop the service**: If it's running, stop it temporarily:
   - Go to your service
   - Click "Settings"
   - Click "Delete" or "Stop" (you can redeploy later)

## Step 3: Delete Session Files

```bash
cd worker
./cleanup_sessions.sh
```

Or manually:
```bash
cd worker
rm -f *.session
rm -f gen.session
rm -f session_generator*.session
rm -f telegram_worker.session
```

## Step 4: Wait a Few Minutes

After stopping all instances, wait 2-3 minutes for Telegram to release the session lock.

## Step 5: Generate New Session

```bash
cd worker
./generate_session.sh
```

## Common Places to Check

1. **Terminal windows**: Check all open terminal tabs/windows
2. **Background processes**: Check if you started it with `&` or `nohup`
3. **Railway**: Most likely culprit - check Railway dashboard
4. **Docker containers**: If you ran it in Docker locally
5. **IDE run configurations**: Check if your IDE is running it

## Quick Checklist

- [ ] Checked all terminal windows
- [ ] Checked Railway dashboard (stopped service)
- [ ] Deleted all `.session` files
- [ ] Waited 2-3 minutes
- [ ] Generated new session

## If Still Failing

1. **Generate session on a different machine** (if possible)
2. **Use a different Telegram account** (temporary, just for Railway)
3. **Contact Telegram support** if the session seems permanently locked

