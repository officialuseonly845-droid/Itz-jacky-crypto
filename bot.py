import asyncio
import os
import logging
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.methods.copy_messages import CopyMessages
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sympy import sympify, diff, integrate, symbols

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
known_groups = set() # Session memory

# --- ADVANCED MATH LOGIC ---
def solve_math(query):
    try:
        query = query.lower().replace('=', '').strip()
        x = symbols('x')
        
        # 1. Differentiation
        if any(keyword in query for keyword in ['diff', 'dy/dx', 'derivative']):
            expr_str = re.sub(r'(differentiate|diff|dy/dx|derivative)', '', query).strip()
            expr_str = expr_str.replace('^', '**')
            result = diff(sympify(expr_str), x)
            return f"📈 **Differentiation Result:**\n`{result}`"
        
        # 2. Integration
        elif any(keyword in query for keyword in ['int', 'integrate']):
            expr_str = re.sub(r'(integrate|int)', '', query).strip()
            expr_str = expr_str.replace('^', '**')
            result = integrate(sympify(expr_str), x)
            return f"📉 **Integration Result:**\n`{result} + C`"
        
        # 3. Standard Math
        else:
            if re.search(r'[\+\-\*/\^0-9]', query):
                expr_str = query.replace('^', '**')
                result = sympify(expr_str)
                return f"🔢 **Result:** `{result}`"
        return None
    except Exception as e:
        logging.error(f"Math Error: {e}")
        return None

# --- HANDLERS ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # Auto-save chat ID if bot is started in a group
    if message.chat.type in ['group', 'supergroup', 'channel']:
        known_groups.add(message.chat.id)
    
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
    
    # Inline buttons for both Group and Channel addition
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ ADD TO GROUP", url=f"https://t.me/{bot_info.username}?startgroup=true")],
        [InlineKeyboardButton(text="➕ ADD TO CHANNEL", url=f"https://t.me/{bot_info.username}?startchannel=true")]
    ])
    await message.answer("Click a button below to add me as an Admin:", reply_markup=kb)

@dp.message(Command("update"))
async def update_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    await message.answer(f"🔄 **Sync Status:**\nActive in `{len(known_groups)}` chats.\nNote: Restart clears memory unless I am re-added or messaged.")

@dp.message(Command("calculate"))
async def calculate_handler(message: types.Message):
    query = message.text.replace('/calculate', '').strip()
    if not query:
        return await message.answer("Please provide a math question!")
    answer = solve_math(query)
    await message.reply(answer if answer else "❌ Could not solve that expression.", parse_mode="Markdown")

# Auto-math detection for messages like "5+5"
@dp.message(lambda message: re.search(r'^\d+[\+\-\*/\^]\d+', message.text))
async def auto_math_handler(message: types.Message):
    answer = solve_math(message.text)
    if answer:
        await message.reply(answer, parse_mode="Markdown")

@dp.message(Command("post"))
async def post_handler(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    target = message.reply_to_message
    if target:
        # Album detection
        if target.media_group_id:
            history = await bot.get_chat_history(chat_id=target.chat.id, limit=20)
            msg_ids = sorted([m.message_id for m in history if m.media_group_id == target.media_group_id])
        else:
            msg_ids = [target.message_id]

        for chat_id in known_groups:
            try:
                await bot(CopyMessages(chat_id=chat_id, from_chat_id=target.chat.id, message_ids=msg_ids))
            except Exception: continue
        await message.answer(f"✅ Broadcasted to {len(known_groups)} chats.")
    else:
        # Direct text broadcast
        text = message.text.replace('/post', '').strip()
        if text:
            for chat_id in known_groups:
                try: await bot.send_message(chat_id, text)
                except: continue
            await message.answer(f"✅ Text broadcasted to {len(known_groups)} chats.")

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_promoted(event: types.ChatMemberUpdated):
    known_groups.add(event.chat.id)

# --- SERVER FOR RENDER ---
async def handle(request):
    return web.Response(text="Crypto Owl is Online")

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080))).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
