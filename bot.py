import asyncio
import os
import logging
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.methods.copy_messages import CopyMessages
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sympy import sympify, diff, integrate, symbols, sin, cos, tan, log, exp, sqrt

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
SHEET_NAME = os.getenv("SHEET_NAME") 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- GOOGLE SHEETS PERSISTENCE ---
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Using your specific filename
    json_file = "Crypto-owl-memory-94eeb8a1e146.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_file, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

def save_id(chat_id):
    try:
        sheet = get_sheet()
        existing = sheet.col_values(1)
        if str(chat_id) not in existing:
            sheet.append_row([str(chat_id)])
    except Exception as e:
        logging.error(f"Save Error: {e}")

def load_ids():
    try:
        sheet = get_sheet()
        return [int(i) for i in sheet.col_values(1) if i.strip().lstrip('-').isdigit()]
    except Exception:
        return []

# --- POWERFUL MATH ENGINE ---
def solve_math(query):
    try:
        # Clean query: replace ^ with **, add * between numbers and x (e.g. 2x -> 2*x)
        query = query.lower().replace('=', '').strip()
        query = query.replace('^', '**')
        # Fix missing multiplication: 2x -> 2*x
        query = re.sub(r'(\d)([a-zA-Z\(])', r'\1*\2', query)
        
        x = symbols('x')
        
        # Format check for Differentiation
        if any(k in query for k in ['diff', 'dy/dx', 'derivative']):
            expr_str = re.sub(r'(diff|dy/dx|derivative|differentiate)', '', query).strip()
            # Handle sinx -> sin(x)
            expr_str = re.sub(r'(sin|cos|tan|log|sqrt|exp)([a-z0-9])', r'\1(\2)', expr_str)
            result = diff(sympify(expr_str), x)
            return f"📈 **Differentiation:**\n`{result}`"
            
        # Format check for Integration
        elif any(k in query for k in ['int', 'integrate']):
            expr_str = re.sub(r'(int|integrate)', '', query).strip()
            expr_str = re.sub(r'(sin|cos|tan|log|sqrt|exp)([a-z0-9])', r'\1(\2)', expr_str)
            result = integrate(sympify(expr_str), x)
            return f"📉 **Integration:**\n`{result} + C`"
            
        # Standard Math (BODMAS)
        else:
            # Handle sinx -> sin(x) for normal calculation too
            query = re.sub(r'(sin|cos|tan|log|sqrt|exp)([a-z0-9])', r'\1(\2)', query)
            result = sympify(query)
            return f"🔢 **Result:** `{result}`"
    except Exception as e:
        logging.error(f"Math Error: {e}")
        return None

# --- HANDLERS ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        save_id(message.chat.id)
    
    start_text = (
        "**HEY! I AM CRYPTO OWL 🦉.**\n\n"
        "**IF YOU MANAGE MANY GROUPS AND CHANNELS, USE THE /post COMMAND!**\n\n"
        "**HOW TO USE:**\n"
        "**1. REPLY TO ANY MESSAGE/ALBUM WITH /post.**\n"
        "**2. OR TYPE /post [TEXT] FOR DIRECT BROADCAST.**\n\n"
        "**MADE BY TEAM ( OLDY CRYPTO ❤️‍🩹 )**"
    )
    await message.answer(start_text, parse_mode="Markdown")

@dp.message(Command("addchannel"))
async def add_channel_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    bot_info = await bot.get_me()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ ADD TO GROUP", url=f"https://t.me/{bot_info.username}?startgroup=true")],
        [InlineKeyboardButton(text="➕ ADD TO CHANNEL", url=f"https://t.me/{bot_info.username}?startchannel=true")]
    ])
    await message.answer("Select where to add the bot:", reply_markup=kb)

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    active_ids = load_ids()
    chat_names = []
    
    status_msg = await message.answer("🔄 **Syncing with Google Sheets...**")
    
    for chat_id in active_ids:
        try:
            chat = await bot.get_chat(chat_id)
            chat_names.append(f"• {chat.title} (`{chat_id}`)")
        except:
            chat_names.append(f"• Unknown/Hidden Chat (`{chat_id}`)")
            
    response = f"✅ **Sync Complete!**\n\n**Active in {len(active_ids)} chats:**\n" + "\n".join(chat_names)
    await status_msg.edit_text(response, parse_mode="Markdown")

@dp.message(Command("calculate"))
async def calculate_handler(message: types.Message):
    query = message.text.replace('/calculate', '').strip()
    if not query:
        return await message.answer("Please provide a question!")
    ans = solve_math(query)
    await message.reply(ans if ans else "❌ Calculation error. Check your format.")

@dp.message(lambda message: re.search(r'^\d+[\+\-\*/\^]\d+', message.text))
async def auto_math(message: types.Message):
    ans = solve_math(message.text)
    if ans: await message.reply(ans, parse_mode="Markdown")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    target = message.reply_to_message
    active_ids = load_ids()
    
    if target:
        if target.media_group_id:
            history = await bot.get_chat_history(chat_id=target.chat.id, limit=20)
            msg_ids = sorted([m.message_id for m in history if m.media_group_id == target.media_group_id])
        else:
            msg_ids = [target.message_id]
            
        for gid in active_ids:
            try: await bot(CopyMessages(chat_id=gid, from_chat_id=target.chat.id, message_ids=msg_ids))
            except: continue
    else:
        text = message.text.replace('/post', '').strip()
        if text:
            for gid in active_ids:
                try: await bot.send_message(gid, text)
                except: continue
    await message.answer(f"✅ Sent to {len(active_ids)} chats.")

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_promoted(event: types.ChatMemberUpdated):
    save_id(event.chat.id)

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is Live"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
