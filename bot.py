import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CMC_API_KEY = os.getenv("CMC_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()
known_groups = set()

# --- Discovery: Bot added as Admin ---
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_promoted(event: types.ChatMemberUpdated):
    known_groups.add(event.chat.id)
    logging.info(f"Bot promoted in: {event.chat.id}")

# --- Commands ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        known_groups.add(message.chat.id)
    await message.answer("HEY I AM CRYPTO OWL 🦉.")

@dp.message(Command("addchannel"))
async def add_channel_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    bot_info = await bot.get_me()
    url = f"https://t.me/{bot_info.username}?startchannel=true"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Add to Channel", url=url)]])
    await message.answer("Click below to add me to your channel:", reply_markup=kb)

@dp.message(Command("price"))
async def price_cmd(message: types.Message):
    args = message.text.split()
    symbol = args[1].upper() if len(args) > 1 else "BTC"
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol={symbol}"
            headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
                price = data['data'][symbol]['quote']['USD']['price']
                await message.answer(f"💰 *{symbol}* Price: ${price:,.2f}", parse_mode="Markdown")
    except Exception:
        await message.answer("Could not fetch price. Check the symbol.")

@dp.message(Command("post"))
async def post_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    caption = message.caption or message.text.replace('/post', '').strip()
    photo = message.photo[-1].file_id if message.photo else None
    
    for chat_id in known_groups:
        try:
            if photo: await bot.send_photo(chat_id, photo, caption=caption)
            else: await bot.send_message(chat_id, caption)
        except Exception as e:
            logging.error(f"Post failed for {chat_id}: {e}")
    await message.answer(f"Broadcast sent to {len(known_groups)} chats.")

# --- Web Server (Uptime) ---
async def start_http_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is alive!"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080))).start()

async def main():
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(start_http_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
