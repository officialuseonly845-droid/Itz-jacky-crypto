import asyncio
import os
import sys
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
PORT = int(os.getenv("PORT", 10000)) 
GROUP_FILE = "groups.txt"
FOOTER = "\n\n( OLDY CRYPTO ₿ )"
# ==========================================

# --- Web Server (Health Check) ---
async def handle_health(request):
    return web.Response(text="Bot is running smoothly!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web server online on port {PORT}")

# --- Helper Functions ---
def get_crypto_data():
    try:
        # Get BTC Price
        p_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        p_res = requests.get(p_url, headers={"X-CMC_PRO_API_KEY": CMC_KEY}, params={"symbol": "BTC"}, timeout=5)
        price = round(p_res.json()["data"]["BTC"]["quote"]["USD"]["price"], 2)
        
        # Get News
        n_url = f"https://cryptonews-api.com/api/v1/category?section=general&items=1&token={NEWS_KEY}"
        n_res = requests.get(n_url, timeout=5)
        news = n_res.json()["data"][0]["title"]
        
        return f"📊 Oldy Crypto Update\n\n💰 BTC Price: ${price}\n📰 News: {news}{FOOTER}"
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return None

def save_group(chat_id):
    if not os.path.exists(GROUP_FILE):
        open(GROUP_FILE, "w").close()
    with open(GROUP_FILE, "r") as f:
        groups = f.read().splitlines()
    if str(chat_id) not in groups:
        with open(GROUP_FILE, "a") as f:
            f.write(str(chat_id) + "\n")

# --- Bot Command Handlers ---
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_group(update.effective_chat.id)
    await update.message.reply_text("hey I am alive!! 😄\n\nMade by ( TEAM OLDY CRYPTO )")

async def capture_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ["group", "supergroup"]:
        save_group(update.effective_chat.id)
        # React every 7th message
        count = context.chat_data.get('msg_count', 0) + 1
        context.chat_data['msg_count'] = count
        if count % 7 == 0:
            await update.message.reply_text("😄")

# --- Scheduled Update Job ---
async def hourly_update_job(context: ContextTypes.DEFAULT_TYPE):
    message = get_crypto_data()
    if not message: return
    
    if os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "r") as f:
            for chat_id in f.read().splitlines():
                try:
                    await context.bot.send_message(chat_id=chat_id, text=message)
                except Exception as e:
                    print(f"Failed to send to {chat_id}: {e}")

# --- Main Entry Point ---
async def main():
    if not TELEGRAM_TOKEN:
        print("❌ FATAL: No TELEGRAM_TOKEN found")
        sys.exit(1)

    # 1. Start web server immediately for Render
    await start_web_server()

    # 2. Build Bot with JobQueue
    print("🤖 Initializing Bot (v22.6)...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 3. Add Handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), capture_msg))

    # 4. Schedule the Hourly Job
    app.job_queue.run_repeating(hourly_update_job, interval=3600, first=10)

    # 5. Run everything
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        print("🚀 System fully operational.")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
