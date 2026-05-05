import asyncio
import os
import logging
import re
import base64
import random
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

# --- UI INTERFACES ---
def get_update_ui(status, bar, percent):
    return (f"🛰  **SYSTEM SYNC**\n\n• **OP** → `Database Reconciliation` \n• **ST** → `{status}`\n• **PR** → `{bar}` `{percent}%` ")

def get_post_ui(status, bar, percent):
    return (f"🛰  **SYSTEM SYNC**\n\n› **OP** : `BROADCAST PROTOCOL` \n› **ST** : `{status}` \n› **PR** : `{bar}` `{percent}%` ")

# --- SMART MATH PRE-PROCESSOR ---
def clean_math_query(query):
    q = query.lower().strip()
    q = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', q) # 2x -> 2*x
    q = q.replace('^', '**') # x^2 -> x**2
    q = re.sub(r'([a-zA-Z])(\d+)', r'\1**\2', q) # x2 -> x**2
    return q

# --- GITHUB DATABASE LOGIC ---
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
        repo.update_file(FILE_PATH, "Bot: DB Sync", new_data, contents.sha)
        return True
    except: return False

def save_id_to_github(chat_id):
    ids = get_stored_ids()
    if chat_id not in ids:
        ids.append(chat_id)
        update_github_file(ids)

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_added_as_admin(event: ChatMemberUpdated):
    save_id_to_github(event.chat.id)

# --- HANDLERS ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']: save_id_to_github(message.chat.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 MAIN CHANNEL", url="https://t.me/cryptowitholdy")],
        [InlineKeyboardButton(text="📊 TRADING CHANNEL", url="https://t.me/market_analysis1920")]
    ])
    await message.answer("👋 **Welcome to Crypto Owl 🦉**\n━━━━━━━━━━━━━━━\nPowered by **TEAM OLDY CRYPTO ❤️‍🩹**", reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    status_msg = await message.answer("`Accessing Database...`", parse_mode="Markdown")
    bar_steps = ["░░░░░", "▓░░░░", "▓▓░░░", "▓▓▓░░", "▓▓▓▓░", "▓▓▓▓▓"]
    for i, bar in enumerate(bar_steps):
        await status_msg.edit_text(get_update_ui('Processing...', bar, i*20), parse_mode="Markdown")
        await asyncio.sleep(0.3)
    ids = get_stored_ids()
    await status_msg.edit_text(get_update_ui('Completed ✓', '▓▓▓▓▓', 100) + f"\n\n📊 **Database Synced:** `{len(ids)}` nodes.", parse_mode="Markdown")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    new_caption = message.text.replace("/post", "").strip()
    reply = message.reply_to_message
    if not reply and not new_caption: return await message.answer("❌ **Error:** Reply to a post or provide text content.")

    status_msg = await message.answer("`Preparing Broadcast...`", parse_mode="Markdown")
    ids = get_stored_ids()
    sent = 0
    for chat_id in ids:
        try:
            if reply:
                if new_caption: await reply.send_copy(chat_id=chat_id, caption=new_caption)
                else: await reply.send_copy(chat_id=chat_id)
            else: await bot.send_message(chat_id=chat_id, text=new_caption)
            sent += 1
        except: continue
    await status_msg.edit_text(get_post_ui('SENT ✅', '▓▓▓▓▓', 100) + f"\n\n🚀 **Broadcast Finished!**\nSent to: `{sent}` nodes.", parse_mode="Markdown")

@dp.message(Command("calculate"))
async def calc_handler(message: types.Message):
    raw_query = message.text.replace('/calculate', '').strip()
    if not raw_query: return await message.answer("💡 **Usage:** `/calculate 2x + 10` or `int x^2`")
    
    status_msg = await message.answer("`Booting Math Engine...`", parse_mode="Markdown")
    
    phrases = ["Initializing Core...", "Neural Parsing...", "Mapping Logic...", "Optimizing Result...", "Finalizing Scan..."]
    
    # 4-Second Sprint Loop Animation (14 frames * 0.3s)
    for i in range(14):
        # Infinite Sprint Logic: Man resets every 5 frames
        pos = i % 5 
        track = ["."] * 5
        track[pos] = "🏃‍♂️"
        running_man = "💨 " + " . ".join(track)
        
        progress = min(i * 8, 100)
        bar = "█" * (i % 6) + "░" * (5 - (i % 6))
        
        ui = (
            f"🏃‍♂️ **MATH_ENGINE::RUNNING**\n\n"
            f"```\n{running_man}\n```\n"
            f"• **STATUS** → `{phrases[i % len(phrases)]}`\n"
            f"• **LOAD** → `[{bar}]` **{progress}%**\n\n"
            f"🦉 *Math Owl is sprinting for you...*"
        )
        await status_msg.edit_text(ui, parse_mode="Markdown")
        await asyncio.sleep(0.3)

    try:
        q = clean_math_query(raw_query)
        x = symbols('x')
        if q.startswith('int'):
            expr = q.replace('int', '').strip()
            ans = f"∫({expr}) dx = {integrate(sympify(expr), x)} + C"
        elif q.startswith('diff'):
            expr = q.replace('diff', '').strip()
            ans = f"d/dx ({expr}) = {diff(sympify(expr), x)}"
        else:
            ans = f"Result: {sympify(q)}"
        
        await status_msg.edit_text(f"🔢 **ANALYSIS COMPLETE**\n━━━━━━━━━━━━━━━━━━━━\n📥 **INPUT:** `{raw_query}`\n📤 **OUTPUT:** `{ans}`\n\n✅ `COMPUTATION SUCCESSFUL`", parse_mode="Markdown")
    except:
        await status_msg.edit_text("❌ **SYNTAX ERROR**\nEnsure your mathematical expression is valid.", parse_mode="Markdown")

@dp.message(Command("delete"))
async def delete_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    try:
        tid = int(message.text.split()[1])
        ids = get_stored_ids()
        if tid in ids:
            ids.remove(tid)
            update_github_file(ids)
            await message.answer(f"🗑 **Deleted Node:** `{tid}`")
    except: pass

async def main():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot Status: Online"))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
