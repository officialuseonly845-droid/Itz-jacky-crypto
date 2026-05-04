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

# --- CONFIGURATION (Render Environment Variables) ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = "groups.txt"

bot = Bot(token=TOKEN)
dp = Dispatcher()
g = Github(GITHUB_TOKEN)

# --- PROGRESS BAR ANIMATION ---
async def professional_loading(message: types.Message):
    """Hacker style progress bar animation [███░░░]"""
    bar_steps = [
        "░░░░░░░░░░", "█░░░░░░░░░", "██░░░░░░░░", 
        "███░░░░░░░", "████░░░░░░", "█████░░░░░", 
        "██████░░░░", "███████░░░", "████████░░", 
        "█████████░", "██████████"
    ]
    for i, bar in enumerate(bar_steps):
        percent = i * 10
        try:
            await message.edit_text(
                f"🛰 **System Sync in Progress...**\n"
                f"`[{bar}]` **{percent}%**\n"
                f"Please wait, updating database..."
            )
            await asyncio.sleep(0.6) # Approx 7 seconds total
        except: continue

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

# --- UI BUTTONS ---
def main_menu():
    kb = [
        [InlineKeyboardButton(text="📢 Channel", url="https://t.me/OldyCrypto")],
        [InlineKeyboardButton(text="➕ Add to Group", url=f"https://t.me/{(bot.get_me()).username}?startgroup=true")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- COMMAND HANDLERS ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        save_id_to_github(message.chat.id)
    
    start_text = (
        "👋 **Hello! I am Crypto Owl 🦉**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "I am an advanced management bot with built-in **Calculus** powers.\n\n"
        "✨ **Main Commands:**\n"
        "• `/calculate` - Solve any math (BODMAS to Integration)\n"
        "• `/post` - Broadcast (Owner Only)\n"
        "• `/update` - Sync all active chats\n\n"
        "🛡 **Developed by TEAM ( OLDY CRYPTO ❤️‍🩹 )**"
    )
    await message.answer(start_text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    status_msg = await message.answer("🔄 **Starting Database Sync...**")
    await professional_loading(status_msg)
    
    ids = get_stored_ids()
    report = []
    for cid in ids:
        try:
            chat = await bot.get_chat(cid)
            report.append(f"🟢 **{chat.title}** | `{cid}`")
        except:
            report.append(f"🔴 **Unknown/Left** | `{cid}`")
            
    final_text = (
        "📊 **SYNC COMPLETED SUCCESSFULLY**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ **Active Nodes:** {len(ids)}\n\n"
        + "\n".join(report) +
        "\n━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await status_msg.edit_text(final_text, parse_mode="Markdown")

@dp.message(Command("calculate"))
async def calculate_handler(message: types.Message):
    query = message.text.replace('/calculate', '').strip()
    if not query:
        return await message.answer("💡 **Format:** `/calculate int x^2` or `dy/dx sinx`")
    
    try:
        # Regex to fix user common mistakes (like 2x -> 2*x)
        q = query.lower().replace('^', '**')
        q = re.sub(r'(\d)([a-z\(])', r'\1*\2', q)
        x = symbols('x')
        
        if any(k in q for k in ['int', 'integrate']):
            expr_str = re.sub(r'(int|integrate)', '', q).strip()
            res = integrate(sympify(expr_str), x)
            ans = f"📉 **Integral Result:**\n`∫ {expr_str} dx = {res} + C`"
        elif any(k in q for k in ['diff', 'dy/dx', 'derivative']):
            expr_str = re.sub(r'(diff|dy/dx|derivative)', '', q).strip()
            res = diff(sympify(expr_str), x)
            ans = f"📈 **Derivative Result:**\n`d/dx ({expr_str}) = {res}`"
        else:
            res = sympify(q)
            ans = f"🔢 **Result:** `{res}`"
            
        await message.answer(f"💎 **Crypto Owl Calculator**\n━━━━━━━━━━━━━━━━━━━━\n{ans}", parse_mode="Markdown")
    except Exception:
        await message.answer("❌ **Syntax Error!** Please check your expression.")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    reply = message.reply_to_message
    if not reply:
        return await message.answer("❌ **Reply to a message or album to broadcast!**")

    ids = get_stored_ids()
    sent = 0
    status = await message.answer("🚀 **Broadcasting in progress...**")
    
    for chat_id in ids:
        try:
            # Using copy_message ensures text, photos, and links all go through
            await bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=reply.message_id)
            sent += 1
        except: continue
        
    await status.edit_text(f"✅ **Broadcast Finished!**\nSent to: `{sent}` chats.")

# --- HTTP SERVER FOR RENDER ---
async def handle(request):
    return web.Response(text="Bot is Alive and Running! 🦉")

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    
    # Start Bot Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
