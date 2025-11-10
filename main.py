import telebot
from telebot import types
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

participant_count = 0

@bot.message_handler(commands=['start'])
def start_message(message):
    text = (
        "🎉 *Konkurs botiga xush kelibsiz!*\n\n"
        "Bu bot sizga kanalingizda reaksiya asosida *battle* o‘tkazishga yordam beradi.\n\n"
        "⚙️ *Qanday ishlaydi:*\n"
        "1️⃣ Botni kanalga admin sifatida qo‘shing.\n"
        "2️⃣ Kanalda `#batle` deb yozing.\n"
        "3️⃣ Bot avtomatik konkurs postini yuboradi.\n"
        "4️⃣ Foydalanuvchilar 'Qo'shilish' tugmasini bossalar, "
        "bot ularning ismini kanalga chiqadi.\n\n"
        "📜 *Postni tahrirlasangiz ham bot ishlayveradi.*\n"
        "⚠️ Nakrutka, spam yoki firibgarlik aniqlansa ban qilinadi!\n\n"
        "👇 Quyidagi tugma orqali botni kanalga qo‘shing:"
    )

    btn = types.InlineKeyboardMarkup()
    add_channel = types.InlineKeyboardButton(
        text="➕ KANALGA QO‘SHISH", url=f"https://t.me/{bot.get_me().username}?startchannel=true"
    )
    btn.add(add_channel)
    bot.send_message(message.chat.id, text, reply_markup=btn, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "#batle")
def start_battle(message):
    if message.chat.type != "supergroup" and message.chat.type != "channel":
        return bot.reply_to(message, "❗ Bu buyruq faqat kanal yoki supergruppalarda ishlaydi.")
    
    caption = (
        "🏆 #konkurs Boshlandi 🥳\n\n"
        "📋 *Konkurs shartlari:* Kanal postini o‘qib, qatnashing!\n"
        "🎁 *Sovg‘alar:* Admin tomonidan belgilanadi.\n\n"
        "📊 Ball tizimi:\n"
        "⭐ Reaksiya: 1 ball\n"
        "💫 Stars: 3 ball\n"
        "🚀 Boost: 5 ball\n\n"
        "📢 Battle o‘tkaziladigan kanal:\n"
        f"👉 @{message.chat.username}\n\n"
        "Nakrutka, spam — ban ❌"
    )

    join_btn = types.InlineKeyboardMarkup()
    join_btn.add(types.InlineKeyboardButton("🟢 Qo'shilish", callback_data="join_battle"))

    bot.send_message(message.chat.id, caption, reply_markup=join_btn, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "join_battle")
def join_battle(call):
    global participant_count
    participant_count += 1
    username = call.from_user.username or call.from_user.first_name
    text = (
        f"{participant_count} - @{username}\n"
        "Stars 3 Ball ⭐\n"
        "Reaksiya 1 Ball 🙊\n"
        "Boost 5 Ball 💫\n\n"
        "OMAD 🍀"
    )
    bot.send_message(call.message.chat.id, text)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "🚫 Siz admin emassiz.")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📢 Reklama yuborish", "📊 Statistika")
    bot.send_message(message.chat.id, "🔧 Admin paneliga xush kelibsiz!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish")
def send_ads(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "✍️ Reklama xabarini yuboring:")
        bot.register_next_step_handler(message, broadcast_message)

def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(ADMIN_ID, "✅ Reklama foydalanuvchilarga yuborildi.")

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    bot.send_message(message.chat.id, f"👥 Jami qatnashuvchilar: {participant_count} ta.")

bot.polling(non_stop=True)
