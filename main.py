import telebot
from telebot import types
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

participants = []

@bot.message_handler(commands=['start'])
def start_message(message):
    text = (
        "🎉 <b>Konkurs botiga xush kelibsiz!</b>\n\n"
        "📋 Bu bot sizga kanal orqali konkurs (battle) o‘tkazishda yordam beradi.\n\n"
        "⚙️ <b>Qanday ishlaydi:</b>\n"
        "1️⃣ Botni kanalga admin sifatida qo‘shing.\n"
        "2️⃣ Kanalda <code>#batle</code> so‘zini yozing.\n"
        "3️⃣ Bot konkurs postini avtomatik joylaydi.\n"
        "4️⃣ Foydalanuvchilar 'Qatnashish' tugmasini bosganda ismlari chiqadi.\n\n"
        "🛠 Post tahrir qilinganda ham bot ishlayveradi.\n\n"
        "🚫 Nakrutka / spam / ban sababli ishtirokchi chiqariladi.\n\n"
        "👇 Quyidagi tugma orqali botni kanalga qo‘shing:"
    )
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton(
            "➕ KANALGA QO‘SHISH",
            url=f"https://t.me/{bot.get_me().username}?startchannel=true"
        )
    )
    bot.send_message(message.chat.id, text, reply_markup=btn)

@bot.message_handler(func=lambda m: m.chat.type in ["supergroup", "channel"] and "#batle" in m.text.lower())
def start_battle(message):
    caption = (
        "🏆 <b>KONKURS BOSHLANDI!</b>\n\n"
        "🎁 Sovg‘alar va shartlarni admin tahrir qilishi mumkin.\n\n"
        "⚠️ Nakrutka yoki spam aniqlansa — ban!\n\n"
        "👇 Quyidagi tugma orqali qatnashing:"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🟢 Qatnashish", callback_data="join"))
    bot.send_message(message.chat.id, caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "join")
def join_user(call):
    user = call.from_user
    username = f"@{user.username}" if user.username else user.first_name

    if username not in participants:
        participants.append(username)
        count = len(participants)
        msg = f"{count} - {username}\nOMAD 🍀"
        bot.send_message(call.message.chat.id, msg)
    else:
        bot.answer_callback_query(call.id, "Siz allaqachon qatnashgansiz ✅", show_alert=True)

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
        bot.send_message(message.chat.id, "✍️ Reklama matnini yuboring:")
        bot.register_next_step_handler(message, broadcast_message)

def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(ADMIN_ID, "✅ Reklama yuborish faqat foydalanuvchilar uchun yo‘lga qo‘yilgan.")

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    bot.send_message(message.chat.id, f"👥 Qatnashuvchilar soni: {len(participants)} ta")

bot.polling(non_stop=True)
