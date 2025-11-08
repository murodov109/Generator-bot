import telebot
import requests
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
bot = telebot.TeleBot(BOT_TOKEN)

user_data = defaultdict(lambda: {
    "count": 0, 
    "coins": 0, 
    "photo": None, 
    "referrals": 0,
    "last_reset": datetime.now(),
    "invited_by": None
})
channels = ["@your_channel"]

def reset_limits():
    for user in user_data:
        if datetime.now() - user_data[user]["last_reset"] > timedelta(days=1):
            user_data[user]["count"] = 0
            user_data[user]["last_reset"] = datetime.now()

@bot.message_handler(commands=["start"])
def start(message):
    reset_limits()
    user_id = message.from_user.id

    args = message.text.split()
    if len(args) > 1:
        inviter_id = int(args[1])
        if inviter_id != user_id and inviter_id in user_data and user_data[user_id]["invited_by"] is None:
            user_data[user_id]["invited_by"] = inviter_id
            user_data[inviter_id]["coins"] += 100
            user_data[inviter_id]["referrals"] += 1
            bot.send_message(inviter_id, "🎉 Sizga 100 coin qo‘shildi! Yangi referal qo‘shildi.")

    if user_id == ADMIN_ID:
        admin_menu(message)
    else:
        user_menu(message)

def admin_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Reklama yuborish", "➕ Kanal qo‘shish", "➖ Kanal o‘chirish")
    bot.send_message(message.chat.id, "👑 Admin paneliga xush kelibsiz!", reply_markup=markup)

def user_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎥 Video yaratish", "💰 Hisobim", "👥 Referallar", "💡 Yordam")
    bot.send_message(message.chat.id, "👋 Salom! Quyidagi menyudan tanlang:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def statistika(message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = len(user_data)
    total_videos = sum(u["count"] for u in user_data.values())
    total_coins = sum(u["coins"] for u in user_data.values())
    bot.send_message(message.chat.id, f"📈 Foydalanuvchilar: {total_users}\n🎬 Videolar: {total_videos}\n💰 Coinlar: {total_coins}")

@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish")
def reklama_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "✍️ Reklama matnini yuboring:")
    bot.register_next_step_handler(message, reklama_yuborish)

def reklama_yuborish(message):
    if message.from_user.id != ADMIN_ID:
        return
    sent = 0
    for uid in user_data:
        try:
            bot.send_message(uid, message.text)
            sent += 1
        except:
            pass
    bot.send_message(message.chat.id, f"✅ {sent} ta foydalanuvchiga reklama yuborildi.")

@bot.message_handler(func=lambda m: m.text == "🎥 Video yaratish")
def video_start(message):
    user_id = message.from_user.id
    reset_limits()
    limit = 3 + (user_data[user_id]["coins"] // 150)
    if user_id != ADMIN_ID and user_data[user_id]["count"] >= limit:
        bot.send_message(user_id, "🚫 Limit tugagan. Referal orqali coin to‘plang yoki ertaga urinib ko‘ring.")
        return
    bot.send_message(user_id, "📸 Rasm yuboring:")
    bot.register_next_step_handler(message, rasm_qabul)

def rasm_qabul(message):
    if not message.photo:
        bot.send_message(message.chat.id, "⚠️ Iltimos, rasm yuboring.")
        return
    user_id = message.from_user.id
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    user_data[user_id]["photo"] = file_url
    bot.send_message(user_id, "✍️ Endi tavsif yozing:")
    bot.register_next_step_handler(message, prompt_qabul)

def prompt_qabul(message):
    user_id = message.from_user.id
    if not user_data[user_id]["photo"]:
        bot.send_message(user_id, "⚠️ Avval rasm yuboring.")
        return
    prompt = message.text
    bot.send_message(user_id, "🎨 AI video tayyorlanmoqda, biroz kuting...")
    try:
        effect = random.choice(["zoom", "move", "wave", "float"])
        api = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
        img = requests.get(api).content
        bot.send_video(user_id, img, caption=f"🎬 {prompt}\n✨ Effekt: {effect}")
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Xatolik: {e}")
    if user_id != ADMIN_ID:
        user_data[user_id]["count"] += 1
    user_data[user_id]["photo"] = None

@bot.message_handler(func=lambda m: m.text == "💰 Hisobim")
def hisobim(message):
    user = user_data[message.from_user.id]
    limit = 3 + (user["coins"] // 150)
    bot.send_message(message.chat.id, f"💰 Coinlar: {user['coins']}\n🎞 Bugungi video: {user['count']}/{limit}")

@bot.message_handler(func=lambda m: m.text == "👥 Referallar")
def referallar(message):
    user = user_data[message.from_user.id]
    ref_link = f"https://t.me/{bot.get_me().username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"👥 Referallar: {user['referrals']}\n💰 1 referal = 100 coin\n🔗 Havola: {ref_link}")

@bot.message_handler(func=lambda m: m.text == "💡 Yordam")
def yordam(message):
    bot.send_message(message.chat.id, "📘 Botdan foydalanish uchun:\n1. 🎥 Rasm yuboring\n2. Tavsif yozing\n3. AI video tayyorlaydi\n\n💰 Referal orqali coin to‘plang!")

bot.polling(none_stop=True)
