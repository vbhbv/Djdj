import requests
import telebot
from telebot import types
import re 
import os # لإدارة المتغيرات البيئية

# ===============================================
#              1. الإعدادات والثوابت
# ===============================================

# قراءة التوكن من المتغير البيئي (الأكثر أماناً للاستضافة)
BOT_TOKEN = os.getenv("BOT_TOKEN") 
DEVELOPER_USER_ID = "1315011160" # معرف المطور
CHANNEL_USERNAME = "@SuPeRx1" # اسم قناة البوت أو المطور (للكابشن)

# روابط الـ API الخارجية التي تعتمد عليها وظائف التحميل
TIKTOK_API = 'https://dev-broksuper.pantheonsite.io/api/e/mp3.php?url='
INSTAGRAM_API = 'https://dev-broksuper.pantheonsite.io/api/ink.php?url='

# التحقق من وجود التوكن
if not BOT_TOKEN:
    print("❌ خطأ: لم يتم تعيين المتغير البيئي BOT_TOKEN. يرجى ضبطه قبل التشغيل.")
    # يمكنك وضع التوكن مباشرة هنا للاختبار المحلي فقط، لكن يُنصح بتجنب ذلك للنشر.
    # BOT_TOKEN = "6876095262:AAEwbcucKYON9q7edyFidOrxAJeI8IfhJao" 
    # في حال النشر، يجب إيقاف التشغيل إذا كان التوكن مفقوداً
    # exit() 

try:
    bot = telebot.TeleBot(BOT_TOKEN)
except Exception as e:
    print(f"❌ فشل تهيئة البوت: {e}")
    # إذا كان الخطأ بسبب توكن غير صحيح (مثل الخطأ الذي ظهر في الصورة)، سيحدث هذا
    exit()

# ===============================================
#              2. معالجة الأوامر الرئيسية
# ===============================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    """يرسل رسالة الترحيب وقائمة الخيارات."""
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
        * اختر من القائمة أدناه وأرسل **الرابط فوراً**.
        """,
        parse_mode='markdown',
        reply_markup=markup
    )

# ===============================================
#              3. معالجة ضغطات الأزرار (Callback)
# ===============================================

@bot.callback_query_handler(func=lambda call: call.data in ['download_tiktok', 'download_instagram'])
def handle_download_choice(call):
    """يحدد نوع التحميل المطلوب ويسجل الدالة التالية للمعالجة."""
    
    platform = "تيك توك" if call.data == 'download_tiktok' else "إنستجرام"
    
    # تحرير رسالة الزر بدلاً من إرسال رسالة جديدة
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"""
        **🚀 أرسل رابط فيديو {platform} الآن!**
        """,
        parse_mode='markdown'
    )
    
    # تحديد الدالة التي ستتولى معالجة الرسالة التالية (الرابط)
    if call.data == 'download_tiktok':
        bot.register_next_step_handler(call.message, process_tiktok_link)
    elif call.data == 'download_instagram':
        bot.register_next_step_handler(call.message, process_instagram_link)
        
# ===============================================
#              4. دوال التحميل والتفاعل
# ===============================================

def process_tiktok_link(message):
    """تحميل الفيديو والصوت من رابط تيك توك."""
    user_url = message.text
    
    if not re.match(r'https?://(?:www\.)?tiktok\.com/', user_url):
        bot.send_message(message.chat.id, "**❌ الرابط غير صالح!** يرجى التأكد من إرسال رابط تيك توك صحيح.", parse_mode='markdown')
        # العودة إلى قائمة البداية بعد الخطأ
        send_welcome(message) 
        return
        
    loading_msg = bot.send_message(message.chat.id, "<strong>⏳ جارٍ التحميل من تيك توك... يرجى الانتظار.</strong>", parse_mode="html")
    
    try:
        response = requests.get(f'{TIKTOK_API}{user_url}', timeout=20).json()
        video_url = response.get("video", {}).get("videoURL")
        audio_url = response.get("audioURL")
        
        bot.delete_message(message.chat.id, loading_msg.message_id) # حذف رسالة الانتظار
        
        if video_url:
            bot.send_video(message.chat.id, video_url, caption=f'**✅ تم تحميل الفيديو بواسطة: {CHANNEL_USERNAME}**', parse_mode='markdown')
        
        if audio_url:
            bot.send_voice(message.chat.id, audio_url, caption=f'**🎧 تم تحميل الصوت بواسطة: {CHANNEL_USERNAME}**', parse_mode='markdown')
            
        if not video_url and not audio_url:
             bot.send_message(message.chat.id, "❌ لم يتم العثور على محتوى للتحميل. تأكد من أن الرابط عام.", parse_mode='markdown')
    
    except Exception as e:
        print(f"Error in TikTok: {e}")
        bot.delete_message(message.chat.id, loading_msg.message_id)
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء التحميل أو نفذ وقت الاتصال. تأكد من الرابط أو حاول لاحقاً.")
        
    # إعادة عرض خيارات البداية بعد الانتهاء
    send_welcome(message)

def process_instagram_link(message):
    """تحميل الفيديو/الصورة من رابط إنستجرام."""
    user_url = message.text
    
    if not re.match(r'https?://(?:www\.)?instagram\.com/', user_url):
        bot.send_message(message.chat.id, "**❌ الرابط غير صالح!** يرجى التأكد من إرسال رابط إنستجرام صحيح.", parse_mode='markdown')
        send_welcome(message)
        return

    loading_msg = bot.send_message(message.chat.id, f"""<strong>⏳ جارٍ التحميل من إنستجرام... يرجى الانتظار.</strong>""", parse_mode="html")
    
    try:
        response = requests.get(f"{INSTAGRAM_API}{user_url}", timeout=20).json()
        media_url = response.get('media')
        
        bot.delete_message(message.chat.id, loading_msg.message_id) # حذف رسالة الانتظار

        if media_url:
            # افتراض أن الرابط يعطي فيديو، يمكن التعديل لاحقاً للتحقق من نوع الملف إذا دعم الـ API ذلك
            bot.send_video(message.chat.id, media_url, caption=f"**✅ تم التحميل بواسطة: {CHANNEL_USERNAME}**", parse_mode='markdown')
        else:
            bot.send_message(message.chat.id, "❌ لم يتم العثور على وسائط في الرابط. قد يكون الرابط خاصاً أو غير صحيح.")

    except Exception as e:
        print(f"Error in Instagram: {e}")
        bot.delete_message(message.chat.id, loading_msg.message_id)
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء التحميل أو نفذ وقت الاتصال. تأكد من الرابط أو حاول لاحقاً.")
        
    # إعادة عرض خيارات البداية بعد الانتهاء
    send_welcome(message)

# ===============================================
#              5. التشغيل
# ===============================================

print('🎉 Bot is starting...')
bot.infinity_polling()
