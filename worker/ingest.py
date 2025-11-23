import os
import time
import logging
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
import boto3
import mimetypes
from supabase import create_client

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
)

supabase = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    logging.warning("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set; will skip DB upserts")

def _media_info(msg):
    if msg.photo:
        p = msg.download()
        return p, msg.photo.width, msg.photo.height, "image"
    if msg.video:
        p = msg.download()
        return p, msg.video.width, msg.video.height, "video"
    if msg.audio:
        p = msg.download()
        return p, None, None, "audio"
    return None, None, None, "none"

def _upload_to_r2(file_path, object_key):
    ct = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    r2.upload_file(file_path, R2_BUCKET, object_key, ExtraArgs={"ContentType": ct})
    return f"{R2_PUBLIC_BASE_URL}/{object_key}"

async def process_message(msg):
    fp, w, h, mt = _media_info(msg)
    mu = None
    if fp:
        ext = os.path.splitext(fp)[1]
        key = f"{msg.chat.id}/{msg.id}{ext}"
        mu = _upload_to_r2(fp, key)
        try:
            os.remove(fp)
        except Exception:
            pass
    content = msg.caption or msg.text
    created = msg.date.isoformat()
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
    async for msg in app.iter_history(TARGET_CHANNEL, limit=limit):
        await process_message(msg)

async def runner():
    await app.start()
    if os.getenv("BACKFILL_ON_START") == "1":
        await backfill()
    await app.idle()
    await app.stop()

if __name__ == "__main__":
    while True:
        try:
            logging.info("Starting Telegram worker...")
            asyncio.run(runner())
        except Exception as e:
            logging.error(f"Worker crashed: {e}")
            time.sleep(5)
            logging.info("Restarting worker...")
