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

# --- UI INTERFACE (Redesigned for Ratio) ---
def get_sync_ui(operation, status, bar, percent):
    # Width thodi kam rakhi hai taaki GC mein break na ho
    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃   🛰 SYSTEM SYNC INTERFACE   ┃\n"
        f"┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩\n"
        f"┃ OP: {operation:<22} ┃\n"
        f"┃ ST: {status:<22} ┃\n"
        f"┃ PR: {bar} {percent:>3}% ┃\n"
        f"┃ TS: SYNCHRONIZED           ┃\n"
        f"└━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘"
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
    await message.answer("👋 **Welcome to Crypto Owl 🦉**\n━━━━━━━━━━━━━━━━━━━━\nPowered by **TEAM OLDY CRYPTO ❤️‍🩹**", reply_markup=kb, parse_mode="Markdown")

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    status_msg = await message.answer("`Initializing...`", parse_mode="MarkdownV2")
    
    # Shortened names for better fit
    bar_steps = ["░░░░░░░░░░", "██░░░░░░░░", "████░░░░░░", "██████░░░░", "████████░░", "██████████"]
    for i, bar in enumerate(bar_steps):
        ui = get_sync_ui('DB_RECONCILIATION', 'PROCESSING...', bar, i*20)
        await status_msg.edit_text(f"```\n{ui}\n```", parse_mode="MarkdownV2")
        await asyncio.sleep(0.4)

    ids = get_stored_ids()
    chat_names = []
    for cid in ids:
        try:
            chat = await bot.get_chat(cid)
            chat_names.append(f"✅ {chat.title}")
        except: continue

    res_ui = get_sync_ui('DB_RECONCILIATION', 'COMPLETED ✅', '██████████', 100)
    final_report = f"```\n{res_ui}\n```" + f"\n\n📊 **SYNC COMPLETE**\n" + "\n".join(chat_names)
    await status_msg.edit_text(final_report, parse_mode="MarkdownV2")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    text_to_send = message.text.replace("/post", "").strip()
    reply = message.reply_to_message
    if not reply and not text_to_send: return await message.answer("❌ Provide content!")

    status_msg = await message.answer("`Booting...`", parse_mode="MarkdownV2")
    
    bar_steps = ["░░░░░░░░░░", "████░░░░░░", "████████░░", "██████████"]
    for i, bar in enumerate(bar_steps):
        ui = get_sync_ui('BROADCAST_PROTO', 'SENDING...', bar, i*33 if i<3 else 100)
        await status_msg.edit_text(f"```\n{ui}\n```", parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)

    ids = get_stored_ids()
    sent = 0
    for chat_id in ids:
        try:
            if reply: await bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=reply.message_id)
            else: await bot.send_message(chat_id=chat_id, text=text_to_send)
            sent += 1
        except: continue
    
    await asyncio.sleep(0.5) 
    final_ui = get_sync_ui('BROADCAST_PROTO', 'SENT ✅', '██████████', 100)
    final_post_ui = f"
http://googleusercontent.com/immersive_entry_chip/0

### **Changes Jo Ratio Sahi Karenge:**
1.  **Code Block Wrapping:** Maine saare interface boxes ko ` ```\n...\n``` ` ke andar wrap kiya hai. Isse Telegram **Monospace Font** use karta hai, jisme har character ki width barabar hoti hai. Alignment kabhi nahi bigdegi.
2.  **Reduced Width:** Box ki width ko 45 characters se ghata kar **30 characters** kar diya hai. Ab ye chhote se chhote mobile screen pe bhi ek line mein fit aayega.
3.  **Space Padding:** `OP:` (Operation) aur `ST:` (Status) jaise labels use kiye hain taaki content ke liye jagah zyada bache aur ratio clean lage.
4.  **Force Edit Fix:** Jaise hi loop khatam hoga, ye `SENT ✅` update kar dega.

Ab isse deploy kar, interface ekdam professional aur aligned dikhega! 🦉🚀

