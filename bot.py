import asyncio
import os
import logging
import re
import base64
from github import Github
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sympy import sympify, diff, integrate, symbols

# --- CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = "groups.txt"

bot = Bot(token=TOKEN)
dp = Dispatcher()
g = Github(GITHUB_TOKEN)

# --- SYNC INTERFACE GENERATOR ---
def get_sync_ui(operation, status, progress_bar, percent):
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃            🛰 SYSTEM SYNC INTERFACE          ┃\n"
        f"┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩\n"
        f"┃ OPERATION      : {operation:<25} ┃\n"
        f"┃ STATUS         : {status:<25} ┃\n"
        f"┃ PROGRESS       : {progress_bar} {percent}%     ┃\n"
        f"┃ TIMESTAMP      : SYNCHRONIZED               ┃\n"
        f"└──────────────────────────────────────────────┘"
    )

# --- LOADING ANIMATION LOGIC ---
async def run_animation(message, operation, duration=0.5):
    bar_steps = ["░░░░░░░░░░", "██░░░░░░░░", "████░░░░░░", "██████░░░░", "████████░░", "██████████"]
    for i, bar in enumerate(bar_steps):
        percent = i * 20
        try:
            await message.edit_text(f"`{get_sync_ui(operation, 'PROCESSING...', bar, percent)}`", parse_mode="MarkdownV2")
            await asyncio.sleep(duration)
        except: continue
    
    await message.edit_text(f"`{get_sync_ui(operation, 'COMPLETED ✅', '██████████', 100)}`", parse_mode="MarkdownV2")
    await asyncio.sleep(1)

# --- GITHUB PERSISTENCE ---
def get_stored_ids():
    try:
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(FILE_PATH)
        content = base64.b64decode(file_content.content).decode()
        return [int(i) for i in content.splitlines() if i.strip().lstrip('-').isdigit()]
    except: return []

def save_id_to_github(chat_id):
    try:
        repo = g.get_repo(REPO_NAME)
        ids = get_stored_ids()
        if chat_id not in ids:
            ids.append(chat_id)
            new_data = "\n".join(map(str, ids))
            try:
                contents = repo.get_contents(FILE_PATH)
                repo.update_file(FILE_PATH, "Bot: Update Group IDs", new_data, contents.sha)
            except:
                repo.create_file(FILE_PATH, "Bot: Initialize IDs", new_data)
    except Exception as e: logging.error(f"Storage Error: {e}")

# --- KEYBOARDS ---
async def get_add_me_kb():
    bot_user = await bot.get_me()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Bot to GC/Channel", url=f"https://t.me/{bot_user.username}?startgroup=true")],
        [InlineKeyboardButton(text="📢 Support Channel", url="https://t.me/OldyCrypto")]
    ])
    return kb

# --- HANDLERS ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        save_id_to_github(message.chat.id)
    
    welcome_text = (
        "👋 **Hello! I am Crypto Owl 🦉**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "I am an advanced management bot with **Calculus** powers.\n\n"
        "✨ **Main Commands:**\n"
        "• `/calculate` - Solve any math\n"
        "• `/post` - Broadcast (Owner Only)\n"
        "• `/update` - Sync all active chats\n"
        "• `/addchannel` - Add me to your group\n\n"
        "🛡 **Developed by TEAM ( OLDY CRYPTO ❤️‍🩹 )**"
    )
    await message.answer(welcome_text, reply_markup=await get_add_me_kb(), parse_mode="Markdown")

@dp.message(Command("addchannel"))
async def add_channel_handler(message: types.Message):
    await message.answer(
        "✨ **Add Me To Your Group/Channel**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Click the button below to add me as an Admin to your group or channel for broadcasting.",
        reply_markup=await get_add_me_kb(),
        parse_mode="Markdown"
    )

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    status_msg = await message.answer("`Initializing...`", parse_mode="MarkdownV2")
    await run_animation(status_msg, "DATABASE RECONCILIATION", duration=0.8)
    
    ids = get_stored_ids()
    report = []
    for cid in ids:
        try:
            chat = await bot.get_chat(cid)
            report.append(f"🟢 **{chat.title}** | `{cid}`")
        except: report.append(f"🔴 **Unknown** | `{cid}`")
            
    await status_msg.answer(f"📊 **SYNC COMPLETE**\n━━━━━━━━━━━━━━\n" + "\n".join(report), parse_mode="Markdown")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    reply = message.reply_to_message
    if not reply: return await message.answer("❌ Reply to a post to broadcast!")

    status_msg = await message.answer("`Starting Broadcast...`", parse_mode="MarkdownV2")
    await run_animation(status_msg, "BROADCAST PROTOCOL", duration=0.4)

    ids = get_stored_ids()
    sent = 0
    for chat_id in ids:
        try:
            await bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=reply.message_id)
            sent += 1
        except: continue
        
    await status_msg.answer(f"🚀 **Broadcast Finished!**\nSent to: `{sent}` chats.", parse_mode="Markdown")

@dp.message(Command("calculate"))
async def calculate_handler(message: types.Message):
    query = message.text.replace('/calculate', '').strip()
    if not query: return await message.answer("💡 Usage: `/calculate int x^2` or `dy/dx sinx`")
    
    try:
        q = query.lower().replace('^', '**')
        q = re.sub(r'(\d)([a-z\(])', r'\1*\2', q)
        x = symbols('x')
        if any(k in q for k in ['int', 'integrate']):
            expr = re.sub(r'(int|integrate)', '', q).strip()
            res = integrate(sympify(expr), x)
            ans = f"📉 **Integral:**\n`∫ {expr} dx = {res} + C`"
        elif any(k in q for k in ['diff', 'dy/dx']):
            expr = re.sub(r'(diff|dy/dx)', '', q).strip()
            res = diff(sympify(expr), x)
            ans = f"📈 **Derivative:**\n`d/dx ({expr}) = {res}`"
        else:
            ans = f"🔢 **Result:** `{sympify(q)}`"
        await message.answer(f"💎 **Calculator**\n━━━━━━━━━━━━\n{ans}", parse_mode="Markdown")
    except: await message.answer("❌ Invalid Syntax!")

# --- SERVER ---
async def handle(request): return web.Response(text="Bot Alive! 🦉")
async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
