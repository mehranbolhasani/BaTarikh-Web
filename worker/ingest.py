import os
from dotenv import load_dotenv
from pyrogram import Client, filters

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

app = Client("telegram_worker", api_id=API_ID, api_hash=API_HASH)

async def process_message(msg):
    return None

@app.on_message(filters.all)
async def handle_message(client, message):
    await process_message(message)

if __name__ == "__main__":
    app.run()

