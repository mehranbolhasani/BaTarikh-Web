# Worker Reliability Guide

This document describes the reliability improvements made to the Telegram worker and how to configure them.

## Key Improvements

### 1. Automatic Reconnection
- **What**: The worker automatically detects connection drops and reconnects to Telegram
- **How**: Connection monitor runs every 30 seconds and attempts reconnection with exponential backoff
- **Config**: `MAX_RESTARTS` (default: 10), reconnection delays start at 5 seconds

### 2. Message Retry Queue
- **What**: Failed messages are queued and retried automatically
- **How**: In-memory queue stores failed messages with exponential backoff retry logic
- **Config**: 
  - `MAX_MESSAGE_RETRIES` (default: 5)
  - `RETRY_DELAY_BASE_SECS` (default: 60)

### 3. Circuit Breakers
- **What**: Prevents cascading failures by temporarily disabling failing services
- **How**: Tracks failures and opens circuit after threshold, automatically closes after timeout
- **Services**: R2 storage and Supabase
- **Config**: 
  - Failure threshold: 5 failures
  - Timeout: 60 seconds

### 4. Resource Limits
- **What**: Prevents memory exhaustion from large images
- **How**: 
  - Limits image file size (default: 50MB)
  - Limits image dimensions (default: 8K)
  - Automatic garbage collection every 10 messages
- **Config**:
  - `MAX_IMAGE_SIZE_BYTES` (default: 52428800 = 50MB)
  - `MAX_IMAGE_DIMENSION` (default: 8192 = 8K)

### 5. Graceful Shutdown
- **What**: Handles shutdown signals properly to avoid data loss
- **How**: SIGTERM/SIGINT handlers stop processing gracefully
- **Benefit**: Messages in progress complete before shutdown

### 6. Process Supervisor
- **What**: Optional supervisor script monitors and restarts worker
- **How**: Runs worker as subprocess and restarts on failure
- **Config**:
  - `SUPERVISOR_MAX_RESTARTS` (default: 100)
  - `SUPERVISOR_RESTART_DELAY` (default: 10 seconds)

### 7. Enhanced Error Handling
- **What**: Better error recovery and logging
- **How**: 
  - Errors don't crash the worker
  - Failed operations are logged and queued for retry
  - Connection errors trigger automatic reconnection

### 8. Health Monitoring
- **What**: Status endpoint shows worker health
- **Endpoint**: `/status` or `/health`
- **Metrics**: 
  - Connection status
  - Processed/failed/retried counts
  - Queue size
  - Circuit breaker states
  - Last error

## Configuration

### Environment Variables

```bash
# Reconnection
MAX_RESTARTS=10                    # Max worker restarts before giving up

# Message Retry
MAX_MESSAGE_RETRIES=5              # Max retries per message
RETRY_DELAY_BASE_SECS=60           # Base delay between retries (exponential backoff)

# Resource Limits
MAX_IMAGE_SIZE_BYTES=52428800      # Max image file size (50MB)
MAX_IMAGE_DIMENSION=8192           # Max image width/height (8K)

# Supervisor (if using supervisor.py)
SUPERVISOR_MAX_RESTARTS=100        # Max supervisor restarts
SUPERVISOR_RESTART_DELAY=10        # Delay between restarts (seconds)
WORKER_SCRIPT="python ingest.py"   # Worker command

# Existing variables
HEARTBEAT_SECS=60                  # Heartbeat interval
BACKFILL_ON_START=0                # Run backfill on startup
BACKFILL_LIMIT=0                   # Number of messages to backfill
```

## Deployment Options

### Option 1: Direct Execution (Railway Default)
Railway's restart policy handles restarts automatically:
```bash
python ingest.py
```

### Option 2: With Supervisor (Extra Protection)
Use supervisor for additional monitoring:
```bash
python supervisor.py
```

Update `start.sh`:
```bash
#!/bin/bash
exec python supervisor.py
```

### Option 3: Using Railway Restart Policy
Railway's `restartPolicyType: ON_FAILURE` already configured in `railway.json`.

## Monitoring

### Health Check Endpoint
```bash
curl https://your-app.railway.app/status
```

Response:
```json
{
  "ok": true,
  "stats": {
    "started_at": "2024-01-01T00:00:00Z",
    "processed": 100,
    "failed": 2,
    "retried": 1,
    "connected": true,
    "queue_size": 0,
    "r2_circuit_breaker": "closed",
    "supabase_circuit_breaker": "closed"
  }
}
```

### Key Metrics to Monitor
1. **`connected`**: Should always be `true`
2. **`failed`**: Should be low relative to `processed`
3. **`queue_size`**: Should be 0 or small
4. **Circuit breakers**: Should be `closed` (not `open`)

## Troubleshooting

### Worker Keeps Restarting
1. Check logs for specific errors
2. Verify environment variables are set correctly
3. Check if `AUTH_KEY_DUPLICATED` error (session conflict)
4. Verify channel access permissions

### Messages Not Processing
1. Check `connected` status
2. Verify channel membership
3. Check circuit breaker states
4. Review error logs for specific failures

### High Memory Usage
1. Reduce `MAX_IMAGE_SIZE_BYTES`
2. Reduce `MAX_IMAGE_DIMENSION`
3. Disable image format conversion (`ENABLE_WEBP=0`, `ENABLE_AVIF=0`)
4. Reduce `IMAGE_SIZES` to fewer sizes

### Circuit Breaker Stuck Open
1. Check service health (R2/Supabase)
2. Verify credentials
3. Circuit breaker auto-closes after timeout (60s)
4. Check network connectivity

## Best Practices

1. **Monitor the `/status` endpoint** regularly
2. **Set up alerts** for:
   - `connected: false`
   - High `failed` count
   - Large `queue_size`
   - Circuit breakers `open`

3. **Use separate sessions** for different environments
4. **Monitor Railway logs** for patterns
5. **Test locally** before deploying changes

## Performance Tuning

### For High Volume
- Increase `MAX_MESSAGE_RETRIES` for better reliability
- Increase `RETRY_DELAY_BASE_SECS` to avoid rate limits
- Disable unnecessary image processing

### For Low Memory
- Reduce `MAX_IMAGE_SIZE_BYTES`
- Reduce `MAX_IMAGE_DIMENSION`
- Disable AVIF conversion (most memory-intensive)
- Process fewer image sizes

### For Stability
- Use supervisor script
- Increase `MAX_RESTARTS`
- Monitor circuit breakers
- Set up external monitoring/alerting

