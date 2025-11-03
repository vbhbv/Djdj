import requests
import telebot
from telebot import types
from flask import Flask, request
import re
import os
import sys

# ===============================================
# 0. الإعدادات الأساسية
# ===============================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL_BASE = os.getenv("WEBHOOK_URL")  # مثال: https://web-production-4979.up.railway.app
WEBHOOK_URL_PATH = f"/{BOT_TOKEN}"  # Telegram سيرسل POST على هذا المسار
WEBHOOK_PORT = int(os.environ.get("PORT", 5000))

DEVELOPER_USER_ID = "1315011160"
CHANNEL_USERNAME = "@SuPeRx1"

TIKTOK_API = "https://dev-broksuper.pantheonsite.io/api/e/mp3.php?url="
INSTAGRAM_API = "https://dev-broksuper.pantheonsite.io/api/ink.php?url="

if not BOT_TOKEN or not WEBHOOK_URL_BASE:
    print("❌ خطأ: يجب تعيين BOT_TOKEN و WEBHOOK_URL!")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ===============================================
# 0.1 إدارة حالة المستخدم
# ===============================================
user_states = {}  # key=chat_id, value=platform ('tiktok' أو 'instagram')

# ===============================================
# 1. Webhook endpoint
# ===============================================

@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "!", 403

# ===============================================
# 2. /start
# ===============================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    first_name = message.from_user.first_name

    markup = types.InlineKeyboardMarkup(row_width=2)
    tt_btn = types.InlineKeyboardButton("تحميل تيك توك 🎶", callback_data="download_tiktok")
    ig_btn = types.InlineKeyboardButton("تحميل إنستجرام 📸", callback_data="download_instagram")
    dev_btn = types.InlineKeyboardButton("المطور 👨‍💻", url=f"tg://user?id={DEVELOPER_USER_ID}")
    markup.add(tt_btn, ig_btn, dev_btn)

    bot.send_message(
        message.chat.id,
        f"""
<b>مرحباً بك {first_name}!</b> 👋

أنا بوت التحميل الشامل. اختر المنصة التي تريد التحميل منها:
* اختر من القائمة أدناه وأرسل <b>الرابط فوراً</b>.
        """,
        parse_mode="HTML",
        reply_markup=markup,
    )

# ===============================================
# 3. التعامل مع Inline Buttons
# ===============================================

@bot.callback_query_handler(func=lambda call: call.data in ["download_tiktok", "download_instagram"])
def handle_download_choice(call):
    platform = "تيك توك" if call.data == "download_tiktok" else "إنستجرام"
    user_states[call.message.chat.id] = call.data
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"<b>🚀 أرسل رابط فيديو {platform} الآن!</b>",
        parse_mode="HTML",
    )

# ===============================================
# 4. معالجة الرابط بعد اختيار المنصة
# ===============================================

@bot.message_handler(func=lambda message: message.chat.id in user_states)
def process_link(message):
    platform_choice = user_states.pop(message.chat.id, None)
    if not platform_choice:
        bot.send_message(message.chat.id, "❌ حدث خطأ. حاول من جديد.", parse_mode="HTML")
        send_welcome(message)
        return

    if platform_choice == "download_tiktok":
        process_tiktok_link(message)
    elif platform_choice == "download_instagram":
        process_instagram_link(message)

# ===============================================
# 5. دوال التحميل
# ===============================================

def process_tiktok_link(message):
    user_url = message.text
    loading_msg = None
    if user_url.startswith("/"):
        bot.send_message(message.chat.id, "❌ تم إلغاء العملية.", parse_mode="HTML")
        send_welcome(message)
        return
    try:
        if not re.match(r"https?://(?:www\.)?tiktok\.com/", user_url):
            bot.send_message(message.chat.id, "<b>❌ الرابط غير صالح!</b>", parse_mode="HTML")
            send_welcome(message)
            return

        loading_msg = bot.send_message(message.chat.id, "<b>⏳ جارٍ التحميل من تيك توك...</b>", parse_mode="HTML")
        response = requests.get(f"{TIKTOK_API}{user_url}", timeout=20).json()
        video_url = response.get("video", {}).get("videoURL")
        audio_url = response.get("audioURL")
        bot.delete_message(message.chat.id, loading_msg.message_id)

        caption_text = f"✅ تم التحميل بواسطة: {CHANNEL_USERNAME}"
        if video_url:
            bot.send_video(message.chat.id, video_url, caption=f"<b>{caption_text}</b>", parse_mode="HTML")
        if audio_url:
            bot.send_voice(message.chat.id, audio_url, caption=f"<b>🎧 {caption_text}</b>", parse_mode="HTML")
        if not video_url and not audio_url:
            bot.send_message(message.chat.id, "❌ لم يتم العثور على محتوى.", parse_mode="HTML")
    except Exception as e:
        print(f"Error TikTok: {e}")
        if loading_msg:
            try: bot.delete_message(message.chat.id, loading_msg.message_id)
            except: pass
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء التحميل.", parse_mode="HTML")
    bot.send_message(message.chat.id, "اضغط على /start للعودة للقائمة الرئيسية.", parse_mode="HTML")

def process_instagram_link(message):
    user_url = message.text
    loading_msg = None
    if user_url.startswith("/"):
        bot.send_message(message.chat.id, "❌ تم إلغاء العملية.", parse_mode="HTML")
        send_welcome(message)
        return
    try:
        if not re.match(r"https?://(?:www\.)?instagram\.com/", user_url):
            bot.send_message(message.chat.id, "<b>❌ الرابط غير صالح!</b>", parse_mode="HTML")
            send_welcome(message)
            return

        loading_msg = bot.send_message(message.chat.id, "<b>⏳ جارٍ التحميل من إنستجرام...</b>", parse_mode="HTML")
        response = requests.get(f"{INSTAGRAM_API}{user_url}", timeout=20).json()
        media_url = response.get("media")
        bot.delete_message(message.chat.id, loading_msg.message_id)

        caption_text = f"✅ تم التحميل بواسطة: {CHANNEL_USERNAME}"
        if media_url:
            bot.send_video(message.chat.id, media_url, caption=f"<b>{caption_text}</b>", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ لم يتم العثور على وسائط.", parse_mode="HTML")
    except Exception as e:
        print(f"Error Instagram: {e}")
        if loading_msg:
            try: bot.delete_message(message.chat.id, loading_msg.message_id)
            except: pass
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء التحميل.", parse_mode="HTML")
    bot.send_message(message.chat.id, "اضغط على /start للعودة للقائمة الرئيسية.", parse_mode="HTML")

# ===============================================
# 6. تشغيل Webhook على Railway
# ===============================================

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
    print(f"✅ Webhook مضبوط: {WEBHOOK_URL_BASE + WEBHOOK_URL_PATH}")
    app.run(host="0.0.0.0", port=WEBHOOK_PORT)
