import asyncio
import requests
import os
import time
from aiohttp.web import Application, AppRunner, TCPSite, Response
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

PORT = 8080
GROUP_FILE = "groups.txt"
FOOTER = "\n\n( OLDY CRYPTO ₿ )"
# ==========================================

# message counter per group
message_counter = {}

# ---------- KEEP ALIVE SERVER ----------
async def checkHealth(request):
    return Response(text="Oldy Crypto Update Alive")

async def startServer():
    app = Application()
    app.router.add_get('/', checkHealth)
    app.router.add_get('/healthz', checkHealth)

    runner = AppRunner(app)
    await runner.setup()

    site = TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

    print(f"KeepAlive server running on port {PORT}")

# ---------- GROUP SAVE SYSTEM ----------
def save_group(chat_id):
    if not os.path.exists(GROUP_FILE):
        open(GROUP_FILE, "w").close()

    with open(GROUP_FILE, "r+") as f:
        groups = f.read().splitlines()
        if str(chat_id) not in groups:
            f.write(str(chat_id) + "\n")

def load_groups():
    if not os.path.exists(GROUP_FILE):
        return []
    with open(GROUP_FILE, "r") as f:
        return f.read().splitlines()

# ---------- CRYPTO FUNCTIONS ----------
def get_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_KEY}
    params = {"symbol": "BTC"}
    r = requests.get(url, headers=headers, params=params, timeout=10)
    data = r.json()
    return round(data["data"]["BTC"]["quote"]["USD"]["price"], 2)

def get_news():
    url = f"https://cryptonews-api.com/api/v1/category?section=general&items=1&token={NEWS_KEY}"
    r = requests.get(url, timeout=10)
    return r.json()["data"][0]["title"]

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

    # Count messages
    message_counter[chat_id] = message_counter.get(chat_id, 0) + 1

    # React every 7th message
    if message_counter[chat_id] % 7 == 0:
        try:
            await update.message.reply_text("😄")
        except:
            pass

# ---------- GLOBAL ERROR HANDLER ----------
async def error_handler(update, context):
    print("----- GLOBAL ERROR -----")
    print("Update:", update)
    print("Error:", context.error)

# ---------- UPDATE SCHEDULER ----------
async def send_updates(app):
    bot = app.bot

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
                    print("Send Error:", e)

        except Exception as e:
            print("Update Loop Error:", e)

        await asyncio.sleep(3600)  # every 1 hour

# ---------- MAIN ----------
async def main():
    await startServer()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("updates", updates_cmd))
    app.add_handler(MessageHandler(filters.ALL, capture_and_react))

    app.add_error_handler(error_handler)

    asyncio.create_task(send_updates(app))

    print("Oldy Crypto Update Bot Running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
