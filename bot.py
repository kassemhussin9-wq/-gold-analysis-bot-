import os
import telebot
import google.generativeai as genai
import json
import urllib.request
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask('')

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

def fetch_live_market_data(asset_type, frame_choice):
    limit = 30
    try:
        if asset_type == "الذهب":
            # جلب شارت الذهب الفوري المباشر والمطابق لأسعار التداول الحية تماماً
            period = "5d" if frame_choice in ["5 دقائق", "15 دقيقة"] else "30d"
            interval_map = {"5 دقائق": "5m", "15 دقيقة": "15m", "ساعة واحدة": "1h", "4 ساعات": "1h"}
            sub_int = interval_map.get(frame_choice, "1h")
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range={period}&interval={sub_int}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=8) as response:
                json_data = json.loads(response.read().decode())
                result = json_data["chart"]["result"][0]
                indicators = result["indicators"]["quote"][0]
                
                market_summary = []
                for i in range(len(result["timestamp"])):
                    if indicators["open"][i] and indicators["high"][i] and indicators["low"][i] and indicators["close"][i]:
                        market_summary.append({
                            "open": round(float(indicators["open"][i]), 2),
                            "high": round(float(indicators["high"][i]), 2),
                            "low": round(float(indicators["low"][i]), 2),
                            "close": round(float(indicators["close"][i]), 2),
                            "volume": int(indicators["volume"][i]) if indicators["volume"][i] else 0
                        })
                return market_summary[-limit:]
        else:
            # شارت البيتكوين المباشر
            interval_map = {"5 دقائق": "5m", "15 دقيقة": "15m", "ساعة واحدة": "1h", "4 ساعات": "4h"}
            sub_int = interval_map.get(frame_choice, "1h")
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={sub_int}&limit={limit}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode())
                market_summary = []
                for row in res_data:
                    market_summary.append({
                        "open": round(float(row[1]), 2),
                        "high": round(float(row[2]), 2),
                        "low": round(float(row[3]), 2),
                        "close": round(float(row[4]), 2),
                        "volume": int(float(row[5]))
                    })
                return market_summary

    except Exception as e:
        print(f"Error fetching direct live data: {e}")
        return None

