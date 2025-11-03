import requests
import telebot
from telebot import types
import re # لإضافة التحقق من الروابط

# **1. التهيئة والثوابت (Configuration)**
BOT_TOKEN = "ضع_التوكن_الخاص_بك_هنا" # يجب استبداله بتوكن البوت
DEVELOPER_USER_ID = "1315011160" # معرف المطور
CHANNEL_USERNAME = "@SuPeRx1" # اسم قناة البوت أو المطور
TIKTOK_API = 'https://dev-broksuper.pantheonsite.io/api/e/mp3.php?url='
INSTAGRAM_API = 'https://dev-broksuper.pantheonsite.io/api/ink.php?url='

bot = telebot.TeleBot(BOT_TOKEN)

# **2. قائمة التشغيل الرئيسية (Start Command)**
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    tt_btn = types.InlineKeyboardButton("تحميل تيك توك 🎶", callback_data="download_tiktok")
    ig_btn = types.InlineKeyboardButton("تحميل إنستجرام 📸", callback_data="download_instagram")
    dev_btn = types.InlineKeyboardButton("المطور 👨‍💻", url=f"tg://user?id={DEVELOPER_USER_ID}")
    
    markup.add(tt_btn, ig_btn, dev_btn)
    
    bot.send_message(
        message.chat.id,
        f"""
        **مرحبا بك {message.from_user.first_name}!** 👋
        
        أنا بوت التحميل الشامل. اختر المنصة التي تريد التحميل منها:
        * اختر من القائمة أدناه وأرسل الرابط فوراً.
        """,
        parse_mode='markdown',
        reply_markup=markup
    )

# **3. معالجة الـ Callback (التفاعل مع الأزرار)**
@bot.callback_query_handler(func=lambda call: call.data in ['download_tiktok', 'download_instagram'])
def handle_download_choice(call):
    # قم بتعديل رسالة الزر لتجنب إرسال رسالة جديدة
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="""
        **🚀 أرسل رابط الفيديو الآن!** سيتم تحديد نوع التحميل تلقائياً بناءً على اختيارك السابق.
        """,
        parse_mode='markdown'
    )
    
    # تحديد الخطوة التالية (Next Step) لتحديد نوع التحميل
    if call.data == 'download_tiktok':
        bot.register_next_step_handler(call.message, process_tiktok_link)
    elif call.data == 'download_instagram':
        bot.register_next_step_handler(call.message, process_instagram_link)
        
# **4. دالة معالجة روابط تيك توك**
def process_tiktok_link(message):
    user_url = message.text
    
    if not re.match(r'https?://(?:www\.)?tiktok\.com/', user_url):
        bot.send_message(message.chat.id, "**❌ الرابط غير صالح!** يرجى التأكد من إرسال رابط تيك توك صحيح.", parse_mode='markdown')
        return
        
    bot.send_message(message.chat.id, "<strong>⏳ جارٍ التحميل من تيك توك... يرجى الانتظار.</strong>", parse_mode="html")
    
    try:
        response = requests.get(f'{TIKTOK_API}{user_url}').json()
        video_url = response.get("video", {}).get("videoURL")
        audio_url = response.get("audioURL")
        
        if video_url:
            bot.send_video(message.chat.id, video_url, caption=f'**✅ تم تحميل الفيديو بواسطة: {CHANNEL_USERNAME}**', parse_mode='markdown')
        
        if audio_url:
            bot.send_voice(message.chat.id, audio_url, caption=f'**🎧 تم تحميل الصوت بواسطة: {CHANNEL_USERNAME}**', parse_mode='markdown')
            
        if not video_url and not audio_url:
             bot.send_message(message.chat.id, "❌ لم يتم العثور على محتوى للتحميل. تأكد من أن الرابط عام.", parse_mode='markdown')
    
    except Exception as e:
        print(f"Error in TikTok: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء التحميل. تأكد من الرابط أو حاول لاحقاً.")

# **5. دالة معالجة روابط إنستجرام**
def process_instagram_link(message):
    user_url = message.text
    
    if not re.match(r'https?://(?:www\.)?instagram\.com/', user_url):
        bot.send_message(message.chat.id, "**❌ الرابط غير صالح!** يرجى التأكد من إرسال رابط إنستجرام صحيح.", parse_mode='markdown')
        return

    bot.send_message(message.chat.id, f"""<strong>⏳ جارٍ التحميل من إنستجرام... يرجى الانتظار.</strong>""", parse_mode="html")
    
    try:
        response = requests.get(f"{INSTAGRAM_API}{user_url}").json()
        media_url = response.get('media')
        
        if media_url:
            # يمكن أن تكون ميديا واحدة فقط في الردود التي تعتمد على هذا الـ API
            # يمكن تطوير هذه الجزئية لاحقاً لدعم البومات الصور والفيديوهات المتعددة.
            bot.send_video(message.chat.id, media_url, caption=f"**✅ تم التحميل بواسطة: {CHANNEL_USERNAME}**", parse_mode='markdown')
        else:
            bot.send_message(message.chat.id, "❌ لم يتم العثور على وسائط في الرابط. قد يكون الرابط خاصاً أو غير صحيح.")

    except Exception as e:
        print(f"Error in Instagram: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء التحميل. تأكد من الرابط أو حاول لاحقاً.")

# **6. التشغيل الدائم (Polling)**
print('Bot is running...')
bot.infinity_polling()

