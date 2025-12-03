import os
import sys
import subprocess

# Install dependencies if missing (Railway workaround)
def ensure_dependencies():
    """Ensure required dependencies are installed."""
    try:
        import dotenv
        return  # Dependencies already installed
    except ImportError:
        pass
    
    print("Dependencies not found. Installing from requirements.txt...", file=sys.stderr, flush=True)
    
    # Try to find requirements.txt in current directory or parent
    req_paths = ["requirements.txt", "../requirements.txt", "/app/requirements.txt"]
    req_file = None
    for path in req_paths:
        if os.path.exists(path):
            req_file = path
            break
    
    if not req_file:
        print("ERROR: Could not find requirements.txt", file=sys.stderr, flush=True)
        print(f"Current directory: {os.getcwd()}", file=sys.stderr, flush=True)
        print(f"Files in current dir: {os.listdir('.')}", file=sys.stderr, flush=True)
        sys.exit(1)
    
    try:
        print(f"Installing from: {req_file}", file=sys.stderr, flush=True)
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", 
            "--upgrade", "pip"
        ], stdout=sys.stderr, stderr=sys.stderr)
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", 
            "-r", req_file
        ], stdout=sys.stderr, stderr=sys.stderr)
        print("Dependencies installed successfully!", file=sys.stderr, flush=True)
        
        # Verify installation
        try:
            import dotenv
            print("✓ Verified: dotenv is now available", file=sys.stderr, flush=True)
        except ImportError:
            print("ERROR: dotenv still not available after installation", file=sys.stderr, flush=True)
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

ensure_dependencies()

import time
import logging
import asyncio
import json
import signal
import sys
import gc
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Optional, Tuple, Dict, Any, Deque
from collections import deque
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import re
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, AuthKeyDuplicated, ConnectionError as PyrogramConnectionError
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
    "failed": 0,
    "retried": 0,
    "last_id": None,
    "last_time": None,
    "last_error": None,
    "connected": False,
    "reconnect_count": 0,
    "queue_size": 0,
}

# Message queue for retry mechanism
@dataclass
class QueuedMessage:
    message_id: int
    chat_id: int
    timestamp: float
    retry_count: int
    last_error: Optional[str]
    message_data: Dict[str, Any]

# In-memory queue (persisted to Supabase on failure)
_message_queue: Deque[QueuedMessage] = deque(maxlen=1000)
_shutdown_event = threading.Event()
_max_retries = int(os.getenv("MAX_MESSAGE_RETRIES", "5"))
_retry_delay_base = int(os.getenv("RETRY_DELAY_BASE_SECS", "60"))

# Circuit breaker state
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logging.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def can_proceed(self):
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                logging.info("Circuit breaker entering half-open state")
                return True
            return False
        return True  # half_open

