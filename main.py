import requests
import telebot
from telebot import types
from flask import Flask, request # لعمل Webhook
import re 
import os 
import sys

# ===============================================
#              0. دالة مساعدة لتأمين النصوص (لـ MarkdownV2 في الكابشن فقط)
# ===============================================
def escape_markdown_v2(text):
    """تؤمن النص ليتناسب مع تنسيق MarkdownV2 بتأمين الرموز الخاصة."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)

# ===============================================
#              1. الإعدادات والثوابت والتهيئة
# ===============================================

# قراءة المتغيرات البيئية الضرورية
BOT_TOKEN = os.getenv("BOT_TOKEN") 
WEBHOOK_PORT = int(os.environ.get('PORT', 5000))
WEBHOOK_URL_BASE = os.getenv("WEBHOOK_URL") 
WEBHOOK_URL_PATH = "/{}".format(BOT_TOKEN)

DEVELOPER_USER_ID = "1315011160"
CHANNEL_USERNAME = "@SuPeRx1"

TIKTOK_API = 'https://dev-broksuper.pantheonsite.io/api/e/mp3.php?url='
INSTAGRAM_API = 'https://dev-broksuper.pantheonsite.io/api/ink.php?url='

if not BOT_TOKEN or not WEBHOOK_URL_BASE:
    print("❌ خطأ: يجب تعيين متغيرات BOT_TOKEN و WEBHOOK_URL!")
    sys.exit(1) 

try:
    bot = telebot.TeleBot(BOT_TOKEN)
    app = Flask(__name__) 
except Exception as e:
    print(f"❌ فشل تهيئة البوت/Flask. الخطأ: {e}")
    sys.exit(1)

# ===============================================
#              2. نقاط وصول Webhook
# ===============================================

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    """نقطة النهاية التي يستقبل منها البوت تحديثات تيليجرام."""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '!', 200
    else:
        return '!', 403

# ===============================================
#              3. معالجة الأوامر الرئيسية (تم التعديل لـ HTML)
# ===============================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    """يرسل رسالة الترحيب وقائمة الخيارات باستخدام HTML لضمان الثبات."""
    
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
        parse_mode='HTML', # *** تم التعديل إلى HTML ***
        reply_markup=markup
    )

# ===============================================
#              4. معالجة الـ Callback و الدوال (مع MarkdownV2 في الأماكن الآمنة)
# ===============================================

@bot.callback_query_handler(func=lambda call: call.data in ['download_tiktok', 'download_instagram'])
def handle_download_choice(call):
    platform = "تيك توك" if call.data == 'download_tiktok' else "إنستجرام"
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=fr"""
        **🚀 أرسل رابط فيديو {platform} الآن\!**
        """,
        parse_mode='MarkdownV2'
    )
    if call.data == 'download_tiktok':
        bot.register_next_step_handler(call.message, process_tiktok_link)
    elif call.data == 'download_instagram':
        bot.register_next_step_handler(call.message, process_instagram_link)
        
def process_tiktok_link(message):
    """تحميل الفيديو والصوت من رابط تيك توك."""
    user_url = message.text
    loading_msg = None
    
    # تحقق من إلغاء العملية
    if user_url.startswith('/'):
        bot.send_message(message.chat.id, r"❌ تم إلغاء عملية التحميل\. يرجى البدء من جديد واختيار المنصة أولاً\.", parse_mode='MarkdownV2')
        send_welcome(message) 
        return
        
    try:
        if not re.match(r'https?://(?:www\.)?tiktok\.com/', user_url):
            bot.send_message(message.chat.id, r"**❌ الرابط غير صالح\!** يرجى التأكد من إرسال رابط تيك توك صحيح\.", parse_mode='MarkdownV2')
            send_welcome(message) 
            return
            
        loading_msg = bot.send_message(message.chat.id, "<strong>⏳ جارٍ التحميل من تيك توك... يرجى الانتظار.</strong>", parse_mode="html")
        
        response = requests.get(f'{TIKTOK_API}{user_url}', timeout=20).json()
        video_url = response.get("video", {}).get("videoURL")
        audio_url = response.get("audioURL")
        
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        if video_url:
            bot.send_video(message.chat.id, video_url, caption=f'**✅ تم تحميل الفيديو بواسطة: {CHANNEL_USERNAME}**', parse_mode='MarkdownV2')
        
        if audio_url:
            bot.send_voice(message.chat.id, audio_url, caption=f'**🎧 تم تحميل الصوت بواسطة: {CHANNEL_USERNAME}**', parse_mode='MarkdownV2')
            
        if not video_url and not audio_url:
             bot.send_message(message.chat.id, r"❌ لم يتم العثور على محتوى للتحميل\. تأكد من أن الرابط عام\.", parse_mode='MarkdownV2')
    
    except Exception as e:
        print(f"Error in TikTok: {e}")
        if loading_msg:
             try: bot.delete_message(message.chat.id, loading_msg.message_id) 
             except: pass 
        bot.send_message(message.chat.id, r"❌ حدث خطأ أثناء التحميل\. تأكد من الرابط أو حاول لاحقاً\.", parse_mode='MarkdownV2')
        
    bot.send_message(message.chat.id, r"اضغط على الأمر /start للعودة إلى القائمة الرئيسية\.", parse_mode='MarkdownV2')


def process_instagram_link(message):
    """تحميل الفيديو/الصورة من رابط إنستجرام."""
    user_url = message.text
    loading_msg = None
    if user_url.startswith('/'):
        bot.send_message(message.chat.id, r"❌ تم إلغاء عملية التحميل\. يرجى البدء من جديد واختيار المنصة أولاً\.", parse_mode='MarkdownV2')
        send_welcome(message) 
        return
        
    try:
        if not re.match(r'https?://(?:www\.)?instagram\.com/', user_url):
            bot.send_message(message.chat.id, r"**❌ الرابط غير صالح\!** يرجى التأكد من إرسال رابط إنستجرام صحيح\.", parse_mode='MarkdownV2')
            send_welcome(message)
            return

        loading_msg = bot.send_message(message.chat.id, f"""<strong>⏳ جارٍ التحميل من إنستجرام... يرجى الانتظار.</strong>""", parse_mode="html")
        
        response = requests.get(f"{INSTAGRAM_API}{user_url}", timeout=20).json()
        media_url = response.get('media')
        
        bot.delete_message(message.chat.id, loading_msg.message_id) 

        if media_url:
            bot.send_video(message.chat.id, media_url, caption=f"**✅ تم التحميل بواسطة: {CHANNEL_USERNAME}**", parse_mode='MarkdownV2')
        else:
            bot.send_message(message.chat.id, r"❌ لم يتم العثور على وسائط في الرابط\. قد يكون الرابط خاصاً أو غير صحيح\.", parse_mode='MarkdownV2')

    except Exception as e:
        print(f"Error in Instagram: {e}")
        if loading_msg:
             try: bot.delete_message(message.chat.id, loading_msg.message_id) 
             except: pass 
        bot.send_message(message.chat.id, r"❌ حدث خطأ أثناء التحميل\. تأكد من الرابط أو حاول لاحقاً\.", parse_mode='MarkdownV2')
        
    bot.send_message(message.chat.id, r"اضغط على الأمر /start للعودة إلى القائمة الرئيسية\.", parse_mode='MarkdownV2')


# ===============================================
#              5. تشغيل Webhook
# ===============================================

if __name__ == '__main__':
    # إزالة أي Webhook قديم
    bot.remove_webhook()
    
    # إعداد Webhook الجديد
    bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
    
    # بدء تشغيل Flask للسماح بـ Telegram بإرسال التحديثات إلى نقطة الوصول
    print(f'✅ البوت يعمل الآن في وضع Webhook على المنفذ: {WEBHOOK_PORT}...')
    app.run(host='0.0.0.0', port=WEBHOOK_PORT)
