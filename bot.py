import asyncio
import requests
import os
import time
import sys
from aiohttp.web import Application as WebApp, AppRunner, TCPSite, Response
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

# Render/Railway usually provide the PORT env var automatically
PORT = int(os.getenv("PORT", 8080)) 
GROUP_FILE = "groups.txt"
FOOTER = "\n\n( OLDY CRYPTO ₿ )"
# ==========================================

# Simple sanity check to prevent Status 1 immediately
if not TELEGRAM_TOKEN:
    print("❌ FATAL ERROR: TELEGRAM_TOKEN is missing from Environment Variables!")
    sys.exit(1)

message_counter = {}

# ---------- KEEP ALIVE SERVER ----------
async def checkHealth(request):
    return Response(text="Oldy Crypto Update Alive")

async def startServer():
    try:
        web_app = WebApp()
        web_app.router.add_get('/', checkHealth)
        web_app.router.add_get('/healthz', checkHealth)
        runner = AppRunner(web_app)
        await runner.setup()
        site = TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        print(f"✅ KeepAlive server running on port {PORT}")
    except Exception as e:
        print(f"❌ Web Server Failed: {e}")
        # We don't exit here, maybe the bot can still run

# ---------- CRYPTO FUNCTIONS ----------
def get_btc_price():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        params = {"symbol": "BTC"}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return round(data["data"]["BTC"]["quote"]["USD"]["price"], 2)
    except Exception as e:
        print(f"⚠️ Price API Error: {e}")
        return "Check Market"

def get_news():
    try:
        url = f"https://cryptonews-api.com/api/v1/category?section=general&items=1&token={NEWS_KEY}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()["data"][0]["title"]
    except Exception as e:
        print(f"⚠️ News API Error: {e}")
        return "New updates coming soon..."

# ---------- COMMANDS & HANDLERS ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("hey I am alive!! 😄\n\nMade by ( TEAM OLDY CRYPTO )")

async def updates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Bot is active and monitoring market...{FOOTER}")

async def capture_and_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat: return
    chat_id = update.effective_chat.id
    message_counter[chat_id] = message_counter.get(chat_id, 0) + 1
    if message_counter[chat_id] % 7 == 0:
        try: await update.message.reply_text("😄")
        except: pass

# ---------- UPDATE LOOP ----------
async def send_updates(bot):
    print("🔄 Update Loop Started (Hourly updates)")
    while True:
        try:
            # Logic to send updates to your groups can go here
            # For now, we just log to keep the task alive
            pass
        except Exception as e:
            print(f"Update Loop Error: {e}")
        await asyncio.sleep(3600)

# ---------- MAIN ----------
async def main():
    # 1. Start Server
    await startServer()

    # 2. Build Bot
    try:
        print("🤖 Initializing Telegram Bot...")
        # Use explicit PTB Application
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("updates", updates_cmd))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), capture_and_react))

        # 3. Run everything
        async with app:
            await app.initialize()
            await app.start()
            print("🚀 Bot Authenticated and Polling...")
            
            # Start background update task
            asyncio.create_task(send_updates(app.bot))
            
            await app.updater.start_polling()
            await asyncio.Event().wait()
            
    except Exception as e:
        print(f"❌ CRITICAL BOT ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
