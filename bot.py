import asyncio
import os
import logging
import re
import base64
from github import Github
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from sympy import sympify, diff, integrate, symbols

# --- CONFIG ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = "groups.txt"

bot = Bot(token=TOKEN)
dp = Dispatcher()
g = Github(GITHUB_TOKEN)

# --- UI INTERFACE ---
def get_sync_ui(operation, status, bar, percent):
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃            🛰 SYSTEM SYNC INTERFACE          ┃\n"
        f"┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩\n"
        f"┃ OPERATION      : {operation:<25} ┃\n"
        f"┃ STATUS         : {status:<25} ┃\n"
        f"┃ PROGRESS       : {bar} {percent}%     ┃\n"
        f"┃ TIMESTAMP      : SYNCHRONIZED               ┃\n"
        f"└──────────────────────────────────────────────┘"
    )

# --- GITHUB LOGIC ---
def get_stored_ids():
    try:
        repo = g.get_repo(REPO_NAME)
        file_content = repo.get_contents(FILE_PATH)
        content = base64.b64decode(file_content.content).decode()
        return [int(i) for i in content.splitlines() if i.strip().lstrip('-').isdigit()]
    except: return []

def update_github_file(id_list):
    try:
        repo = g.get_repo(REPO_NAME)
        new_data = "\n".join(map(str, id_list))
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(FILE_PATH, "Bot: Sync Database", new_data, contents.sha)
        return True
    except: return False

def save_id_to_github(chat_id):
    ids = get_stored_ids()
    if chat_id not in ids:
        ids.append(chat_id)
        update_github_file(ids)

# --- AUTO-ADD HANDLER ---
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_added_as_admin(event: ChatMemberUpdated):
    save_id_to_github(event.chat.id)

# --- HANDLERS ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        save_id_to_github(message.chat.id)
    bot_user = await bot.get_me()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 MAIN CHANNEL", url="https://t.me/cryptowitholdy")],
        [InlineKeyboardButton(text="📊 TRADING CHANNEL", url="https://t.me/market_analysis1920")],
        [InlineKeyboardButton(text="➕ ADD ME TO GC", url=f"https://t.me/{bot_user.username}?startgroup=true")]
    ])
    await message.answer("👋 **Welcome to Crypto Owl 🦉**\n━━━━━━━━━━━━━━━━━━━━━━━━\nPowered by **TEAM OLDY CRYPTO ❤️‍🩹**", reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("addchannel"))
async def add_ch_handler(message: types.Message):
    bot_user = await bot.get_me()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Add Me to Your Group", url=f"https://t.me/{bot_user.username}?startgroup=true")]])
    await message.answer("✨ **Invite me as an Admin to start broadcasting!**", reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    status_msg = await message.answer("`Initializing...`", parse_mode="MarkdownV2")
    
    bar_steps = ["░░░░░░░░░░", "██░░░░░░░░", "████░░░░░░", "██████░░░░", "████████░░", "██████████"]
    for i, bar in enumerate(bar_steps):
        await status_msg.edit_text(f"`{get_sync_ui('DATABASE RECONCILIATION', 'PROCESSING...', bar, i*20)}`", parse_mode="MarkdownV2")
        await asyncio.sleep(0.4)

    ids = get_stored_ids()
    chat_names = []
    for cid in ids:
        try:
            chat = await bot.get_chat(cid)
            chat_names.append(f"✅ {chat.title}")
        except: continue

    final_report = f"`{get_sync_ui('DATABASE RECONCILIATION', 'COMPLETED ✅', '██████████', 100)}`" + f"\n\n📊 **SYNC COMPLETE**\n" + "\n".join(chat_names)
    await status_msg.edit_text(final_report, parse_mode="MarkdownV2")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    text_to_send = message.text.replace("/post", "").strip()
    reply = message.reply_to_message
    if not reply and not text_to_send: return await message.answer("❌ Error: Provide content")

    status_msg = await message.answer("`Booting...`", parse_mode="MarkdownV2")
    
    # 1. Show Progress First
    bar_steps = ["░░░░░░░░░░", "████░░░░░░", "████████░░", "██████████"]
    for i, bar in enumerate(bar_steps):
        await status_msg.edit_text(f"`{get_sync_ui('BROADCAST PROTOCOL', 'SENDING...', bar, i*33 if i<3 else 100)}`", parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)

    # 2. Run Background Broadcast
    ids = get_stored_ids()
    sent = 0
    for chat_id in ids:
        try:
            if reply: await bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=reply.message_id)
            else: await bot.send_message(chat_id=chat_id, text=text_to_send)
            sent += 1
        except: continue
    
    # 3. Final Step: FORCE EDIT to SENT ✅
    # Hum yahan thoda delay de rahe hain taaki Telegram api sync ho jaye
    await asyncio.sleep(0.5) 
    final_post_ui = f"`{get_sync_ui('BROADCAST PROTOCOL', 'SENT ✅', '██████████', 100)}`" + f"\n\n🚀 **Broadcast Finished!**\nSent to: `{sent}` chats."
    await status_msg.edit_text(final_post_ui, parse_mode="MarkdownV2")

@dp.message(Command("delete"))
async def delete_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        target_id = int(message.text.split()[1])
        ids = get_stored_ids()
        if target_id in ids:
            ids.remove(target_id)
            update_github_file(ids)
            await message.answer(f"🗑 **Deleted:** `{target_id}`")
    except: await message.answer("💡 Usage: `/delete ID`")

@dp.message(Command("calculate"))
async def calc_handler(message: types.Message):
    query = message.text.replace('/calculate', '').strip()
    if not query: return
    try:
        q = query.lower().replace('^', '**')
        q = re.sub(r'(\d)([a-z\(])', r'\1*\2', q)
        x = symbols('x')
        if 'int' in q: res = integrate(sympify(q.replace('int','')), x); ans = f"∫ dx = {res} + C"
        elif 'diff' in q or 'dy/dx' in q: res = diff(sympify(re.sub(r'(diff|dy/dx)','',q)), x); ans = f"d/dx = {res}"
        else: ans = f"Result: {sympify(q)}"
        await message.answer(f"🔢 **Math Owl**\n`{ans}`", parse_mode="Markdown")
    except: await message.answer("❌ Syntax Error")

async def main():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot Active!"))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

