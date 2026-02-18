import asyncio
import os
import sys
import time
import requests
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
PORT = int(os.getenv("PORT", 8080)) # Render provides this variable
FOOTER = "\n\n( OLDY CRYPTO ₿ )"
GROUP_FILE = "groups.txt"
# ==========================================

# --- Web Server for Keep Alive ---
async def handle_health(request):
    return web.Response(text="Bot is Healthy", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/healthz", handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    # Binding to 0.0.0.0 is critical for Render/Railway
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web server listening on port {PORT}")

# --- Bot Logic ---
def get_btc_price():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        r = requests.get(url, headers={"X-CMC_PRO_API_KEY": CMC_KEY}, params={"symbol": "BTC"}, timeout=5)
        return round(r.json()["data"]["BTC"]["quote"]["USD"]["price"], 2)
    except: return "Market Data Error"

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is Online! 😄")

async def send_updates(bot):
    while True:
        # Update logic here
        await asyncio.sleep(3600)

async def main():
    if not TELEGRAM_TOKEN:
        print("❌ Missing TELEGRAM_TOKEN")
        sys.exit(1)

    # 1. Start Web Server FIRST to satisfy Port Scan
    await start_web_server()

    # 2. Setup Bot
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    
    # 3. Run Bot
    async with app:
        await app.initialize()
        await app.start()
        print("🚀 Bot started successfully")
        
        asyncio.create_task(send_updates(app.bot))
        
        await app.updater.start_polling()
        # Keep the event loop running
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
