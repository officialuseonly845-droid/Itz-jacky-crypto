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
        repo.update_file(FILE_PATH, "Bot: Final Master Update", new_data, contents.sha)
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

@dp.message(Command("sos"))
async def sos_handler(message: types.Message):
    reply = message.reply_to_message
    if not reply:
        return await message.answer("❌ **Error:** Reply to a suspect to call the police!")

    # Custom Crime Logic
    crime = message.text.replace("/sos", "").strip()
    if not crime:
        crime = "Being too suspicious"

    suspect = reply.from_user
    msg = await message.answer("`Contacting Emergency Services...`")

    # Siren Animation
    sirens = ["🔵🔴🔵🔴", "🔴🔵🔴🔵", "🔵🔴🔵🔴", "🔴🔵🔴🔵"]
    signals = ["📡. . .", "📡.. .", "📡...", "📡...."]
    
    for i in range(4):
        await msg.edit_text(get_sos_ui("Locating Suspect...", sirens[i], signals[i]), parse_mode="Markdown")
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

@dp.message(Command("calculate"))
async def calc_handler(message: types.Message):
    question = message.text.replace('/calculate', '').strip()
    if not question: return await message.answer("💡 **Usage:** `/calculate 5*5`")
    
    msg = await message.answer("`Booting Engine...`")

    # Aadmi track par daudega (Dots track)
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
        except: pass
        await asyncio.sleep(1.0)

    try:
        q = clean_math_query(question)
        ans = f"{sympify(q)}"
        # Final result - runner replaced with 🫡🫵
        final_text = (
            f"⚡ **CALCULATING:** `{question}`\n"
            f"────────────────────\n"
            f"**PROGRESS** | `. . . . . . . 🫡🫵` \n"
            f"**ANSWER** | ✅ `{ans}`\n"
            f"────────────────────\n"
            f"**LOADING** `████` `100%`"
        )
        await msg.edit_text(final_text, parse_mode="Markdown")
    except:
        await msg.edit_text("❌ **SYNTAX ERROR**")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    new_caption = message.text.replace("/post", "").strip()
    reply = message.reply_to_message
    if not reply and not new_caption: return await message.answer("❌ **Error: Content missing.**")

    status_msg = await message.answer("`System Sync...`")
    ids = get_stored_ids()
    
    for i in range(1, 5):
        bar = "█" * i + "░" * (4-i)
        await status_msg.edit_text(get_post_ui('Broadcasting...', bar, i*25), parse_mode="Markdown")
        await asyncio.sleep(0.5)

    sent = 0
    for chat_id in ids:
        try:
            if reply:
                # Fixed media + caption handling
                await reply.send_copy(chat_id=chat_id, caption=new_caption if new_caption else reply.caption)
            else:
                await bot.send_message(chat_id=chat_id, text=new_caption)
            sent += 1
        except Exception: continue
    
    await status_msg.edit_text(get_post_ui('COMPLETED ✅', '▓▓▓▓▓', 100) + f"\n\n🚀 **Sent to:** `{sent}` groups.", parse_mode="Markdown")

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    status_msg = await message.answer("`Accessing DB...`")
    bar_steps = ["░░░░░", "▓░░░░", "▓▓░░░", "▓▓▓░░", "▓▓▓▓░", "▓▓▓▓▓"]
    for i, bar in enumerate(bar_steps):
        await status_msg.edit_text(get_update_ui('Syncing...', bar, i*20), parse_mode="Markdown")
        await asyncio.sleep(0.8)
    ids = get_stored_ids()
    await status_msg.edit_text(get_update_ui('Completed ✓', '▓▓▓▓▓', 100) + f"\n\n📊 **Nodes:** `{len(ids)}`", parse_mode="Markdown")

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']: save_id_to_github(message.chat.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 MAIN CHANNEL", url="https://t.me/cryptowitholdy")],
        [InlineKeyboardButton(text="📊 TRADING CHANNEL", url="https://t.me/market_analysis1920")]
    ])
    await message.answer("👋 **Welcome to Crypto Owl 🦉**\n━━━━━━━━━━━━━━━━━━━━\nPowered by **TEAM OLDY CRYPTO ❤️‍🩹**", reply_markup=kb, parse_mode="Markdown")

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
    app.router.add_get("/", lambda r: web.Response(text="Bot Active"))
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
