import logging
import requests
import os
import sys
import re

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web # يستخدم لتشغيل Webhook

# ===============================================
#              0. الإعدادات والثوابت والتهيئة
# ===============================================

# إعدادات Webhook والتوكن (يجب أن تكون مضبوطة في Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN") 
WEBHOOK_URL_BASE = os.getenv("WEBHOOK_URL") 
WEBHOOK_PATH = f'/{BOT_TOKEN}'

# إعدادات ثابتة
DEVELOPER_USER_ID = 1315011160 # تم تحويله إلى رقم لـ aiogram
CHANNEL_USERNAME = "@SuPeRx1"

TIKTOK_API = 'https://dev-broksuper.pantheonsite.io/api/e/mp3.php?url='
INSTAGRAM_API = 'https://dev-broksuper.pantheonsite.io/api/ink.php?url='
API_TIMEOUT = 25 # زيادة المهلة الزمنية للتحميل

# التحقق من المتغيرات
if not BOT_TOKEN or not WEBHOOK_URL_BASE:
    print("❌ خطأ: يجب تعيين متغيرات BOT_TOKEN و WEBHOOK_URL بشكل كامل!")
    sys.exit(1)

# إعداد التسجيل (Logging)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# ===============================================
#              1. تهيئة البوت والموزع (Dispatcher)
# ===============================================

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML) # استخدام HTML افتراضياً
dp = Dispatcher()

# ===============================================
#              2. دوال بناء الواجهة
# ===============================================

def build_main_keyboard():
    """بناء لوحة مفاتيح الأزرار الرئيسية."""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="تحميل تيك توك 🎶", callback_data="download_tiktok"),
        types.InlineKeyboardButton(text="تحميل إنستجرام 📸", callback_data="download_instagram")
    )
    builder.row(
        types.InlineKeyboardButton(text="المطور 👨‍💻", url=f"tg://user?id={DEVELOPER_USER_ID}")
    )
    return builder.as_markup()

# ===============================================
#              3. معالجة الأوامر الرئيسية (Command /start)
# ===============================================

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    """الرد على أمر /start باستخدام HTML لضمان الثبات."""
    
    first_name = message.from_user.first_name if message.from_user else "صديقنا"
    
    await message.answer(
        f"""
        <b>مرحباً بك {first_name}!</b> 👋
        
        أنا بوت التحميل الشامل. اختر المنصة التي تريد التحميل منها:
        * اختر من القائمة أدناه وأرسل <b>الرابط فوراً</b>.
        """,
        reply_markup=build_main_keyboard()
    )

# ===============================================
#              4. معالجة ضغطات الأزرار (Callbacks)
# ===============================================

@dp.callback_query(F.data == "download_tiktok")
async def process_tiktok_choice(callback: types.CallbackQuery, state: F.data):
    """معالجة اختيار تحميل تيك توك."""
    await callback.message.edit_text(
        "<b>🚀 أرسل رابط فيديو تيك توك الآن!</b>",
        parse_mode=ParseMode.HTML
    )
    # تسجيل الخطوة التالية (aiogram يستخدم طريقة مختلفة لانتظار الرسالة)
    dp.message.register(handle_tiktok_link, F.text, callback_data=callback.data)
    await callback.answer() # إغلاق إشعار الزر

@dp.callback_query(F.data == "download_instagram")
async def process_instagram_choice(callback: types.CallbackQuery, state: F.data):
    """معالجة اختيار تحميل إنستجرام."""
    await callback.message.edit_text(
        "<b>🚀 أرسل رابط فيديو إنستجرام الآن!</b>",
        parse_mode=ParseMode.HTML
    )
    # تسجيل الخطوة التالية
    dp.message.register(handle_instagram_link, F.text, callback_data=callback.data)
    await callback.answer() # إغلاق إشعار الزر


# ===============================================
#              5. دوال التحميل (Asynchronous Handling)
# ===============================================

