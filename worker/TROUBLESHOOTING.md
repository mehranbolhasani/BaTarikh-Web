# Troubleshooting Telegram Worker

## Common Issues and Solutions

### Worker Not Receiving New Messages

#### 1. Check Channel Format
- **Issue**: Channel identifier might be incorrect
- **Solution**: Ensure `TARGET_CHANNEL` is set correctly:
  - For username: `batarikh` or `@batarikh` (both work)
  - For channel ID: Use numeric ID like `-1001234567890`
- **Check**: Look for log message "Listening for messages from channel: @batarikh"

#### 2. Verify Channel Membership
- **Issue**: The Telegram account must be a member of the channel
- **Solution**: 
  - Add the account to the channel as a member
  - Ensure the account has permission to read messages
- **Check**: Look for "Channel membership status" in logs

#### 3. Session String Issues
- **Issue**: Session might be expired or invalid
- **Solution**: 
  - Generate a new session string locally
  - Update `SESSION_STRING` environment variable
  - Session strings are account-specific and don't expire easily, but can become invalid if:
    - Account is logged out
    - Two-factor authentication is changed
    - Account is banned or restricted

#### 4. Railway Deployment Issues
- **Issue**: Worker might be crashing or not staying connected
- **Solution**:
  - Check Railway logs for errors
  - Verify all environment variables are set
  - Check if the worker is actually running (check status endpoint)
  - Ensure Railway service is not sleeping (use a paid plan or keep-alive)

#### 5. Network/Firewall Issues
- **Issue**: Railway might be blocking Telegram connections
- **Solution**: 
  - Telegram uses port 443 (HTTPS), which should be open
  - Check if Railway has any firewall rules blocking outbound connections

### Debugging Steps

1. **Check Status Endpoint**:
   ```bash
   curl https://your-railway-app.railway.app/status
   ```
   Should return JSON with `connected: true` and stats

2. **Check Logs**:
   - Look for "Telegram client started"
   - Look for "Successfully connected to channel"
   - Look for "Received message id=..." when new messages arrive
   - Check for any error messages

3. **Test Locally**:
   - Run the worker locally with the same environment variables
   - Send a test message to the channel
   - Verify it's received and processed

4. **Verify Environment Variables**:
   - `API_ID` and `API_HASH` - from https://my.telegram.org
   - `SESSION_STRING` - generated from a logged-in session
   - `TARGET_CHANNEL` - channel username or ID
   - All R2/Supabase variables if using those features

### Generating a New Session String

If you need to generate a new session string:

```python
from pyrogram import Client

api_id = YOUR_API_ID
api_hash = "YOUR_API_HASH"

app = Client("session_generator", api_id=api_id, api_hash=api_hash)
app.start()
session_string = app.export_session_string()
print(f"Session string: {session_string}")
app.stop()
```

### Monitoring

The worker exposes a status endpoint at `/status` that shows:
- Connection status
- Number of processed messages
- Last processed message ID
- Last error (if any)

Use this to monitor the worker's health.