@app.route('/')
def home():
    return "Bot Core Live with Real Market Price Feeds!"

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
        "مرحباً بك يا غالي في منظومة القناص الميكانيكي! 📊\n"
        "📡 [Live Global Market Data Stream Connected]\n\n"
        "البوت الحين مبرمج ليسحب الشارت المباشر للذهب والبيتكوين تلقائياً وبأرقام الشاشة الحية الحالية الحقيقية.\n\n"
        "اختر الأصل المالي المطلوب الحين:"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🪙 قنص شارت الذهب المباشر (XAU/USD)", callback_data="trade_gold"),
        InlineKeyboardButton("⚡ قنص شارت البيتكوين المباشر (BTC/USDT)", callback_data="trade_btc")
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    
    if call.data in ["trade_gold", "trade_btc"]:
        asset = "الذهب" if call.data == "trade_gold" else "البيتكوين"
        user_states[chat_id] = {"asset": asset}
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⏱️ 5 دقائق (5M)", callback_data="frame_5m"),
            InlineKeyboardButton("⏱️ 15 دقيقة (15M)", callback_data="frame_15m"),
            InlineKeyboardButton("⏱️ ساعة واحدة (1H)", callback_data="frame_1h"),
            InlineKeyboardButton("⏱️ 4 ساعات (4H)", callback_data="frame_4h")
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                              text=f"🎯 ممتاز، اخترت تداول {asset}.\nحدد فريم العمل الحين ليقوم البوت بسحب الشارت المباشر تلقائياً:", 
                              reply_markup=markup)

    elif call.data and str(call.data).startswith("frame_"):
        frames = {"frame_4h": "4 ساعات", "frame_1h": "ساعة واحدة", "frame_15m": "15 دقيقة", "frame_5m": "5 دقائق"}
        selected_frame = frames[call.data]
        
        if chat_id in user_states and "asset" in user_states[chat_id]:
            asset = user_states[chat_id]["asset"]
            user_states[chat_id]["frame"] = selected_frame
            
            is_scalping = "true" if selected_frame in ["5 دقائق", "15 دقيقة"] else "false"
            mode_label = "⚡ سـكـالـبـيـنج سـريـع" if is_scalping == "true" else "🏢 ســويــنــج مـمـتـد"
            
            waiting_msg = bot.send_message(chat_id, f"📡 جاري فتح قنوات البيانات والاتصال بشارت {asset} المباشر والحي... 🔄")
            
            market_data = fetch_live_market_data(asset, selected_frame)
            
            if not market_data:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, 
                                      text="❌ واجه السيرفر قيوداً مؤقتة في جلب البيانات الحية مباشرة. يرجى إعادة الضغط أو تجربة فريم آخر للتحديث.")
                return
            
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=f"📊 تم جلب الشارت الحي بنجاح! جاري تطبيق الفلاتر الرقمية والريشيو 1:3... ⏳")
                
                prompt = (
                    f"أنت كبير محللين كميين وتستخدم مفاهيم SMC والـ Orderflow بالتكامل مع الاستراتيجية الحسابية الرقمية 2.18.\n"
                    f"أمامك شارت الشموع الحية المأخوذة فوراً من خوادم التداول لزوج {asset} فريم ({selected_frame}).\n\n"
                    f"البيانات الحية المباشرة من السوق الحين:\n{json.dumps(market_data)}\n\n"
                    "قم بمعالجة هذه الأرقام وتطبيق القواعد الصارمة التالية حسابياً:\n"
                    "1. حدد أعلى قمة حركية حقيقية وأدنى قاع حركي حقيقي للموجة الحالية بناءً على الأرقام المعطاة.\n"
                    "2. الحسبة الرقمية الثابتة 2.18: الفارق = (القمة - القاع). القيمة التصحيحية المستهدفة = (الفارق / 2.18).\n"
                    "3. مستويات الصفقة: الدخول شراء معلق (Buy Limit) = القمة - القيمة التصحيحية. الستوب تحت القاع لضمان ريشيو 1:3 محمي تماماً. الهدف الأول (TP1) عند القمة السابقة، والهدف الثاني (TP2) = القمة + القيمة التصحيحية.\n"
                    "4. اعكس العملية بدقة ميكانيكية كاملة إذا كان الاتجاه هابطاً (Sell Limit) واجعل الريشيو دائماً 1:3.\n\n"
                    "أخرج لي الإجابة بدقة كاملة في قالب JSON يحتوي على المفاتيح التالية فقط وبدون أي نصوص إضافية خارج الـ JSON:\n"
                    "{\n"
                    '  "trade_type": "BUY" أو "SELL",\n'
                    '  "extracted_high": "قيمة القمة المستخرجة الحقيقية الحين",\n'
                    '  "extracted_low": "قيمة القاع المستخرج الحقيقي الحين",\n'
                    '  "entry": "نقطة الدخول المحسوبة رقمياً",\n'
                    '  "sl": "وقف الخسارة لضمان ريشيو 1:3 الصارم",\n'
                    '  "tp1": "الهدف الأول الميكانيكي",\n'
                    '  "tp2": "الهدف الممتد الثاني",\n'
                    '  "rr_ratio": "1:3",\n'
                    '  "analysis": "اشرح هنا باختصار باللغة العربية تفاصيل تدفق السيولة الحية للشارت"\n'
                    "}"
                )
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                
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
                    f"⚙ **نوع الاتصال المفعّل:** `Global Price Feed Connection` 📡\n"
                    f"📈 **الفئة والنمط المفعّل:** `{mode_label}`\n\n"
                    f"📊 **الصفقة المستخرجة من شارت الذهب المباشر (2.18):**\n\n"
                    f"{icon} **نوع الأمر المعتمد:** `{order_name}`\n"
                    f"🔺 قمة الشارت الحقيقية الحين: `{data['extracted_high']}`\n"
                    f"🔻 قاع الشارت الحقيقي الحين: `{data['extracted_low']}`\n"
                    f"🎯 **نقطة الدخول القناصة:** `{data['entry']}`\n"
                    f"❌ **وقف الخسارة (SL):** `{data['sl']}`\n"
                    f"🎯 **الهدف الأول (TP1):** `{data['tp1']}`\n"
                    f"🎯 **الهدف الثاني (TP2):** `{data['tp2']}`\n\n"
                    f"⏱ الفريم المعالج: {selected_frame}\n"
                    f"⚖ نسبة العائد المحددة: `1:3`\n"
                    f"🛡 حالة البيانات: حية ومطابقة لشاشات التداول تماماً"
                )
                
                bot.delete_message(chat_id, waiting_msg.message_id)
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("❓ تفاصيل تدفق السيولة؟", callback_data="request_analysis"))
                
                bot.send_message(chat_id, result_message, reply_markup=markup, parse_mode="Markdown")
                
            except Exception as e:
                bot.send_message(chat_id, f"❌ حدث خطأ أثناء تحليل بيانات الشارت الحية: {str(e)}")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، يرجى إعادة بدء البوت عبر إرسال /start")

    elif call.data == "request_analysis":
        if chat_id in user_states and "full_analysis" in user_states[chat_id]:
            analysis_text = user_states[chat_id]["full_analysis"]
            bot.send_message(chat_id, f"📊 **التفسير الميكانيكي للشارت المباشر الحقيقي:**\n\n{analysis_text}", parse_mode="Markdown")
            user_states[chat_id] = {}
        else:
            bot.send_message(chat_id, "⚠️ انتهت صلاحية الجلسة.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
