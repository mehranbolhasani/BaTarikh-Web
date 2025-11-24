import os
import time
import logging
import asyncio
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from dotenv import load_dotenv
import re
try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait
import boto3
from botocore.config import Config
from boto3.s3.transfer import S3Transfer, TransferConfig
import mimetypes
from supabase import create_client

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

missing = []
for k in ["API_ID", "API_HASH", "SESSION_STRING", "R2_ENDPOINT", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_PUBLIC_BASE_URL"]:
    if not os.getenv(k):
        missing.append(k)
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

app = Client(
    "telegram_worker",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
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

supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
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

def start_status_server():
    try:
        port = int(os.getenv("PORT", "8000"))
    except Exception:
        port = 8000
    server = HTTPServer(("0.0.0.0", port), StatusHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    logging.info(f"Status server listening on :{port}")

async def _download(msg):
    while True:
        try:
            return await msg.download()
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)

async def _media_info(msg):
    if msg.photo:
        p = await _download(msg)
        return p, getattr(msg.photo, "width", None), getattr(msg.photo, "height", None), "image"
    if msg.video:
        p = await _download(msg)
        return p, getattr(msg.video, "width", None), getattr(msg.video, "height", None), "video"
    if msg.audio:
        p = await _download(msg)
        return p, None, None, "audio"
    if getattr(msg, 'document', None):
        # Detect PDFs specifically; otherwise mark as document
        mime = getattr(msg.document, 'mime_type', None)
        if (mime and mime.lower() == 'application/pdf') or (getattr(msg.document, 'file_name', '') or '').lower().endswith('.pdf'):
            p = await _download(msg)
            return p, None, None, "document"
        # Optional: handle other documents similarly
        # p = await _download(msg)
        # return p, None, None, "document"
    return None, None, None, "none"

def _upload_to_r2(file_path, object_key):
    ct = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    attempts = 0
    while True:
        try:
            _transfer.upload_file(file_path, R2_BUCKET, object_key, extra_args={"ContentType": ct})
            return f"{R2_PUBLIC_BASE_URL}/{object_key}"
        except Exception as e:
            attempts += 1
            STATS["last_error"] = str(e)
            if attempts >= 5:
                raise e
            time.sleep(min(2 ** attempts, 10))

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
                    sizes = [640, 1024]
                    for s in sizes:
                        try:
                            im_copy = im.copy()
                            im_copy.thumbnail((s, s))
                            out_path = f"{fp}.resized-{s}"
                            im_copy.save(out_path)
                            vkey = f"{msg.chat.id}/{msg.id}-w{s}{ext}"
                            _upload_to_r2(out_path, vkey)
                            try:
                                os.remove(out_path)
                            except Exception:
                                pass
                            try:
                                webp_path = f"{fp}.resized-{s}.webp"
                                im_copy.save(webp_path, format="WEBP", quality=80)
                                vkey_webp = f"{msg.chat.id}/{msg.id}-w{s}.webp"
                                _upload_to_r2(webp_path, vkey_webp)
                                try:
                                    os.remove(webp_path)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                            try:
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
                        webp_path = f"{fp}.webp"
                        im.save(webp_path, format="WEBP", quality=80)
                        o_webp_key = f"{msg.chat.id}/{msg.id}.webp"
                        _upload_to_r2(webp_path, o_webp_key)
                        try:
                            os.remove(webp_path)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    try:
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

chat_filter = filters.chat(TARGET_CHANNEL) if TARGET_CHANNEL else filters.channel
@app.on_message(chat_filter)
async def handle_message(client, message):
    try:
        await process_message(message)
    except Exception as e:
        logging.error(f"Error processing message id={getattr(message, 'id', '?')}: {e}")

async def backfill():
    try:
        limit = int(os.getenv("BACKFILL_LIMIT", "0"))
    except Exception:
        limit = 0
    if not TARGET_CHANNEL or limit <= 0:
        return
    count = 0
    async for msg in app.get_chat_history(TARGET_CHANNEL, limit=limit):
        await process_message(msg)
        count += 1
        if count % 50 == 0:
            logging.info(f"Backfill progress: {count}/{limit} messages processed")

def main_sync():
    start_status_server()
    app.start()
    STATS["connected"] = True
    try:
        if os.getenv("BACKFILL_ON_START") == "1":
            async def backfill_wrapper():
                try:
                    await backfill()
                except Exception as e:
                    logging.error(f"Backfill task failed: {e}")
            # Schedule backfill on the same loop to avoid cross-loop errors
            app.loop.create_task(backfill_wrapper())
        async def heartbeat():
            interval = int(os.getenv("HEARTBEAT_SECS", "60"))
            while True:
                logging.info(f"Heartbeat connected={STATS['connected']} processed={STATS['processed']} last_id={STATS['last_id']}")
                await asyncio.sleep(interval)
        app.loop.create_task(heartbeat())
        idle()
    finally:
        app.stop()
        STATS["connected"] = False

async def main():
    start_status_server()
    await app.start()
    STATS["connected"] = True
    try:
        if os.getenv("BACKFILL_ON_START") == "1":
            await backfill()
        await idle()
    finally:
        await app.stop()
        STATS["connected"] = False

if __name__ == "__main__":
    logging.info("Starting Telegram worker...")
    try:
        main_sync()
    except Exception as e:
        logging.error(f"Worker crashed: {e}")
