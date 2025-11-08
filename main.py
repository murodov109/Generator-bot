import telebot
import sqlite3
import os
import requests
import datetime
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip().isdigit()]

bot = telebot.TeleBot(BOT_TOKEN)
HF_MODEL_URL = "https://api-inference.huggingface.co/models/guoyww/animatediff-motion-lora"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

if not os.path.exists("database.db"):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        coins INTEGER DEFAULT 0,
        daily_used INTEGER DEFAULT 0,
        last_reset TEXT,
        referred_by INTEGER
    )
    """)
    c.execute("""
    CREATE TABLE channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link TEXT
    )
    """)
    conn.commit()
    conn.close()

user_data = {}

def db():
    return sqlite3.connect("database.db")

def reset_daily_limit():
    conn = db()
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("UPDATE users SET daily_used = 0, last_reset = ? WHERE last_reset != ?", (today, today))
    conn.commit()
    conn.close()

def check_subscription(user_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT link FROM channels")
    channels = c.fetchall()
    conn.close()
    if not channels:
        return True
    for ch in channels:
        username = ch[0].replace("https://t.me/", "").replace("@", "")
        try:
            status = bot.get_chat_member(username, user_id)
            if status.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    reset_daily_limit()
    conn = db()
    c = conn.cursor()
    ref_id = None
    if len(message.text.split()) > 1:
        try:
            ref_id = int(message.text.split()[1])
        except:
            pass
    c.execute("SELECT * FROM users WHERE user_id=?", (message.chat.id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, coins, daily_used, last_reset, referred_by) VALUES (?, ?, ?, ?, ?, ?)",
                  (message.chat.id, message.from_user.username, 0, 0, datetime.date.today().isoformat(), ref_id))
        if ref_id:
            c.execute("UPDATE users SET coins = coins + 100 WHERE user_id=?", (ref_id,))
    conn.commit()
    conn.close()

    if not check_subscription(message.chat.id):
        conn = db()
        c = conn.cursor()
        c.execute("SELECT link FROM channels")
        chs = c.fetchall()
        conn.close()
        text = "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:\n\n"
        for ch in chs:
            text += f"👉 {ch[0]}\n"
        text += "\n✅ Obuna bo‘lgach, /start buyrug‘ini qayta yuboring."
        bot.reply_to(message, text)
        return

    bot.reply_to(message, "🎬 Salom! Menga rasm yuboring.\n\n🪙 Har kuni 3 ta bepul jonlantirish imkoniyatingiz bor.\nReferal orqali do‘stlaringizni chaqiring va coin oling!\n\n💰 /hisob — balansni ko‘rish\n⚙️ /panel — adminlar uchun menyu")

@bot.message_handler(commands=['hisob'])
def hisob(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT coins, daily_used FROM users WHERE user_id=?", (message.chat.id,))
    u = c.fetchone()
    conn.close()
    if not u:
        bot.reply_to(message, "Avval /start buyrug‘ini yuboring.")
        return
    coins, used = u
    ref_link = f"https://t.me/{bot.get_me().username}?start={message.chat.id}"
    if message.chat.id in ADMINS:
        bot.reply_to(message, f"👑 Siz adminsiz.\nCheksiz video yaratish ruxsatiga egasiz.\n\n💰 Coinlar: {coins}\n🎨 Bugungi limit: ♾\n🤝 Referal link:\n{ref_link}")
    else:
        bot.reply_to(message, f"💰 Coinlar: {coins}\n🎨 Bugungi limit: {used}/3\n🤝 Referal link:\n{ref_link}")

@bot.message_handler(commands=['panel'])
def panel(message):
    if message.chat.id not in ADMINS:
        return bot.reply_to(message, "❌ Siz admin emassiz.")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Reklama yuborish")
    markup.add("➕ Kanal qo‘shish", "➖ Kanal o‘chirish")
    bot.send_message(message.chat.id, "⚙️ Admin panel:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.chat.id in ADMINS)
def statistika(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    all_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE last_reset=?", (datetime.date.today().isoformat(),))
    today_users = c.fetchone()[0]
    conn.close()
    bot.reply_to(message, f"📈 Foydalanuvchilar: {all_users}\n👥 Bugun faol: {today_users}")

@bot.message_handler(func=lambda m: m.text == "➕ Kanal qo‘shish" and m.chat.id in ADMINS)
def add_channel(message):
    msg = bot.reply_to(message, "🔗 Kanal havolasini yuboring (masalan: https://t.me/yourchannel)")
    bot.register_next_step_handler(msg, save_channel)

def save_channel(message):
    link = message.text.strip()
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO channels (link) VALUES (?)", (link,))
    conn.commit()
    conn.close()
    bot.reply_to(message, "✅ Kanal muvaffaqiyatli qo‘shildi.")

@bot.message_handler(func=lambda m: m.text == "➖ Kanal o‘chirish" and m.chat.id in ADMINS)
def delete_channel(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, link FROM channels")
    chs = c.fetchall()
    conn.close()
    if not chs:
        bot.reply_to(message, "⚠️ Hozircha kanal yo‘q.")
        return
    text = "🗑 O‘chirmoqchi bo‘lgan kanal raqamini yuboring:\n\n"
    for ch in chs:
        text += f"{ch[0]}. {ch[1]}\n"
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, remove_channel)

def remove_channel(message):
    try:
        idd = int(message.text)
        conn = db()
        c = conn.cursor()
        c.execute("DELETE FROM channels WHERE id=?", (idd,))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ Kanal o‘chirildi.")
    except:
        bot.reply_to(message, "❌ Xatolik yuz berdi.")

@bot.message_handler(func=lambda m: m.text == "📢 Reklama yuborish" and m.chat.id in ADMINS)
def reklama(message):
    msg = bot.reply_to(message, "✏️ Reklama matnini yuboring:")
    bot.register_next_step_handler(msg, send_reklama)

def send_reklama(message):
    text = message.text
    conn = db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    sent = 0
    for u in users:
        try:
            bot.send_message(u[0], text)
            sent += 1
        except:
            pass
    bot.reply_to(message, f"📨 Reklama {sent} foydalanuvchiga yuborildi.")

@bot.message_handler(content_types=['photo'])
def get_photo(message):
    reset_daily_limit()
    conn = db()
    c = conn.cursor()
    c.execute("SELECT coins, daily_used FROM users WHERE user_id=?", (message.chat.id,))
    user = c.fetchone()
    conn.close()
    if not user:
        bot.reply_to(message, "Avval /start buyrug‘ini yuboring.")
        return
    coins, used = user
    if message.chat.id not in ADMINS:
        if used >= 3 and coins < 150:
            bot.reply_to(message, "⚠️ Limit tugadi va coin yetarli emas.\nDo‘stingizni taklif qiling va 100 coin oling!")
            return
    file_info = bot.get_file(message.photo[-1].file_id)
    file = bot.download_file(file_info.file_path)
    path = f"temp_{message.chat.id}.jpg"
    with open(path, "wb") as f:
        f.write(file)
    user_data[message.chat.id] = {"image": path}
    bot.reply_to(message, "Endi prompt kiriting ✏️ (masalan: walking through a forest)")

@bot.message_handler(func=lambda msg: msg.chat.id in user_data)
def prompt_handler(message):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT coins, daily_used FROM users WHERE user_id=?", (message.chat.id,))
    user = c.fetchone()
    conn.close()
    if not user:
        bot.reply_to(message, "Avval /start buyrug‘ini yuboring.")
        return
    coins, used = user
    image_path = user_data[message.chat.id]["image"]
    prompt = message.text
    bot.reply_to(message, "⏳ Rasm jonlantirilmoqda, biroz kuting...")

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    response = requests.post(HF_MODEL_URL, headers=headers, files={"image": image_bytes}, data={"inputs": prompt})

    if response.status_code == 200:
        video_path = f"video_{message.chat.id}.mp4"
        with open(video_path, "wb") as f:
            f.write(response.content)
        bot.send_video(message.chat.id, open(video_path, "rb"), caption="🎥 Rasm harakatlantirildi!")
        os.remove(video_path)
        os.remove(image_path)

        if message.chat.id not in ADMINS:
            if used < 3:
                used += 1
            else:
                coins -= 150
            conn = db()
            c = conn.cursor()
            c.execute("UPDATE users SET coins=?, daily_used=? WHERE user_id=?", (coins, used, message.chat.id))
            conn.commit()
            conn.close()
    else:
        bot.reply_to(message, "⚠️ AI bilan aloqa vaqtida xatolik yuz berdi. Keyinroq urinib ko‘ring.")
        os.remove(image_path)

    del user_data[message.chat.id]

bot.infinity_polling()
