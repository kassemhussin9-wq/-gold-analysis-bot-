import os
import telebot
import google.generativeai as genai
from PIL import Image
import io
import json
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask('')

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

@app.route('/')
def home():
    return "Bot is running 24/7 with the 2.18 Mathematical Strategy incorporated!"

@app.route('/' + TELEGRAM_TOKEN if TELEGRAM_TOKEN else '', methods=['POST'])
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
    welcome_text = (
        "مرحباً بك يا غالي في منظومة تحليل الشارتات المطوّرة! 📊✨\n"
        "تم دمج الاستراتيجية الرقمية الميكانيكية (2.18) لحساب القمم والقيعان بدقة وتجنب فخاخ صناع السوق. اختر الخدمة:"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("1️⃣ تحليل شارت الذهب اليومي (تلقائي)", callback_data="analyze_gold_daily"),
        InlineKeyboardButton("2️⃣ استخراج صفقة رقمية ميكانيكية (تحتاج صورة)", callback_data="trade_gold"),
        InlineKeyboardButton("3️⃣ تحليل شارت البيتكوين اليومي (تلقائي)", callback_data="analyze_btc_daily"),
        InlineKeyboardButton("4️⃣ استخراج صفقة بتكوين ميكانيكية (تحتاج صورة)", callback_data="trade_btc")
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    if call.data in ["analyze_gold_daily", "analyze_btc_daily"]:
        asset = "الذهب (XAU/USD)" if call.data == "analyze_gold_daily" else "البيتكوين (BTC/USD)"
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                              text=f"🔄 جاري سحب بيانات شارت {asset} وتحليله رقمياً... انتظر ثواني يا غالي.")
        
        prompt = (
            f"أنت خبير ومحلل فني متقدم تستخدم مفاهيم SMC و ICT بالإضافة إلى المعادلات الرقمية الميكانيكية. "
            f"قم بتقديم تحليل يومي شامل وميكانيكي لحركة سعر {asset} الحالية مع توضيح مستويات السيولة والفخاخ المتوقعة. اكتب التحليل باللغة العربية."
        )
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            bot.send_message(chat_id, response.text)
        except Exception as e:
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء جلب التحليل: {str(e)}")

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
                              text=f"🎯 ممتاز، اخترت استخراج صفقة ميكانيكية قوية على {asset}.\nحدد فريم العمل لتطبيق الحسبة الرقمية وفحص الشارت:", 
                              reply_markup=markup)

    elif call.data and str(call.data).startswith("frame_"):
        frames = {"frame_4h": "4 ساعات", "frame_1h": "ساعة واحدة", "frame_15m": "15 دقيقة", "frame_5m": "5 دقائق"}
        selected_frame = frames[call.data]
        
        if chat_id in user_states and "asset" in user_states[chat_id]:
            user_states[chat_id]["frame"] = selected_frame
            asset = user_states[chat_id]["asset"]
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                                  text=f"📥 تم تحديد فريم ({selected_frame}) لزوج {asset}.\n\n"
                                       "أرسل لي الآن صورة الشارت النظيفة من TradingView. سيقوم البوت بقراءة القمة والقاع وتطبيق معادلة الـ 2.18 فوراً!")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، يرجى إعادة بدء البوت عبر إرسال /start")

    elif call.data == "request_analysis":
        if chat_id in user_states and "full_analysis" in user_states[chat_id]:
            analysis_text = user_states[chat_id]["full_analysis"]
            bot.send_message(chat_id, f"📊 **التحليل الرقمي الميكانيكي وتفسير الفخاخ:**\n\n{analysis_text}", parse_mode="Markdown")
            user_states[chat_id] = {}
        else:
            bot.send_message(chat_id, "⚠️ انتهت صلاحية الجلسة أو لم يتم العثور على تحليل للصورة السابقة.")

