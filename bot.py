import asyncio
import requests
import os
import time
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

PORT = int(os.getenv("PORT", 8080)) # Ensure PORT is an integer
GROUP_FILE = "groups.txt"
FOOTER = "\n\n( OLDY CRYPTO ₿ )"
# ==========================================

if not TELEGRAM_TOKEN:
    print("ERROR: TELEGRAM_TOKEN is not set in environment variables.")
    exit(1)

# message counter per group
message_counter = {}

# ---------- KEEP ALIVE SERVER ----------
async def checkHealth(request):
    return Response(text="Oldy Crypto Update Alive")

async def startServer():
    # Using WebApp alias to avoid conflict with Telegram's Application
    web_app = WebApp()
    web_app.router.add_get('/', checkHealth)
    web_app.router.add_get('/healthz', checkHealth)

    runner = AppRunner(web_app)
    await runner.setup()

    site = TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"KeepAlive server running on port {PORT}")

# ---------- GROUP SAVE SYSTEM ----------
def save_group(chat_id):
    if not os.path.exists(GROUP_FILE):
        with open(GROUP_FILE, "w") as f: pass

    with open(GROUP_FILE, "r") as f:
        groups = f.read().splitlines()
    
    if str(chat_id) not in groups:
        with open(GROUP_FILE, "a") as f:
            f.write(str(chat_id) + "\n")

def load_groups():
    if not os.path.exists(GROUP_FILE):
        return []
    with open(GROUP_FILE, "r") as f:
        return f.read().splitlines()

# ---------- CRYPTO FUNCTIONS ----------
def get_btc_price():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
        params = {"symbol": "BTC"}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        data = r.json()
        return round(data["data"]["BTC"]["quote"]["USD"]["price"], 2)
    except Exception as e:
        print(f"Price Fetch Error: {e}")
        return "N/A"

def get_news():
    try:
        url = f"https://cryptonews-api.com/api/v1/category?section=general&items=1&token={NEWS_KEY}"
        r = requests.get(url, timeout=10)
        return r.json()["data"][0]["title"]
    except Exception as e:
        print(f"News Fetch Error: {e}")
        return "No recent news available"

# ---------- COMMANDS ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "hey I am alive!! 😄\n\nMade by ( TEAM OLDY CRYPTO )"
    )

async def updates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.message.reply_text("Checking ping...")
    ping = round((time.time() - start) * 1000)

    text = (
        f"hello I will send updates when I get some!!\n"
        f"Ping: {ping} ms"
        f"{FOOTER}"
    )
    await msg.edit_text(text)

# ---------- GROUP MESSAGE HANDLER ----------
async def capture_and_react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return

    chat_id = chat.id
    save_group(chat_id)

    message_counter[chat_id] = message_counter.get(chat_id, 0) + 1

    if message_counter[chat_id] % 7 == 0:
        try:
            await update.message.reply_text("😄")
        except:
            pass

# ---------- GLOBAL ERROR HANDLER ----------
async def error_handler(update, context):
    print(f"----- GLOBAL ERROR -----\nUpdate: {update}\nError: {context.error}")

# ---------- UPDATE SCHEDULER ----------
async def send_updates(bot):
    while True:
        try:
            price = get_btc_price()
            news = get_news()

            message = (
                f"📊 Oldy Crypto Update\n\n"
                f"💰 BTC Price: ${price}\n"
                f"📰 News: {news}"
                f"{FOOTER}"
            )

            groups = load_groups()
            for gid in groups:
                try:
                    await bot.send_message(chat_id=gid, text=message)
                except Exception as e:
                    print(f"Send Error to {gid}: {e}")

        except Exception as e:
            print(f"Update Loop Error: {e}")

        await asyncio.sleep(3600)  # 1 hour

# ---------- MAIN ----------
async def main():
    # Start the Web Server
    await startServer()

    # Build the Telegram Application
    # We use the full path to avoid any ambiguity
    ptb_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    ptb_app.add_handler(CommandHandler("start", start_cmd))
    ptb_app.add_handler(CommandHandler("updates", updates_cmd))
    ptb_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), capture_and_react))

    ptb_app.add_error_handler(error_handler)

    # Initialize and start the bot manually to keep the loop under control
    async with ptb_app:
        await ptb_app.initialize()
        await ptb_app.start()
        
        # Start background tasks
        asyncio.create_task(send_updates(ptb_app.bot))
        
        print("Oldy Crypto Update Bot Running...")
        await ptb_app.updater.start_polling()
        
        # Keep running until interrupted
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot application stopped.")
