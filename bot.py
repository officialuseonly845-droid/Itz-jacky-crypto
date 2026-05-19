import asyncio
import os
import logging
import re
import base64
import traceback
from github import Github
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from sympy import sympify, diff, integrate, symbols

# --- ROOT LOGGING AND BULWARK CONFIG ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("FortressEngine")

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = "groups.txt"

# Initialization Guard
if not TOKEN:
    logger.critical("BOT_TOKEN environment variable is totally missing!")
    raise RuntimeError("Missing BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Safe GitHub Initialization
g = None
if GITHUB_TOKEN:
    try:
        g = Github(GITHUB_TOKEN)
    except Exception as e:
        logger.error(f"Failed to initialize GitHub instance: {e}")

# --- UI INTERFACES ---
def get_sos_ui(status, siren, progress):
    return (
        f"🚨 **POLICE EMERGENCY PROTOCOL** 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"**STATUS** : `{status}`\n"
        f"**SIREN** : {siren}\n"
        f"**SIGNAL** : `{progress}`\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

def get_update_ui(status, bar, percent):
    return (
        f"🛰  **SYSTEM SYNCHRONIZATION**\n\n"
        f"• **OPERATION** → `Database Reconciliation` \n"
        f"• **STATUS** → `{status}`\n"
        f"• **PROGRESS** → `{bar}` `{percent}%` "
    )

def get_post_ui(status, bar, percent):
    return (
        f"🛰  **SYSTEM SYNCHRONIZATION**\n\n"
        f"› **OPERATION** : `BROADCAST PROTOCOL` \n"
        f"› **STATUS** : `{status}` \n"
        f"› **PROGRESS** : `{bar}` `{percent}%` "
    )

# --- MATH PRE-PROCESSOR ---
def clean_math_query(query):
    q = query.lower().strip()
    q = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', q)
    q = q.replace('^', '**')
    q = re.sub(r'([a-zA-Z])(\d+)', r'\1**\2', q)
    return q

# --- SAFE GITHUB DATA LAYERS ---
def get_stored_ids():
    if not g or not REPO_NAME:
        logger.warning("GitHub components are unconfigured. Skipping fetch.")
        return []
    try:
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(FILE_PATH)
        content = base64.b64decode(file_content.content).decode()
        return [int(i) for i in content.splitlines() if i.strip().lstrip('-').isdigit()]
    except Exception as e:
        logger.error(f"[GitHub Data Fetch Error] Safe fallback triggered: {e}")
        return []

def update_github_file(id_list):
    if not g or not REPO_NAME:
        logger.warning("GitHub components are unconfigured. Skipping push.")
        return False
    try:
        repo = g.get_repo(REPO_NAME)
        new_data = "\n".join(map(str, id_list))
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(FILE_PATH, "Bot: Final Master Update", new_data, contents.sha)
        return True
    except Exception as e:
        logger.error(f"[GitHub Push Failure] Persistent layer skipped: {e}")
        return False

def save_id_to_github(chat_id):
    try:
        ids = get_stored_ids()
        if chat_id not in ids:
            ids.append(chat_id)
            update_github_file(ids)
    except Exception as e:
        logger.error(f"[Async Registration Intercept] Chat registration failure: {e}")

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_added_as_admin(event: ChatMemberUpdated):
    try:
        save_id_to_github(event.chat.id)
    except Exception as e:
        logger.error(f"Error in on_bot_added_as_admin: {e}")

# --- ARMORED HANDLERS ---

@dp.message(Command("sos"))
async def sos_handler(message: types.Message):
    try:
        reply = message.reply_to_message
        if not reply:
            return await message.answer("❌ **Error:** Reply to a suspect to call the police!")

        crime = message.text.replace("/sos", "").strip()
        if not crime:
            crime = "Being too suspicious"

        suspect = reply.from_user
        msg = await message.answer("`Contacting Emergency Services...`")

        sirens = ["🔵🔴🔵🔴", "🔴🔵🔴🔵", "🔵🔴🔵🔴", "🔴🔵🔴🔵"]
        signals = ["📡. . .", "📡.. .", "📡...", "📡...."]
        
        for i in range(4):
            try:
                await msg.edit_text(get_sos_ui("Locating Suspect...", sirens[i], signals[i]), parse_mode="Markdown")
            except Exception as loop_err:
                logger.debug(f"Animation loop frame skip: {loop_err}")
            await asyncio.sleep(0.8)

        final_report = (
            f"📢 **DISPATCH COMPLETE**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **SUSPECT:** `{suspect.first_name}`\n"
            f"🆔 **USER ID:** `{suspect.id}`\n"
            f"⚖️ **CRIME:** `{crime}`\n"
            f"🚓 **UNIT:** En-route to their location!\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🫡🫵 **CASE CLOSED BY POLICE**"
        )
        await msg.edit_text(final_report, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Crash averted in /sos handler: {e}")

@dp.message(Command("calculate"))
async def calc_handler(message: types.Message):
    try:
        question = message.text.replace('/calculate', '').strip()
        if not question: 
            return await message.answer("💡 **Usage:** `/calculate 5*5`")
        
        msg = await message.answer("`Booting Engine...`")

        frames = [
            {"runner": "🏃‍♂️. . . . . . .", "load": "█░░░", "pct": "25%", "face": "🤨"},
            {"runner": ". . 🏃‍♂️. . . . .", "load": "██░░", "pct": "50%", "face": "🧐"},
            {"runner": ". . . . 🏃‍♂️. . .", "load": "███░", "pct": "75%", "face": "🫤"},
            {"runner": ". . . . . . 🏃‍♂️.", "load": "████", "pct": "100%", "face": "😵‍💫"}
        ]

        for frame in frames:
            text = (
                f"⚡ **CALCULATING:** `{question}`\n"
                f"────────────────────\n"
                f"**PROGRESS** | `{frame['runner']}`\n"
                f"**ANSWER** | {frame['face']}\n"
                f"────────────────────\n"
                f"**LOADING** `{frame['load']}` `{frame['pct']}`"
            )
            try:
                await msg.edit_text(text, parse_mode="Markdown")
            except Exception: 
                pass
            await asyncio.sleep(1.0)

        try:
            q = clean_math_query(question)
            ans = f"{sympify(q)}"
            final_text = (
                f"⚡ **CALCULATING:** `{question}`\n"
                f"────────────────────\n"
                f"**PROGRESS** | `. . . . . . . 🫡🫵` \n"
                f"**ANSWER** | ✅ `{ans}`\n"
                f"────────────────────\n"
                f"**LOADING** `████` `100%`"
            )
            await msg.edit_text(final_text, parse_mode="Markdown")
        except Exception as math_err:
            logger.warning(f"Math calculation parsing anomaly: {math_err}")
            await msg.edit_text("❌ **SYNTAX ERROR**")
    except Exception as e:
        logger.error(f"Crash averted in /calculate handler: {e}")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    try:
        if message.from_user.id != OWNER_ID: return
        new_caption = message.text.replace("/post", "").strip()
        reply = message.reply_to_message
        if not reply and not new_caption: 
            return await message.answer("❌ **Error: Content missing.**")

        status_msg = await message.answer("`System Sync...`")
        ids = get_stored_ids()
        
        for i in range(1, 5):
            bar = "█" * i + "░" * (4-i)
            try:
                await status_msg.edit_text(get_post_ui('Broadcasting...', bar, i*25), parse_mode="Markdown")
            except Exception:
                pass
            await asyncio.sleep(0.5)

        sent = 0
        for chat_id in ids:
            try:
                if reply:
                    await reply.send_copy(chat_id=chat_id, caption=new_caption if new_caption else reply.caption)
                else:
                    await bot.send_message(chat_id=chat_id, text=new_caption)
                sent += 1
            except Exception as send_err: 
                logger.debug(f"Broadcast failed for element {chat_id}: {send_err}")
                continue
        
        await status_msg.edit_text(get_post_ui('COMPLETED ✅', '▓▓▓▓▓', 100) + f"\n\n🚀 **Sent to:** `{sent}` groups.", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Crash averted in /post handler: {e}")

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    try:
        if message.from_user.id != OWNER_ID: return
        status_msg = await message.answer("`Accessing DB...`")
        bar_steps = ["░░░░░", "▓░░░░", "▓▓░░░", "▓▓▓░░", "▓▓▓▓░", "▓▓▓▓▓"]
        for i, bar in enumerate(bar_steps):
            try:
                await status_msg.edit_text(get_update_ui('Syncing...', bar, i*20), parse_mode="Markdown")
            except Exception:
                pass
            await asyncio.sleep(0.8)
        ids = get_stored_ids()
        await status_msg.edit_text(get_update_ui('Completed ✓', '▓▓▓▓▓', 100) + f"\n\n📊 **Nodes:** `{len(ids)}`", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Crash averted in /update handler: {e}")

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    try:
        if message.chat.type in ['group', 'supergroup', 'channel']: 
            save_id_to_github(message.chat.id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 MAIN CHANNEL", url="https://t.me/cryptowitholdy")],
            [InlineKeyboardButton(text="📊 TRADING CHANNEL", url="https://t.me/market_analysis1920")]
        ])
        await message.answer("👋 **Welcome to Crypto Owl 🦉**\n━━━━━━━━━━━━━━━━━━━━\nPowered by **TEAM OLDY CRYPTO ❤️‍🩹**", reply_markup=kb, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Crash averted in /start handler: {e}")

@dp.message(Command("delete"))
async def delete_handler(message: types.Message):
    try:
        if message.from_user.id != OWNER_ID: return
        tid = int(message.text.split()[1])
        ids = get_stored_ids()
        if tid in ids:
            ids.remove(tid)
            update_github_file(ids)
            await message.answer(f"🗑 **Deleted Node:** `{tid}`")
    except Exception as e:
        logger.error(f"Crash averted in /delete handler: {e}")

# --- GLOBAL EXTRAORDINARY ERROR MITIGATION LAYER ---
@dp.errors()
async def global_error_mitigator(update: types.Update, exception: Exception):
    tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    logger.critical(f"[FORTRESS GLOBAL WRAPPER CAPTURE]\nException: {exception}\nTraceback:\n{tb}")
    return True

# --- DUAL INTERFACE CONCURRENT RUNNERS ---
async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", lambda r: web.Response(text="Bot Active Protection Layer Layer Operational."))
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Health check web server safely running on port: {port}")
    except Exception as web_err:
        logger.critical(f"Web server initialization failed but execution spared: {web_err}")

async def main():
    # Gather tasks concurrently so that failure in one system cannot chain crash the engine
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot execution stopped safely via system interrupt.")
    except Exception as fatal_err:
        tb = "".join(traceback.format_exception(type(fatal_err), fatal_err, fatal_err.__traceback__))
        print(f"CRITICAL SYSTEM FAILURE AT RUNTIME:\n{tb}")