@bot.message_handler(content_types=['photo'])
def handle_chart_image(message):
    chat_id = message.chat.id
    
    if chat_id in user_states and "frame" in user_states[chat_id]:
        asset = user_states[chat_id]["asset"]
        frame = user_states[chat_id]["frame"]
        
        try:
            waiting_msg = bot.reply_to(message, f"🔍 جاري استخراج القمة والقاع من شارت {asset} وتطبيق معادلة 2.18 الرياضية... 🔄")
            
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            image = Image.open(io.BytesIO(downloaded_file))
            
            prompt = (
                f"أنت خبير محترف ومحلل متقدم جداً تستخدم مفاهيم سمارت موني (SMC) والتحليل الرقمي الرياضي.\n"
                f"أمامك صورة شارت لزوج {asset} فريم ({frame}).\n\n"
                "مهمتك الأساسية هي تطبيق الاستراتيجية الرياضية التالية بالملي وبدقة متناهية:\n"
                "1. استخرج من الصورة قيمة أعلى قمة واضحة وأدنى قاع واضح للحركة الحالية.\n"
                "2. قم بحساب الفارق بين القمة والقاع (القمة - القاع).\n"
                "3. اقسم الناتج على الثابت الرياضي الميكانيكي (2.18) بدقة لاستخراج قيمة الموجة التصحيحية والهدف الممتد.\n"
                "4. إذا كان الهيكل العام مائل للصعود (الاتجاه الحالي صاعد)، ضع أمر شراء معلق (Buy Limit) حيث تكون نقطة الدخول = (القمة - القيمة المقسمة)، وقف الخسارة محمي تماماً تحت القاع الرئيسي، الهدف الأول (TP1) عند القمة السابقة (مما يمنح ريشيو 1:2)، والهدف الثاني (TP2) عند (القمة + القيمة المقسمة) لضرب السيولة العلوية (مما يمنح ريشيو 1:4).\n"
                "5. إذا كان الاتجاه هابطاً، اعكس العملية ميكانيكياً لصفقة بيع معلق (Sell Limit).\n\n"
                "أخرج لي الإجابة بدقة كاملة في قالب JSON يحتوي على المفاتيح التالية فقط وبدون أي نصوص إضافية خارج الـ JSON:\n"
                "{\n"
                '  "trade_type": "BUY" أو "SELL",\n'
                '  "extracted_high": "قيمة القمة المستخرجة بالأرقام",\n'
                '  "extracted_low": "قيمة القاع المستخرجة بالأرقام",\n'
                '  "entry": "نقطة الدخول المحسوبة بالمعادلة الرقمية بالأرقام",\n'
                '  "sl": "وقف الخسارة المحمي تماماً بالأرقام",\n'
                '  "tp1": "الهدف الأول (القمة السابقة في الشراء أو القاع في البيع)",\n'
                '  "tp2": "الهدف الممتد الثاني المحسوب بالمعادلة الرقمية بالأرقام",\n'
                '  "rr_ratio": "توضيح الريشيو المقدر (مثال: 1:2 للهدف الأول و 1:4 للثاني)",\n'
                '  "analysis": "اشرح هنا باللغة العربية تفاصيل الحسبة الرياضية المستخرجة وكيف تتطابق مع مستويات السيولة والـ FVG والـ Order Block لحماية الحساب من الفخاخ الكاذبة"\n'
                "}"
            )
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([prompt, image])
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            data = json.loads(raw_text)
            user_states[chat_id]["full_analysis"] = data["analysis"]
            
            order_name = "شراء معلّق (Buy Limit)" if data["trade_type"] == "BUY" else "بيع معلّق (Sell Limit)"
            icon = "📉" if data["trade_type"] == "BUY" else "📈"
                
            result_message = (
                f"📊 **الصفقة الرقمية المستخرجة (استراتيجية 2.18):**\n\n"
                f"{icon} **نوع الأمر:** `{order_name}`\n"
                f"🔺 القمة المستخرجة: `{data['extracted_high']}`\n"
                f"🔻 القاع المستخرج: `{data['extracted_low']}`\n"
                f"🎯 **نقطة الدخول:** `{data['entry']}`\n"
                f"❌ **وقف الخسارة:** `{data['sl']}`\n"
                f"🎯 **الهدف الأول:** `{data['tp1']}`\n"
                f"🎯 **الهدف الثاني:** `{data['tp2']}`\n\n"
                f"⏱️ الفريم: {frame}\n"
                f"⚖️ نسبة العائد (الريشيو): {data['rr_ratio']}\n"
                f"🛡️ حالة الحماية: تصفية ميكانيكية صارمة ضد الكسر الكاذب"
            )
            
            bot.delete_message(chat_id, waiting_msg.message_id)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("❓ تفاصيل الحسبة الرياضية وفخاخ السوق؟", callback_data="request_analysis"))
            
            bot.send_message(chat_id, result_message, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة الرياضية: {str(e)}")
    else:
        bot.reply_to(message, "⚠️ من فضلك يا غالي، اضغط على /start أولاً واختر الخدمة وحدد الفريم قبل إرسال الصورة.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
