import os
import time
import logging
import asyncio
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv
import re
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, AuthKeyDuplicated
from pyrogram.types import Message
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.s3.transfer import S3Transfer, TransferConfig
import mimetypes
from supabase import create_client, Client as SupabaseClient

mimetypes.add_type('image/avif', '.avif')
mimetypes.add_type('image/webp', '.webp')

load_dotenv()
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_BUCKET = os.getenv("R2_BUCKET")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "batarikh")

# Image processing toggles (optimize egress by reducing derivatives)
ENABLE_WEBP = os.getenv("ENABLE_WEBP", "1") == "1"
ENABLE_AVIF = os.getenv("ENABLE_AVIF", "0") == "1"
ENABLE_RESIZED_ORIGINALS = os.getenv("ENABLE_RESIZED_ORIGINALS", "0") == "1"
try:
    IMAGE_SIZES = [int(s.strip()) for s in os.getenv("IMAGE_SIZES", "1024").split(",") if s.strip().isdigit()]
except (ValueError, AttributeError) as e:
    logging.warning(f"Failed to parse IMAGE_SIZES, using default: {e}")
    IMAGE_SIZES = [1024]

missing = []
for k in ["API_ID", "API_HASH", "SESSION_STRING", "R2_ENDPOINT", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_PUBLIC_BASE_URL"]:
    if not os.getenv(k):
        missing.append(k)
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Configure client with explicit update settings
app = Client(
    "telegram_worker",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    no_updates=False,  # Explicitly enable updates
    workers=1,  # Use single worker for Railway deployment
)

r2 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(retries={"max_attempts": 5, "mode": "standard"}),
)

_transfer_cfg = TransferConfig(multipart_threshold=8 * 1024 * 1024, multipart_chunksize=8 * 1024 * 1024)
_transfer = S3Transfer(r2, config=_transfer_cfg)

supabase: Optional[SupabaseClient] = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logging.info("Supabase client initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")
        supabase = None
else:
    logging.warning("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; will skip DB upserts")

