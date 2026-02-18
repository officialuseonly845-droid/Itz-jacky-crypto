import asyncio
import os
import sys
import requests
import time
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CMC_KEY = os.getenv("CMC_KEY")
NEWS_KEY = os.getenv("NEWS_KEY")
PORT = int(os.getenv("PORT", 10000)) 
GROUP_FILE = "groups.txt"
FOOTER = "\n\n( OLDY CRYPTO ₿ )"
# ==========================================

# --- Web Server for Health Checks ---
async def handle_health(request):
    return web.Response(text="Bot Status: Online", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Health-check server online on port {PORT}")

# --- Helper Functions ---
def get_crypto_update():
    try:
        p_res = requests.get(
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
            headers={"X-CMC_PRO_API_KEY": CMC_KEY},
            params={"symbol": "BTC"},
            timeout=10
        )
        price = round(p_res.json()["data"]["BTC"]["quote"]["USD"]["price"], 2)
        
        n_res = requests.get(
            f"https://cryptonews-api.com/api/v1/category?section=general&items=1&token={NEWS_KEY}",
            timeout=10
        )
        news = n_res.json()["data"][0]["title"]
        
        return f"📊 Oldy Crypto Update\n\n💰 BTC Price: ${price}\n📰 News: {news}{FOOTER}"
    except Exception as e:
        print(f"⚠️ API Data Error: {e}")
        return None

def save_chat(chat_id):
    if not os.path.exists(GROUP_FILE):
        open(GROUP_FILE, "w").close()
    with open(GROUP_FILE, "r") as f:
        chats = f.read().splitlines()
    if str(chat_id) not in chats:
        with open(GROUP_FILE, "a") as f:
            f.write(str(chat_id) + "\n")

# --- Command & Message Handlers ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat(update.effective_chat.id)
    await update.message.reply_text("hey I am alive!! 😄\n\nMade by ( TEAM OLDY CRYPTO )")

async def updates_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Instant manual update
    start_time = time.time()
    msg = await update.message.reply_text("Checking latest crypto market data...")
    
    content = get_crypto_update()
    ping = round((time.time() - start_time) * 1000)
    
    if content:
        await msg.edit_text(f"{content}\n⚡ Ping: {ping}ms")
    else:
        await msg.edit_text("❌ Error fetching data. Please try again later.")

async def reaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        save_chat(update.effective_chat.id)
        count = context.chat_data.get('msg_count', 0) + 1
        context.chat_data['msg_count'] = count
        if count % 7 == 0:
            await update.message.reply_text("😄")

# --- Automated Task (JobQueue) ---
async def send_hourly_update(context: ContextTypes.DEFAULT_TYPE):
    content = get_crypto_update()
    if not content or not os.path.exists(GROUP_FILE):
        return
    
    with open(GROUP_FILE, "r") as f:
        for chat_id in f.read().splitlines():
            try:
                await context.bot.send_message(chat_id=chat_id, text=content)
            except Exception as e:
                print(f"Could not send to {chat_id}: {e}")

# --- Main Runtime ---
async def main():
    if not TELEGRAM_TOKEN:
        print("❌ CRITICAL: TELEGRAM_TOKEN environment variable is missing!")
        sys.exit(1)

    await start_web_server()

    print("🤖 Booting Bot (Compatible with Python 3.14)...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("updates", updates_handler)) # Added back!
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reaction_handler))

    # Job Queue for Auto-Updates
    app.job_queue.run_repeating(send_hourly_update, interval=3600, first=10)

    async with app:
        await app.initialize()
        await app.start()
        print("🚀 Bot is polling for updates...")
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