async def handle_tiktok_link(message: types.Message):
    """تحميل الفيديو والصوت من رابط تيك توك."""
    user_url = message.text
    
    if user_url.startswith('/'):
        await message.answer("❌ تم إلغاء عملية التحميل. اضغط /start للعودة.")
        return

    if not re.match(r'https?://(?:www\.)?tiktok\.com/', user_url):
        await message.answer("<b>❌ الرابط غير صالح!</b> يرجى التأكد من إرسال رابط تيك توك صحيح.", parse_mode=ParseMode.HTML)
        await command_start_handler(message) 
        return

    loading_msg = await message.answer("<strong>⏳ جارٍ التحميل من تيك توك... يرجى الانتظار.</strong>", parse_mode=ParseMode.HTML)
    
    try:
        response = requests.get(f'{TIKTOK_API}{user_url}', timeout=API_TIMEOUT).json()
        video_url = response.get("video", {}).get("videoURL")
        audio_url = response.get("audioURL")
        
        await bot.delete_message(message.chat.id, loading_msg.message_id)
        
        caption_text = f"✅ تم التحميل بواسطة: {CHANNEL_USERNAME}" 
        
        if video_url:
            await message.answer_video(video_url, caption=f'<b>{caption_text}</b>', parse_mode=ParseMode.HTML)
        
        if audio_url:
            await message.answer_voice(audio_url, caption=f'<b>🎧 {caption_text}</b>', parse_mode=ParseMode.HTML)
            
        if not video_url and not audio_url:
             await message.answer("❌ لم يتم العثور على محتوى للتحميل. تأكد من أن الرابط عام.", parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logging.error(f"Error in TikTok: {e}")
        try: await bot.delete_message(message.chat.id, loading_msg.message_id) 
        except: pass
        await message.answer("❌ حدث خطأ أثناء التحميل. تأكد من الرابط أو حاول لاحقاً.", parse_mode=ParseMode.HTML)
        
    await message.answer("اضغط على الأمر /start للعودة إلى القائمة الرئيسية.", parse_mode=ParseMode.HTML)


async def handle_instagram_link(message: types.Message):
    """تحميل الفيديو/الصورة من رابط إنستجرام."""
    user_url = message.text
    loading_msg = None
    
    if user_url.startswith('/'):
        await message.answer("❌ تم إلغاء عملية التحميل. اضغط /start للعودة.")
        return

    if not re.match(r'https?://(?:www\.)?instagram\.com/', user_url):
        await message.answer("<b>❌ الرابط غير صالح!</b> يرجى التأكد من إرسال رابط إنستجرام صحيح.", parse_mode=ParseMode.HTML)
        await command_start_handler(message) 
        return

    loading_msg = await message.answer(f"""<strong>⏳ جارٍ التحميل من إنستجرام... يرجى الانتظار.</strong>""", parse_mode=ParseMode.HTML)
    
    try:
        response = requests.get(f"{INSTAGRAM_API}{user_url}", timeout=API_TIMEOUT).json()
        media_url = response.get('media')
        
        await bot.delete_message(message.chat.id, loading_msg.message_id) 
        
        caption_text = f"✅ تم التحميل بواسطة: {CHANNEL_USERNAME}" 

        if media_url:
            await message.answer_video(media_url, caption=f"<b>{caption_text}</b>", parse_mode=ParseMode.HTML)
        else:
            await message.answer("❌ لم يتم العثور على وسائط في الرابط. قد يكون الرابط خاصاً أو غير صحيح.", parse_mode=ParseMode.HTML)

    except Exception as e:
        logging.error(f"Error in Instagram: {e}")
        try: await bot.delete_message(message.chat.id, loading_msg.message_id) 
        except: pass 
        await message.answer("❌ حدث خطأ أثناء التحميل. تأكد من الرابط أو حاول لاحقاً.", parse_mode=ParseMode.HTML)
        
    await message.answer("اضغط على الأمر /start للعودة إلى القائمة الرئيسية.", parse_mode=ParseMode.HTML)

# ===============================================
#              6. تهيئة Webhook وبدء التشغيل
# ===============================================

async def on_startup(dispatcher, bot: Bot):
    """إعداد Webhook عند بدء تشغيل التطبيق."""
    logging.info("بدء تشغيل AioGram Webhook...")
    await bot.set_webhook(url=f"{WEBHOOK_URL_BASE}{WEBHOOK_PATH}")
    logging.info(f"✅ Webhook تم تعيينه إلى: {WEBHOOK_URL_BASE}{WEBHOOK_PATH}")


async def on_shutdown(dispatcher, bot: Bot):
    """تنظيف وإزالة Webhook عند إيقاف التشغيل."""
    logging.warning("إيقاف تشغيل AioGram...")
    await bot.delete_webhook()
    await dispatcher.storage.close()
    logging.warning("🛑 تم إزالة Webhook.")


def main():
    """تشغيل التطبيق الرئيسي."""
    try:
        # تهيئة تطبيق aiohttp كخادم ويب
        app = web.Application()
        web.run_app(
            app,
            host="0.0.0.0",
            port=int(os.environ.get('PORT', 8080)),
            on_startup=[on_startup],
            on_shutdown=[on_shutdown],
        )
        # ربط الـ Webhook مباشرة بالموزع (Dispatcher)
        app.router.add_post(WEBHOOK_PATH, lambda request: dp.web_hook(request))

    except Exception as e:
        logging.error(f"فشل تشغيل AioGram Webhook: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
