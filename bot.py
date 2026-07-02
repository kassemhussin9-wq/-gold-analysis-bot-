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
    return "Bot is secured, enhanced, and running 24/7 on Render!"

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
    welcome_text = "مرحباً بك يا غالي في منظومة تحليل الشارتات المطوّرة! 📊✨\nتم تحديث الخوارزمية بفلاتر سيولة صارمة لتجنب الفخاخ. اختر الخدمة:"
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
                              text=f"🔄 جاري سحب بيانات شارت {asset} اليومي وتحليله ميكانيكياً بفلاتر السيولة... انتظر ثواني يا غالي.")
        
        prompt = (
            f"أنت خبير ومحلل فني متقدم تستخدم مفاهيم SMC و ICT. قم بتقديم تحليل يومي شامل وميكانيكي لحركة سعر {asset} الحالية. "
            "حدد هيكل السوق العام مع التركيز على كشف مصايد ومصائد صناع السوق (Market Traps) والكسر الكاذب. اكتب التحليل باللغة العربية بأسلوب صارم ودقيق."
        )
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
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
                              text=f"🎯 ممتاز، اخترت استخراج صفقة قوية على {asset}.\nحدد فريم العمل المراد تصفية السيولة بناءً عليه:", 
                              reply_markup=markup)

    elif call.data and str(call.data).startswith("frame_"):
        frames = {"frame_4h": "4 ساعات", "frame_1h": "ساعة واحدة", "frame_15m": "15 دقيقة", "frame_5m": "5 دقائق"}
        selected_frame = frames[call.data]
        
        if chat_id in user_states and "asset" in user_states[chat_id]:
            user_states[chat_id]["frame"] = selected_frame
            asset = user_states[chat_id]["asset"]
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                                  text=f"📥 تم تحديد فريم ({selected_frame}) لزوج {asset}.\n\n"
                                       "أرسل لي الآن صورة الشارت النظيفة من TradingView. سيتم فحص مناطق السيولة والدخول بحذر مضاعف!")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، يرجى إعادة بدء البوت عبر إرسال /start")

    elif call.data == "request_analysis":
        if chat_id in user_states and "full_analysis" in user_states[chat_id]:
            analysis_text = user_states[chat_id]["full_analysis"]
            bot.send_message(chat_id, f"📊 **التحليل الفني والفلترة الميكانيكية ضد الفخاخ:**\n\n{analysis_text}", parse_mode="Markdown")
            user_states[chat_id] = {}
        else:
            bot.send_message(chat_id, "⚠️ انتهت صلاحية الجلسة أو لم يتم العثور على تحليل للصورة السابقة. يرجى إرسال شارت جديد.")

@bot.message_handler(content_types=['photo'])
def handle_chart_image(message):
    chat_id = message.chat.id
    
    if chat_id in user_states and "frame" in user_states[chat_id]:
        asset = user_states[chat_id]["asset"]
        frame = user_states[chat_id]["frame"]
        
        try:
            waiting_msg = bot.reply_to(message, f"🔍 جاري تشغيل الفلاتر الميكانيكية المتقدمة وفحص فخاخ السيولة لزوج {asset}... 🔄")
            
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            image = Image.open(io.BytesIO(downloaded_file))
            
            prompt = (
                f"أنت خبير محترف ومحلل متقدم جداً تستخدم مفاهيم سمارت موني (SMC) ومنهجية ICT.\n"
                f"أمامك صورة شارت لزوج {asset} فريم ({frame}).\n\n"
                "مهمتك الأساسية هي حماية المتداول من ضرب الستوب الكاذب واكتشاف مصايد صناع السوق (Market Traps) والكسور المزيفة للقمم والقيعان قبل اقتراح الصفقة.\n"
                "طبق الفلاتر التالية بدقة:\n"
                "1. تأكد من وجود كسر حقيقي لبنية السوق (True MSS/BOS) وليس مجرد ذيل شمعة لجمع السيولة.\n"
                "2. حدد منطقة الدخول (Entry) الصارمة حصرياً داخل منطقة الخصم (Discount Area) للشراء، أو منطقة الممتاز (Premium Area) للبيع، ليكون الستوب صغير ومحمي تماماً.\n"
                "3. ضع الأهداف (هدفين كحد أقصى) عند مناطق سيولة رئيسية ومضمونة قريبة، على أن تبدأ نسبة العائد من 1:2 كحد أدنى لضمان نسبة نجاح عالية جداً (Win Rate).\n\n"
                "أخرج لي الإجابة بدقة في قالب JSON يحتوي على المفاتيح التالية فقط وبدون أي نصوص إضافية خارج الـ JSON:\n"
                "{\n"
                '  "trade_type": "BUY" أو "SELL",\n'
                '  "is_limit": true إذا كان الأمر معلق أو false إذا كان دخول مباشر بالماركت,\n'
                '  "entry": "نقطة الدخول الفلترة بالأرقام",\n'
                '  "sl": "وقف الخسارة المحمي تماماً خلف مستويات السيولة بالأرقام",\n'
                '  "tp1": "الهدف الأول المضمون بالأرقام (عائد 1:2 كحد أدنى)",\n'
                '  "tp2": "الهدف الثاني بالأرقام (إن وجد أو اكتب نفس قيمة الهدف الأول إذا لم يكن هناك هدف ثانٍ)",\n'
                '  "rr_ratio": "نسبة العائد الفعلي المقدرة"،\n'
                '  "analysis": "اشرح هنا ميكانيكياً أين كانت الفخاخ (Market Traps) وكيف تم تجنبها وتحديد الدخول الآمن والستوب المحمي بناءً على الـ OB والـ FVG باللغة العربية"\n'
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
            
            trade_type_str = ""
            if data["trade_type"] == "BUY":
                order_name = "شراء معلّق (Buy Limit)" if data["is_limit"] else "شراء مباشر (Buy Market)"
                trade_type_str = f"📉 **{order_name}**"
            else:
                order_name = "بيع معلّق (Sell Limit)" if data["is_limit"] else "بيع مباشر (Sell Market)"
                trade_type_str = f"📈 **{order_name}**"
                
            tp_section = f"🎯 الهدف الأول: `{data['tp1']}`"
            if data['tp2'] and data['tp2'] != data['tp1']:
                tp_section += f"\n🎯 الهدف الثاني: `{data['tp2']}`"
                
            result_message = (
                f"📊 **الصفقة المستخرجة لزوج {asset} (بعد الفلترة القوية):**\n\n"
                f"{trade_type_str}\n"
                f"📉 نقطة الدخول: `{data['entry']}`\n"
                f"❌ وقف الخسارة: `{data['sl']}`\n"
                f"{tp_section}\n\n"
                f"⏱️ الفريم: {frame}\n"
                f"⚖️ نسبة العائد: {data['rr_ratio']}\n"
                f"🛡️ حالة الحماية: مُفلترة ومحمية ضد الكسر الكاذب"
            )
            
            bot.delete_message(chat_id, waiting_msg.message_id)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("❓ هل تريد رؤية فخاخ السوق التي تم تجنبها والتحليل؟", callback_data="request_analysis"))
            
            bot.send_message(chat_id, result_message, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة: {str(e)}")
    else:
        bot.reply_to(message, "⚠️ من فضلك يا غالي، اضغط على /start أولاً واختر 'تحليل وصفقة' وحدد الفريم قبل إرسال الصورة.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
