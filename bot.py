import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.methods.copy_messages import CopyMessages
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
known_groups = set()

# --- Admin Discovery ---
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_promoted(event: types.ChatMemberUpdated):
    known_groups.add(event.chat.id)

# --- Start Command ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        known_groups.add(message.chat.id)
    
    start_text = (
        "**HEY! I AM CRYPTO OWL 🦉.**\n\n"
        "**IF YOU MANAGE MANY GROUPS AND CHANNELS AND WANT TO SEND THE SAME MESSAGE TO ALL OF THEM, USE THE /post COMMAND!**\n\n"
        "**HOW TO USE:**\n"
        "**1. SEND YOUR MESSAGE OR MEDIA IN OUR PRIVATE CHAT.**\n"
        "**2. REPLY TO THAT MESSAGE WITH /post.**\n"
        "**3. I WILL INSTANTLY BROADCAST IT TO ALL YOUR REGISTERED GROUPS AND CHANNELS! 🚀**\n\n"
        "**⚠️ NOTE: THE /post COMMAND IS STRICTLY RESTRICTED TO THE OWNER ONLY.**\n\n"
        "**CURRENTLY IN BETA VERSION 🫡.**\n\n"
        "**MADE BY TEAM ( OLDY CRYPTO ❤️‍🩹 )**"
    )
    await message.answer(start_text, parse_mode="Markdown")

# --- Add Channel Command (Inline Mode) ---
@dp.message(Command("addchannel"))
async def add_channel_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    bot_info = await bot.get_me()
    url = f"https://t.me/{bot_info.username}?startchannel=true"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ ADD TO CHANNEL/GROUP", url=url)]])
    await message.answer("Click below to add me to your channel or group:", reply_markup=kb)

# --- Merged Broadcast Logic ---
@dp.message(Command("post"))
async def post_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return

    # Case 1: Reply to message (Media/Album)
    if message.reply_to_message:
        target = message.reply_to_message
        if target.media_group_id:
            history = await bot.get_chat_history(chat_id=target.chat.id, limit=20)
            message_ids = sorted([m.message_id for m in history if m.media_group_id == target.media_group_id])
        else:
            message_ids = [target.message_id]
        
        for chat_id in known_groups:
            try: await bot(CopyMessages(chat_id=chat_id, from_chat_id=target.chat.id, message_ids=message_ids))
            except Exception as e: logging.error(e)
            
    # Case 2: Direct Text
    else:
        text = message.text.replace('/post', '').strip()
        if not text: return await message.answer("⚠️ Send /post [text] or reply to a message.")
        for chat_id in known_groups:
            try: await bot.send_message(chat_id, text)
            except Exception as e: logging.error(e)

    await message.answer("✅ Broadcast complete!")

# --- Server ---
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
