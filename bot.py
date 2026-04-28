import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, IS_ADMIN

# --- Configuration ---
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
# In-memory storage for chat IDs
known_groups = set()

# --- Admin Auto-Discovery ---
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_promoted(event: types.ChatMemberUpdated):
    known_groups.add(event.chat.id)
    logging.info(f"Bot promoted in chat/channel: {event.chat.id}")

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

# --- Broadcast Logic ---
@dp.message(Command("post"))
async def post_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    
    # Check if user is replying to something
    target = message.reply_to_message
    if not target:
        return await message.answer("⚠️ Reply to a message/media with /post to broadcast it.")

    count = 0
    for chat_id in known_groups:
        try:
            # Copy the entire message (captions/media/text preserved)
            await bot.copy_message(chat_id, target.chat.id, target.message_id)
            count += 1
        except Exception as e:
            logging.error(f"Failed to post to {chat_id}: {e}")
            
    await message.answer(f"✅ Broadcasted successfully to {count} chats.")

# --- Web Server (Uptime) ---
async def start_http_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is alive!"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080))).start()

# --- Main Entry ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(start_http_server(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