_r2_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
_supabase_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/status"):
            stats_copy = STATS.copy()
            stats_copy["queue_size"] = len(_message_queue)
            stats_copy["r2_circuit_breaker"] = _r2_circuit_breaker.state
            stats_copy["supabase_circuit_breaker"] = _supabase_circuit_breaker.state
            body = json.dumps({
                "ok": True,
                "stats": stats_copy,
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
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass

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
    """Upload file to R2 storage with retry logic and circuit breaker."""
    if not _r2_circuit_breaker.can_proceed():
        logging.warning("R2 circuit breaker is open, skipping upload")
        return None
    
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
                _r2_circuit_breaker.record_success()
                return f"{R2_PUBLIC_BASE_URL}/{object_key}"
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise
            # Upload file
            _transfer.upload_file(file_path, R2_BUCKET, object_key, extra_args={"ContentType": ct})
            logging.debug(f"Uploaded to R2: {object_key}")
            _r2_circuit_breaker.record_success()
            return f"{R2_PUBLIC_BASE_URL}/{object_key}"
        except ClientError as e:
            attempts += 1
            STATS["last_error"] = str(e)
            if attempts >= max_attempts:
                logging.error(f"Failed to upload after {max_attempts} attempts: {e}")
                _r2_circuit_breaker.record_failure()
                raise
            wait_time = min(2 ** attempts, 10)
            logging.warning(f"Upload failed, retrying in {wait_time}s (attempt {attempts}/{max_attempts}): {e}")
            time.sleep(wait_time)
        except Exception as e:
            logging.error(f"Unexpected error during upload: {e}")
            STATS["last_error"] = str(e)
            _r2_circuit_breaker.record_failure()
            raise
    return None

async def process_message(msg, retry_count=0):
    """Process a message with error handling and retry logic."""
    try:
        fp, w, h, mt = await _media_info(msg)
        mu = None
        if fp:
            ext = os.path.splitext(fp)[1] if isinstance(fp, str) else ""
            key = f"{msg.chat.id}/{msg.id}{ext}"
            mu = _upload_to_r2(fp, key)
            if mt == "image" and HAS_PIL and isinstance(fp, str):
                try:
                    # Check file size before processing (limit to 50MB)
                    file_size = os.path.getsize(fp) if os.path.exists(fp) else 0
                    max_image_size = int(os.getenv("MAX_IMAGE_SIZE_BYTES", "52428800"))  # 50MB default
                    if file_size > max_image_size:
                        logging.warning(f"Image too large ({file_size} bytes), skipping processing")
                    else:
                        with Image.open(fp) as im:
                            # Limit image dimensions to prevent memory issues
                            max_dimension = int(os.getenv("MAX_IMAGE_DIMENSION", "8192"))  # 8K default
                            if im.width > max_dimension or im.height > max_dimension:
                                logging.warning(f"Image dimensions too large ({im.width}x{im.height}), resizing...")
                                ratio = min(max_dimension / im.width, max_dimension / im.height)
                                new_size = (int(im.width * ratio), int(im.height * ratio))
                                im = im.resize(new_size, Image.Resampling.LANCZOS)
                            
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
        
        # Upsert to Supabase with circuit breaker
        if supabase and _supabase_circuit_breaker.can_proceed():
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
                _supabase_circuit_breaker.record_success()
            except Exception as e:
                logging.error(f"Failed to upsert post id={msg.id}: {e}")
                STATS["last_error"] = str(e)
                _supabase_circuit_breaker.record_failure()
                # Queue message for retry if critical
                if retry_count < _max_retries:
                    _queue_message_for_retry(msg, str(e), retry_count)
        elif supabase:
            logging.warning("Supabase circuit breaker is open, skipping upsert")
            if retry_count < _max_retries:
                _queue_message_for_retry(msg, "Supabase circuit breaker open", retry_count)
        
        # Force garbage collection after processing to free memory
        if STATS["processed"] % 10 == 0:
            gc.collect()
    except Exception as e:
        logging.error(f"Error processing message id={getattr(msg, 'id', '?')}: {e}", exc_info=True)
        STATS["failed"] += 1
        STATS["last_error"] = str(e)
        if retry_count < _max_retries:
            _queue_message_for_retry(msg, str(e), retry_count)
        else:
            logging.error(f"Message id={getattr(msg, 'id', '?')} exceeded max retries, giving up")

def _queue_message_for_retry(msg: Message, error: str, current_retry: int):
    """Queue a message for retry processing."""
    try:
        queued = QueuedMessage(
            message_id=msg.id,
            chat_id=msg.chat.id,
            timestamp=time.time(),
            retry_count=current_retry + 1,
            last_error=error,
            message_data={
                "id": msg.id,
                "chat_id": msg.chat.id,
                "date": msg.date.isoformat() if hasattr(msg, 'date') else None,
                "caption": msg.caption,
                "text": msg.text,
            }
        )
        _message_queue.append(queued)
        STATS["retried"] += 1
        logging.info(f"Queued message id={msg.id} for retry (attempt {queued.retry_count}/{_max_retries})")
    except Exception as e:
        logging.error(f"Failed to queue message for retry: {e}")

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
        await process_message(message, retry_count=0)
        logging.info(f"Successfully processed message id={message.id}")
    except Exception as e:
        logging.error(f"Error processing message id={getattr(message, 'id', '?')}: {e}", exc_info=True)
        STATS["failed"] += 1

async def process_retry_queue():
    """Process messages in the retry queue."""
    while not _shutdown_event.is_set():
        try:
            if not _message_queue:
                await asyncio.sleep(30)  # Check every 30 seconds
                continue
            
            # Process oldest message
            queued = _message_queue.popleft()
            
            # Check if enough time has passed since last retry
            delay = _retry_delay_base * (2 ** queued.retry_count)
            if time.time() - queued.timestamp < delay:
                # Put it back at the end
                _message_queue.append(queued)
                await asyncio.sleep(10)
                continue
            
            logging.info(f"Retrying message id={queued.message_id} (attempt {queued.retry_count}/{_max_retries})")
            
            try:
                # Fetch message from Telegram
                msg = await app.get_messages(queued.chat_id, queued.message_id)
                if msg:
                    await process_message(msg, retry_count=queued.retry_count)
                else:
                    logging.warning(f"Could not fetch message id={queued.message_id} for retry")
            except Exception as e:
                logging.error(f"Retry failed for message id={queued.message_id}: {e}")
                if queued.retry_count < _max_retries:
                    queued.timestamp = time.time()
                    queued.last_error = str(e)
                    queued.retry_count += 1
                    _message_queue.append(queued)
                else:
                    logging.error(f"Message id={queued.message_id} exceeded max retries, giving up")
            
            await asyncio.sleep(1)  # Small delay between retries
        except Exception as e:
            logging.error(f"Error in retry queue processor: {e}", exc_info=True)
            await asyncio.sleep(10)

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

async def reconnect_client(max_retries=10, base_delay=5):
    """Reconnect Telegram client with exponential backoff."""
    retry_count = 0
    while retry_count < max_retries and not _shutdown_event.is_set():
        try:
            if app.is_connected:
                await app.stop()
            await app.start()
            STATS["connected"] = True
            STATS["reconnect_count"] += 1
            logging.info("Successfully reconnected to Telegram")
            return True
        except AuthKeyDuplicated as e:
            logging.error("=" * 80)
            logging.error("CRITICAL ERROR: AUTH_KEY_DUPLICATED")
            logging.error("=" * 80)
            logging.error("The same SESSION_STRING is being used in multiple places simultaneously.")
            logging.error("SOLUTION:")
            logging.error("  - Stop ALL other instances using this session")
            logging.error("  - OR generate a NEW session string specifically for Railway")
            logging.error("=" * 80)
            raise
        except Exception as e:
            retry_count += 1
            delay = min(base_delay * (2 ** retry_count), 300)  # Max 5 minutes
            logging.error(f"Reconnection attempt {retry_count}/{max_retries} failed: {e}")
            logging.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    return False

async def connection_monitor():
    """Monitor connection and automatically reconnect if needed."""
    while not _shutdown_event.is_set():
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            if not app.is_connected:
                logging.warning("Connection lost, attempting to reconnect...")
                STATS["connected"] = False
                await reconnect_client()
        except Exception as e:
            logging.error(f"Error in connection monitor: {e}", exc_info=True)
            await asyncio.sleep(60)

async def main() -> None:
    """Main async entry point with automatic reconnection."""
    start_status_server()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        _shutdown_event.set()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initial connection with retry
        if not await reconnect_client():
            logging.error("Failed to establish initial connection")
            return
        
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
        
        # Start background tasks
        async def heartbeat() -> None:
            try:
                interval = int(os.getenv("HEARTBEAT_SECS", "60"))
            except (ValueError, TypeError):
                interval = 60
            while STATS["connected"] and not _shutdown_event.is_set():
                logging.info(f"Heartbeat connected={STATS['connected']} processed={STATS['processed']} failed={STATS['failed']} queue={len(_message_queue)} last_id={STATS['last_id']}")
                await asyncio.sleep(interval)
        
        # Run backfill if enabled
        if os.getenv("BACKFILL_ON_START") == "1":
            try:
                await backfill()
            except Exception as e:
                logging.error(f"Backfill task failed: {e}")
        
        # Start background tasks
        heartbeat_task = asyncio.create_task(heartbeat())
        connection_monitor_task = asyncio.create_task(connection_monitor())
        retry_queue_task = asyncio.create_task(process_retry_queue())
        
        # Keep running until shutdown
        try:
            while not _shutdown_event.is_set():
                if not app.is_connected:
                    logging.warning("Client disconnected, waiting for reconnection...")
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            logging.info("Received interrupt signal")
            _shutdown_event.set()
        
        # Cancel background tasks
        heartbeat_task.cancel()
        connection_monitor_task.cancel()
        retry_queue_task.cancel()
        
        # Wait for tasks to finish
        for task in [heartbeat_task, connection_monitor_task, retry_queue_task]:
            try:
                await task
            except asyncio.CancelledError:
                pass
        
    except Exception as e:
        logging.error(f"Worker error: {e}", exc_info=True)
        if not _shutdown_event.is_set():
            # Try to reconnect instead of crashing
            logging.info("Attempting to recover from error...")
            await asyncio.sleep(10)
            await reconnect_client()
    finally:
        STATS["connected"] = False
        _shutdown_event.set()
        try:
            if app.is_connected:
                await app.stop()
                logging.info("Telegram client stopped")
        except Exception as e:
            logging.error(f"Error stopping client: {e}")

if __name__ == "__main__":
    logging.info("Starting Telegram worker...")
    max_restarts = int(os.getenv("MAX_RESTARTS", "10"))
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            asyncio.run(main())
            # If main() returns normally, break the loop
            break
        except KeyboardInterrupt:
            logging.info("Worker stopped by user")
            break
        except AuthKeyDuplicated:
            # Don't retry on auth errors
            logging.error("Auth key duplicated, exiting")
            sys.exit(1)
        except Exception as e:
            restart_count += 1
            logging.error(f"Worker crashed (restart {restart_count}/{max_restarts}): {e}", exc_info=True)
            if restart_count < max_restarts:
                wait_time = min(30 * restart_count, 300)  # Max 5 minutes
                logging.info(f"Restarting in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Max restarts reached, exiting")
                sys.exit(1)
