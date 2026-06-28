import os
import telebot
import google.generativeai as genai
from PIL import Image
import io
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask('')

# سحب التوكن والمفتاح بأمان ميكانيكي من إعدادات السيرفر
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8970508610:AAHV_KC4f6fTRbdx3RDzAJ0Qf8SNMdB3NFA')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

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
    user_states[message.chat.id] = {}
    welcome_text = "مرحباً بك يا غالي في منظومة تحليل الشارتات الذكية! 📊✨\nاختر الخدمة المطلوبة ميكانيكياً من الأزرار أدناه:"
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("1️⃣ تحليل شارت الذهب اليومي (تلقائي)", callback_data="analyze_gold_daily"),
        InlineKeyboardButton("2️⃣ تحليل وصفقة على الذهب (تحتاج صورة)", callback_data="trade_gold"),
        InlineKeyboardButton("3️⃣ تحليل شارت البيتكوين اليومي (تلقائي)", callback_data="analyze_btc_daily"),
        InlineKeyboardButton("4️⃣ تحليل وصفقة بتكوين (تحتاج صورة)", callback_data="trade_btc")
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    if call.data in ["analyze_gold_daily", "analyze_btc_daily"]:
        asset = "الذهب (XAU/USD)" if call.data == "analyze_gold_daily" else "البيتكوين (BTC/USD)"
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                              text=f"🔄 جاري سحب بيانات شارت {asset} اليومي وتحليله ميكانيكياً... انتظر ثواني يا غالي.")
        
        prompt = (
            f"أنت خبير ومحلل فني متقدم تستخدم مفاهيم SMC و ICT. قم بتقديم تحليل يومي شامل وميكانيكي لحركة سعر {asset} الحالية. "
            "حدد هيكل السوق العام (Bullish/Bearish)، ومناطق السيولة اليومية القريبة، وتوقعات الاتجاه القادم مع تجنب فخاخ السوق تماماً. اكتب التحليل باللغة العربية بأسلوب واضح وبسيط."
        )
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            bot.send_message(chat_id, response.text)
        except Exception as e:
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء جلب التحليل التلقائي: {str(e)}")

    elif call.data in ["trade_gold", "trade_btc"]:
        asset = "الذهب" if call.data == "trade_gold" else "البيتكوين"
        user_states[chat_id] = {"action": "trade", "asset": asset}
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⏱️ 4 ساعات (4H)", callback_data="frame_4h"),
            InlineKeyboardButton("⏱️ ساعة واحدة (1H)", callback_data="frame_1h"),
            InlineKeyboardButton("⏱️ 15 دقيقة (15M)", callback_data="frame_15m"),
            InlineKeyboardButton("⏱️ 5 دقائق (5M)", callback_data="frame_5m")
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                              text=f"🎯 ممتاز، اخترت تحليل وصفقة على {asset}.\nالآن حدد شمعة الفريم المراد العمل عليها أولاً:", 
                              reply_markup=markup)

    elif call.data and str(call.data).startswith("frame_"):
        frames = {"frame_4h": "4 ساعات", "frame_1h": "ساعة واحدة", "frame_15m": "15 دقيقة", "frame_5m": "5 دقائق"}
        selected_frame = frames[call.data]
        
        if chat_id in user_states and "asset" in user_states[chat_id]:
            user_states[chat_id]["frame"] = selected_frame
            asset = user_states[chat_id]["asset"]
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                                  text=f"📥 تم تحديد فريم ({selected_frame}) لزوج {asset}.\n\n"
                                       "أرسل لي الآن صورة الشارت النظيفة من TradingView ليتم استخراج صفقة ذكية وقوية فوراً!")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، يرجى إعادة بدء البوت عبر إرسال /start")

@bot.message_handler(content_types=['photo'])
def handle_chart_image(message):
    chat_id = message.chat.id
    
    if chat_id in user_states and "frame" in user_states[chat_id]:
        asset = user_states[chat_id]["asset"]
        frame = user_states[chat_id]["frame"]
        
        try:
            waiting_msg = bot.reply_to(message, f"جاري قراءة شارت {asset} على فريم {frame} ميكانيكياً واستخراج الصفقة الذكية... 🔄")
            
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            image = Image.open(io.BytesIO(downloaded_file))
            
            prompt = (
                f"أنت خبير محترف ومحلل متقدم تستخدم مفاهيم سمارت موني (SMC) ومنهجية ICT.\n"
                f"أمامك صورة شارت لزوج {asset}. تم تحديد فريم التداول ليكون عيار شمعة ({frame}) تماماً.\n\n"
                "حلل الصورة بدقة ميكانيكية حذرة جداً وتجنب الفخاخ تماماً (Fake Breakouts / Market Traps).\n"
                "بناءً على التحليل، استخرج صفقة ذكية وقوية تتضمن النقاط التالية بالترتيب وبشكل واضح:\n"
                "1. هيكل السوق الحالي على الفريم المحدد والاتجاه العام.\n"
                "2. مستويات الـ Order Blocks المستهدفة والسيولة (Liquidity Sweeps) والفجوات السعرية (FVG).\n"
                "3. نقطة الدخول الصافية (Entry Price).\n"
                "4. وقف الخسارة الحذر (Stop Loss).\n"
                "5. الهدف النهائي (Take Profit) مع الالتزام الصارم والكامل بنسبة مخاطرة إلى عائد (Risk-to-Reward Ratio) تساوي 1:3 تماماً لتجنب فخاخ السوق.\n\n"
                "اكتب النتيجة باللغة العربية بأسلوب احترافي ميكانيكي جاهز للتنفيذ فوراً."
            )
            
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content([prompt, image])
            
            bot.delete_message(chat_id, waiting_msg.message_id)
            bot.reply_to(message, response.text)
            user_states[chat_id] = {}
            
        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة: {str(e)}")
    else:
        bot.reply_to(message, "⚠️ من فضلك يا غالي، اضغط على /start أولاً واختر 'تحليل وصفقة' وحدد الفريم قبل إرسال الصورة.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
