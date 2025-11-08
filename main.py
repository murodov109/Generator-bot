import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from collections import defaultdict
import requests

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
AI_URL = "https://api.polinations.ai/video"  # Free AI service
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

user_data = defaultdict(lambda: {"count": 0, "coins": 0, "ref": None, "last_reset": datetime.now()})
channels = []

def reset_limits():
    for user in user_data:
        if datetime.now() - user_data[user]["last_reset"] > timedelta(days=1):
            user_data[user]["count"] = 0
            user_data[user]["last_reset"] = datetime.now()

def generate_ref_link(user_id):
    return f"https://t.me/{bot.username}?start={user_id}"

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    reset_limits()
    user_id = msg.from_user.id
    args = msg.get_args()

    if args and args.isdigit() and int(args) != user_id:
        if user_data[user_id]["ref"] is None:
            referrer = int(args)
            user_data[user_id]["ref"] = referrer
            user_data[referrer]["coins"] += 100
            await bot.send_message(referrer, f"🎉 Sizning referalingiz yangi foydalanuvchi qo‘shdi!\n💰 100 coin qo‘shildi.")

    if user_id == ADMIN_ID:
        btns = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📊 Statistika", callback_data="stats"),
            InlineKeyboardButton("📢 Reklama", callback_data="send_ads"),
            InlineKeyboardButton("🔗 Kanal sozlash", callback_data="set_channel")
        )
        await msg.answer("👋 Salom, admin panelga xush kelibsiz!", reply_markup=btns)
    else:
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🪄 Rasm jonlantirish", callback_data="animate"),
            InlineKeyboardButton("👤 Hisobim", callback_data="account"),
            InlineKeyboardButton("🎁 Referal", callback_data="ref")
        )
        await msg.answer("👋 Salom! Men rasmni jonlantiruvchi botman.\nRasm yuboring va natijani oling!", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "account")
async def account_info(call: types.CallbackQuery):
    data = user_data[call.from_user.id]
    await call.message.answer(
        f"📊 Sizning hisobingiz:\n\n💰 Coin: {data['coins']}\n🎞️ Bugungi limit: {data['count']}/3\n\nReferal link:\n{generate_ref_link(call.from_user.id)}"
    )

@dp.callback_query_handler(lambda c: c.data == "ref")
async def ref_system(call: types.CallbackQuery):
    link = generate_ref_link(call.from_user.id)
    await call.message.answer(f"🎁 Do‘stlaringizni taklif qiling va har bir faol foydalanuvchi uchun 100 coin oling!\n\n🔗 Sizning havolangiz:\n{link}")

@dp.callback_query_handler(lambda c: c.data == "animate")
async def ask_photo(call: types.CallbackQuery):
    await call.message.answer("🖼️ Rasm yuboring (jpg/png)...")

@dp.message_handler(content_types=["photo"])
async def handle_photo(msg: types.Message):
    user_id = msg.from_user.id
    if user_id != ADMIN_ID and user_data[user_id]["count"] >= 3 and user_data[user_id]["coins"] < 150:
        await msg.answer("🚫 Sizning bugungi limingiz tugagan va yetarli coin yo‘q.")
        return

    await msg.answer("✍️ Endi rasm uchun prompt (tasvir tavsifi) kiriting:")
    user_data[user_id]["photo"] = msg.photo[-1].file_id

@dp.message_handler(lambda m: m.text and "photo" in user_data[m.from_user.id])
async def handle_prompt(msg: types.Message):
    user_id = msg.from_user.id
    photo_id = user_data[user_id]["photo"]
    prompt = msg.text
    del user_data[user_id]["photo"]

    await msg.answer("⏳ AI orqali video tayyorlanmoqda...")

    # Fake API simulation (Polinations AI video)
    response = requests.get(f"https://image.pollinations.ai/prompt/{prompt}")
    if response.status_code == 200:
        await msg.answer_video(response.url, caption=f"🎬 Natija: {prompt}")
    else:
        await msg.answer("⚠️ AI bilan aloqa vaqtida xatolik yuz berdi. Keyinroq urinib ko‘ring.")

    if user_id != ADMIN_ID:
        user_data[user_id]["count"] += 1
        if user_data[user_id]["count"] > 3:
            user_data[user_id]["coins"] -= 150

@dp.callback_query_handler(lambda c: c.data == "stats" and c.from_user.id == ADMIN_ID)
async def show_stats(call: types.CallbackQuery):
    total_users = len(user_data)
    total_refs = sum(1 for u in user_data.values() if u["ref"])
    await call.message.answer(f"📈 Foydalanuvchilar: {total_users}\n👥 Referallar: {total_refs}")

@dp.callback_query_handler(lambda c: c.data == "send_ads" and c.from_user.id == ADMIN_ID)
async def send_ads(call: types.CallbackQuery):
    await call.message.answer("✍️ Reklama matnini kiriting:")
    @dp.message_handler()
    async def get_ad(msg: types.Message):
        for user in user_data:
            try:
                await bot.send_message(user, msg.text)
            except:
                pass
        await msg.answer("✅ Reklama yuborildi.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
