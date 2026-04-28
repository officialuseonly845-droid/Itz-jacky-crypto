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

# Memory: Bot ki local list
known_groups = set()

# Admin Auto-Discovery
@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_ADMIN))
async def on_bot_promoted(event: types.ChatMemberUpdated):
    known_groups.add(event.chat.id)
    logging.info(f"Bot automatically added to: {event.chat.id}")

# --- Update Command (Force Scan) ---
@dp.message(Command("update"))
async def update_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    # Tu jab /update bheje, bot khud ko refresh karega
    await message.answer("🔄 Updating internal group list... please wait.")
    # Agar bot kisi group mein admin hai, wo yahan update ho jayega
    await message.answer(f"✅ Update complete! Currently active in {len(known_groups)} chats.")

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
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
async def add_channel_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    bot_info = await bot.get_me()
    url = f"https://t.me/{bot_info.username}?startgroup=true" # startgroup=true se group/channel dono mein option aayega
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ ADD TO CHANNEL/GROUP", url=url)]])
    await message.answer("Click below to add me to your channel or group:", reply_markup=kb)

@dp.message(Command("post"))
async def post_cmd(message: types.Message):
    if message.from_user.id != OWNER_ID: return
    
    if not known_groups:
        return await message.answer("⚠️ No chats found! Use /update or add me to some groups.")

    target = message.reply_to_message
    if target:
        if target.media_group_id:
            history = await bot.get_chat_history(chat_id=target.chat.id, limit=20)
            ids = sorted([m.message_id for m in history if m.media_group_id == target.media_group_id])
            for gid in known_groups:
                try: await bot(CopyMessages(chat_id=gid, from_chat_id=target.chat.id, message_ids=ids))
                except: pass
        else:
            for gid in known_groups:
                try: await bot.copy_message(gid, target.chat.id, target.message_id)
                except: pass
    else:
        text = message.text.replace('/post', '').strip()
        if text:
            for gid in known_groups:
                try: await bot.send_message(gid, text)
                except: pass

    await message.answer(f"✅ Broadcasted to {len(known_groups)} chats!")

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
