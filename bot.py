import os
import telebot
import google.generativeai as genai
from PIL import Image
import io
from flask import Flask, request

app = Flask('')

# التوكن النظيف والمحصن 100% ورابط جيميناي
TELEGRAM_TOKEN = '8970508610:AAHV_KC4f6fTRbdx3RDzAJ0Qf8SNMdB3NFA'
GOOGLE_API_KEY = 'AQ.Ab8RN6JKL5jSy8WIsHkZcEwX6-TfRRyp9_dqR07I-9U5PzK03A'

genai.configure(api_key=GOOGLE_API_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@app.route('/')
def home():
    return "Bot is secured and running 24/7 on Render!"

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"Error processing update: {e}")
        return "Error", 500

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "مرحباً بك يا غالي في بوت تحليل الشارتات الذكي! 📊✨\n\n"
        "أرسل لي أي صورة لشارت (الذهب، البيتكوين، إلخ) وسأقوم بتحليلها لك ميكانيكياً بناءً على استراتيجية SMC/ICT مع نسبة مخاطرة 1:3 حذرة لتجنب فخاخ السوق."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_chart_image(message):
    try:
        waiting_msg = bot.reply_to(message, "جاري استقبال الشارت وقراءته ميكانيكياً... انتظر ثواني يا غالي 🔄")
        
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        
        prompt = (
            "أنت خبير محترف في التداول ومحلل فني متقدم تستخدم مفاهيم سمارت موني (SMC) ومنهجية ICT. "
            "حلل هذه الصورة المرفقة للشارت بدقة ميكانيكية حذرة جداً وتجنب الفخاخ تماماً (Fake Breakouts / Market Traps).\n\n"
            "مطلوب منك في التحليل:\n"
            "1. تحديد هيكل السوق الحالي (Market Structure) والاتجاه العام.\n"
            "2. استخراج الفجوات السعرية (Fair Value Gaps - FVG) ونقاط السيولة (Liquidity Sweeps) ومستويات الـ Order Blocks.\n"
            "3. تحديد منطقة الدخول الصافية (Entry Zone) بناءً على الكسر الحقيقي ومؤشر الزيجزاج إن وجد.\n"
            "4. حساب الهدف ووقف الخسارة بدقة مع الالتزام الصارم بنسبة مخاطرة إلى عائد (Risk-to-Reward Ratio) تساوي 1:3 تماماً.\n\n"
            "اكتب التحليل باللغة العربية بأسلوب واضح ومباشر وجاهز للتنفيذ."
        )
        
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content([prompt, image])
        
        bot.delete_message(message.chat.id, waiting_msg.message_id)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