STATS = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "processed": 0,
    "last_id": None,
    "last_time": None,
    "last_error": None,
    "connected": False,
}

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/status"):
            body = json.dumps({
                "ok": True,
                "stats": STATS,
                "channel": TARGET_CHANNEL,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def start_status_server() -> None:
    try:
        port = int(os.getenv("PORT", "8000"))
    except (ValueError, TypeError) as e:
        logging.warning(f"Invalid PORT value, using default 8000: {e}")
        port = 8000
    try:
        server = HTTPServer(("0.0.0.0", port), StatusHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        logging.info(f"Status server listening on :{port}")
    except OSError as e:
        logging.error(f"Failed to start status server: {e}")

async def _download(msg: Message) -> Optional[str]:
    """Download media from Telegram message with retry logic."""
    max_retries = 10
    retry_count = 0
    while retry_count < max_retries:
        try:
            return await msg.download()
        except FloodWait as e:
            wait_time = e.value + 1
            logging.info(f"Rate limited, waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            retry_count += 1
        except Exception as e:
            logging.error(f"Failed to download media: {e}")
            return None
    logging.error(f"Max retries reached for download")
    return None

async def _media_info(msg: Message) -> Tuple[Optional[str], Optional[int], Optional[int], str]:
    """Extract media information from message."""
    try:
        if msg.photo:
            p = await _download(msg)
            width = getattr(msg.photo, "width", None)
            height = getattr(msg.photo, "height", None)
            return p, width, height, "image"
        if msg.video:
            p = await _download(msg)
            width = getattr(msg.video, "width", None)
            height = getattr(msg.video, "height", None)
            return p, width, height, "video"
        if msg.audio:
            p = await _download(msg)
            return p, None, None, "audio"
        if getattr(msg, 'document', None):
            # Detect PDFs specifically; otherwise mark as document
            mime = getattr(msg.document, 'mime_type', None)
            file_name = getattr(msg.document, 'file_name', '') or ''
            if (mime and mime.lower() == 'application/pdf') or file_name.lower().endswith('.pdf'):
                p = await _download(msg)
                return p, None, None, "document"
        return None, None, None, "none"
    except Exception as e:
        logging.error(f"Error extracting media info: {e}")
        return None, None, None, "none"

def _upload_to_r2(file_path: str, object_key: str) -> Optional[str]:
    """Upload file to R2 storage with retry logic."""
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None
    
    ct = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    max_attempts = 5
    attempts = 0
    
    while attempts < max_attempts:
        try:
            # Idempotency: skip upload if object already exists
            try:
                r2.head_object(Bucket=R2_BUCKET, Key=object_key)
                logging.debug(f"Object already exists: {object_key}")
                return f"{R2_PUBLIC_BASE_URL}/{object_key}"
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise
            # Upload file
            _transfer.upload_file(file_path, R2_BUCKET, object_key, extra_args={"ContentType": ct})
            logging.debug(f"Uploaded to R2: {object_key}")
            return f"{R2_PUBLIC_BASE_URL}/{object_key}"
        except ClientError as e:
            attempts += 1
            STATS["last_error"] = str(e)
            if attempts >= max_attempts:
                logging.error(f"Failed to upload after {max_attempts} attempts: {e}")
                raise
            wait_time = min(2 ** attempts, 10)
            logging.warning(f"Upload failed, retrying in {wait_time}s (attempt {attempts}/{max_attempts}): {e}")
            time.sleep(wait_time)
        except Exception as e:
            logging.error(f"Unexpected error during upload: {e}")
            STATS["last_error"] = str(e)
            raise
    return None

async def process_message(msg):
    fp, w, h, mt = await _media_info(msg)
    mu = None
    if fp:
        ext = os.path.splitext(fp)[1] if isinstance(fp, str) else ""
        key = f"{msg.chat.id}/{msg.id}{ext}"
        mu = _upload_to_r2(fp, key)
        if mt == "image" and HAS_PIL and isinstance(fp, str):
            try:
                with Image.open(fp) as im:
                    sizes = IMAGE_SIZES
                    for s in sizes:
                        try:
                            im_copy = im.copy()
                            im_copy.thumbnail((s, s))
                            if ENABLE_RESIZED_ORIGINALS:
                                try:
                                    out_path = f"{fp}.resized-{s}"
                                    im_copy.save(out_path)
                                    vkey = f"{msg.chat.id}/{msg.id}-w{s}{ext}"
                                    _upload_to_r2(out_path, vkey)
                                    try:
                                        os.remove(out_path)
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                            try:
                                if ENABLE_WEBP:
                                    webp_path = f"{fp}.resized-{s}.webp"
                                    im_copy.save(webp_path, format="WEBP", quality=75)
                                    vkey_webp = f"{msg.chat.id}/{msg.id}-w{s}.webp"
                                    _upload_to_r2(webp_path, vkey_webp)
                                    try:
                                        os.remove(webp_path)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            try:
                                if ENABLE_AVIF:
                                    avif_path = f"{fp}.resized-{s}.avif"
                                    im_copy.save(avif_path, format="AVIF")
                                    vkey_avif = f"{msg.chat.id}/{msg.id}-w{s}.avif"
                                    _upload_to_r2(avif_path, vkey_avif)
                                    try:
                                        os.remove(avif_path)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        except Exception:
                            pass
                    try:
                        if ENABLE_WEBP:
                            webp_path = f"{fp}.webp"
                            im.save(webp_path, format="WEBP", quality=75)
                            o_webp_key = f"{msg.chat.id}/{msg.id}.webp"
                            _upload_to_r2(webp_path, o_webp_key)
                            try:
                                os.remove(webp_path)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        if ENABLE_AVIF:
                            avif_path = f"{fp}.avif"
                            im.save(avif_path, format="AVIF")
                            o_avif_key = f"{msg.chat.id}/{msg.id}.avif"
                            _upload_to_r2(avif_path, o_avif_key)
                            try:
                                os.remove(avif_path)
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            os.remove(fp)
        except Exception:
            pass
    content = msg.caption or msg.text
    if content:
        try:
            content = re.sub(r"\s*@batarikh\s*$", "", content.strip(), flags=re.IGNORECASE)
        except Exception:
            pass
    created = msg.date.isoformat()
    STATS["processed"] += 1
    STATS["last_id"] = msg.id
    STATS["last_time"] = created
    if supabase:
        try:
            supabase.table("posts").upsert({
                "id": msg.id,
                "created_at": created,
                "content": content,
                "media_type": mt,
                "media_url": mu,
                "width": w,
                "height": h,
            }).execute()
            logging.info(f"Upserted post id={msg.id} type={mt}")
        except Exception as e:
            logging.error(f"Failed to upsert post id={msg.id}: {e}")
            STATS["last_error"] = str(e)

# Normalize channel identifier - add @ if not present and not a numeric ID
def normalize_channel(channel: str) -> str:
    """Normalize channel identifier for Pyrogram."""
    if not channel:
        return channel
    # If it's already a numeric ID, return as is
    if channel.lstrip('-').isdigit():
        return channel
    # If it doesn't start with @, add it
    if not channel.startswith('@'):
        return f'@{channel}'
    return channel

NORMALIZED_CHANNEL = normalize_channel(TARGET_CHANNEL) if TARGET_CHANNEL else None

# Use more flexible filter - accept both channel username and ID
if NORMALIZED_CHANNEL:
    if NORMALIZED_CHANNEL.lstrip('-@').isdigit():
        # It's a numeric ID
        chat_filter = filters.chat(int(NORMALIZED_CHANNEL.lstrip('-')))
    else:
        # It's a username
        chat_filter = filters.chat(NORMALIZED_CHANNEL)
    logging.info(f"Listening for messages from channel: {NORMALIZED_CHANNEL}")
else:
    chat_filter = filters.channel
    logging.warning("No TARGET_CHANNEL specified, listening to all channels")

# Debug handler to log all incoming messages (can be disabled in production)
@app.on_message(filters.all)
async def debug_all_messages(client, message):
    """Debug handler to see all incoming messages."""
    if hasattr(message, 'chat') and message.chat:
        chat_title = getattr(message.chat, 'title', 'Unknown')
        chat_username = getattr(message.chat, 'username', 'None')
        logging.debug(f"Received message from chat: {chat_title} (@{chat_username}, id: {message.chat.id})")

@app.on_message(chat_filter)
async def handle_message(client, message):
    try:
        chat_info = f"chat_id={message.chat.id}"
        if hasattr(message.chat, 'title'):
            chat_info += f" title='{message.chat.title}'"
        if hasattr(message.chat, 'username'):
            chat_info += f" username=@{message.chat.username}"
        logging.info(f"Received message id={message.id} from {chat_info}")
        await process_message(message)
        logging.info(f"Successfully processed message id={message.id}")
    except Exception as e:
        logging.error(f"Error processing message id={getattr(message, 'id', '?')}: {e}", exc_info=True)

async def backfill() -> None:
    """Backfill historical messages from the channel."""
    try:
        limit = int(os.getenv("BACKFILL_LIMIT", "0"))
    except (ValueError, TypeError) as e:
        logging.warning(f"Invalid BACKFILL_LIMIT, using 0: {e}")
        limit = 0
    if not TARGET_CHANNEL or limit <= 0:
        logging.info("Backfill skipped: no limit set or no target channel")
        return
    count = 0
    try:
        async for msg in app.get_chat_history(TARGET_CHANNEL, limit=limit):
            await process_message(msg)
            count += 1
            if count % 50 == 0:
                logging.info(f"Backfill progress: {count}/{limit} messages processed")
        logging.info(f"Backfill completed: {count} messages processed")
    except Exception as e:
        logging.error(f"Backfill failed: {e}")
        raise

async def main() -> None:
    """Main async entry point."""
    start_status_server()
    try:
        try:
            await app.start()
        except AuthKeyDuplicated as e:
            logging.error("=" * 80)
            logging.error("CRITICAL ERROR: AUTH_KEY_DUPLICATED")
            logging.error("=" * 80)
            logging.error("The same SESSION_STRING is being used in multiple places simultaneously.")
            logging.error("This can happen if:")
            logging.error("  1. The worker is running locally AND on Railway at the same time")
            logging.error("  2. Multiple Railway deployments are using the same session")
            logging.error("  3. Another application is using the same session string")
            logging.error("")
            logging.error("SOLUTION:")
            logging.error("  - Stop ALL other instances using this session (local, other deployments)")
            logging.error("  - OR generate a NEW session string specifically for Railway")
            logging.error("  - Update SESSION_STRING environment variable in Railway")
            logging.error("=" * 80)
            raise
        STATS["connected"] = True
        logging.info("Telegram client started")
        
        # Verify channel access
        if NORMALIZED_CHANNEL:
            try:
                chat = await app.get_chat(NORMALIZED_CHANNEL)
                logging.info(f"Successfully connected to channel: {chat.title} (id: {chat.id})")
                # Check if we're a member
                try:
                    member = await app.get_chat_member(NORMALIZED_CHANNEL, "me")
                    logging.info(f"Channel membership status: {member.status}")
                except Exception as e:
                    logging.warning(f"Could not verify channel membership: {e}")
            except Exception as e:
                logging.error(f"Failed to access channel {NORMALIZED_CHANNEL}: {e}")
                logging.error("Make sure the account is a member of the channel and has proper permissions")
        
        # Start heartbeat task
        async def heartbeat() -> None:
            try:
                interval = int(os.getenv("HEARTBEAT_SECS", "60"))
            except (ValueError, TypeError):
                interval = 60
            while STATS["connected"]:
                logging.info(f"Heartbeat connected={STATS['connected']} processed={STATS['processed']} last_id={STATS['last_id']}")
                await asyncio.sleep(interval)
        
        # Run backfill if enabled
        if os.getenv("BACKFILL_ON_START") == "1":
            try:
                await backfill()
            except Exception as e:
                logging.error(f"Backfill task failed: {e}")
        
        # Start heartbeat
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Keep running
        await idle()
        
        # Cancel heartbeat
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Worker error: {e}", exc_info=True)
        raise
    finally:
        STATS["connected"] = False
        try:
            await app.stop()
            logging.info("Telegram client stopped")
        except Exception as e:
            logging.error(f"Error stopping client: {e}")

if __name__ == "__main__":
    logging.info("Starting Telegram worker...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Worker stopped by user")
    except Exception as e:
        logging.error(f"Worker crashed: {e}", exc_info=True)
        raise
