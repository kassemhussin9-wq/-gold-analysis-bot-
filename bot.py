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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    try:
        if asset_type == "الذهب":
            period = "5d" if frame_choice in ["5 دقائق", "15 دقيقة"] else "30d"
            interval_map = {"5 دقائق": "5m", "15 دقيقة": "15m", "ساعة واحدة": "1h", "4 ساعات": "1h"}
            sub_int = interval_map.get(frame_choice, "1h")
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range={period}&interval={sub_int}"
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
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
                            "close": round(float(indicators["close"][i]), 2)
                        })
                return market_summary[-limit:]
        else:
            interval_map = {"5 دقائق": "5m", "15 دقيقة": "15m", "ساعة واحدة": "1h", "4 ساعات": "4h"}
            sub_int = interval_map.get(frame_choice, "1h")
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval={sub_int}&limit={limit}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode())
                market_summary = []
                for row in res_data:
                    market_summary.append({
                        "open": round(float(row[1]), 2),
                        "high": round(float(row[2]), 2),
                        "low": round(float(row[3]), 2),
                        "close": round(float(row[4]), 2)
                    })
                return market_summary

    except Exception as e:
        print(f"Error fetching live data for {asset_type}: {e}")
        return None

@app.route('/')
def home():
    return "Bot JSON Schema Patched Successfully!"

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
        "📡 [Strict JSON Validation Mode Active]\n\n"
        "تم إصلاح هيكلة البيانات بالكامل الحين لتعمل على الذهب والبيتكوين بدون أي أخطاء برمجية.\n\n"
        "اختر الأصل المالي الحين:"
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
                              text=f"🎯 ممتاز، اخترت تداول {asset}.\nحدد فريم العمل الحين ليقوم البوت بسحب الشارت المباشر:", 
                              reply_markup=markup)

    elif call.data and str(call.data).startswith("frame_"):
        frames = {"frame_4h": "4 ساعات", "frame_1h": "ساعة واحدة", "frame_15m": "15 دقيقة", "frame_5m": "5 دقائق"}
        selected_frame = frames[call.data]
        
        if chat_id in user_states and "asset" in user_states[chat_id]:
            asset = user_states[chat_id]["asset"]
            user_states[chat_id]["frame"] = selected_frame
            
            is_scalping = "true" if selected_frame in ["5 دقائق", "15 دقيقة"] else "false"
            mode_label = "⚡ سـكـالـبـيـنج سـريـع" if is_scalping == "true" else "🏢 ســويــنــج مـمـتـد"
            
            waiting_msg = bot.send_message(chat_id, f"📡 جاري جلب بيانات شارت {asset} الحية وتحليل الموجة... 🔄")
            
            market_data = fetch_live_market_data(asset, selected_frame)
            
            if not market_data:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, 
                                      text="❌ واجه السيرفر قيوداً في جلب البيانات الحية. يرجى إعادة المحاولة.")
                return
            
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=f"📊 تم جلب الشارت بنجاح! جاري التثبيت الرقمي واستخراج الصفقة... ⏳")
                
                prompt = (
                    f"أنت كبير محللين كميين وتستخدم مفاهيم SMC والـ Orderflow بالتكامل مع الاستراتيجية الحسابية الرقمية 2.18.\n"
                    f"أمامك شارت الشموع لزوج {asset} فريم ({selected_frame}).\n\n"
                    f"بيانات الشارت الممررة الحين:\n{json.dumps(market_data)}\n\n"
                    "قم بتنفيذ المهام التالية بدقة قطعية:\n"
                    "1. استخرج أعلى قمة حركية حقيقية (high) وأدنى قاع حركي حقيقي (low) للموجة الحالية.\n"
                    "2. حدد اتجاه تدفق السيولة ميكانيكياً (BUY أو SELL).\n"
                    "3. اكتب شرحاً ميكانيكياً مختصراً جداً لحركة السعر.\n\n"
                    "يجب إخراج النتيجة كـ JSON صالح ومطابق تماماً لهذا القالب وبدون أي أخطاء في الفواصل:\n"
                    "{\n"
                    '  "trade_type": "BUY",\n'
                    '  "extracted_high": 0.0,\n'
                    '  "extracted_low": 0.0,\n'
                    '  "analysis": "تحليل تدفق السيولة هنا باللغة العربية"\n'
                    "}"
                )
                
                # إجبار الموديل على الالتزام الصارم ببنية JSON 100% لتجنب أخطاء الفواصل
                generation_config = {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_output_tokens": 1000,
                    "response_mime_type": "application/json"
                }
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt, generation_config=generation_config)
                
                raw_text = response.text.strip()
                data = json.loads(raw_text)
                user_states[chat_id]["full_analysis"] = data["analysis"]
                
                high = float(data["extracted_high"])
                low = float(data["extracted_low"])
                diff = high - low
                correction_value = diff / 2.18
                
                if data["trade_type"] == "BUY":
                    order_name = "شراء معلّق (Buy Limit)"
                    icon = "📉"
                    entry = high - correction_value
                    sl = low
                    risk = entry - sl
                    tp1 = entry + risk
                    tp2 = entry + (risk * 3)
                else:
                    order_name = "بيع معلّق (Sell Limit)"
                    icon = "📈"
                    entry = low + correction_value
                    sl = high
                    risk = sl - entry
                    tp1 = entry - risk
                    tp2 = entry - (risk * 3)
                
                result_message = (
                    f"⚙️ **نوع الاتصال المفعّل:** `Strict JSON Feed Connection` 📡\n"
                    f"📈 **الفئة والنمط المفعّل:** `{mode_label}`\n\n"
                    f"📊 **الصفقة الميكانيكية المستخرجة من شارت {asset} (2.18):**\n\n"
                    f"{icon} **نوع الأمر المعتمد:** `{order_name}`\n"
                    f"🔺 قمة الشارت المستخرجة: `{high:.2f}`\n"
                    f"🔻 قاع الشارت المستخرج: `{low:.2f}`\n"
                    f"🎯 **نقطة الدخول القناصة:** `{entry:.2f}`\n"
                    f"❌ **وقف الخسارة (SL):** `{sl:.2f}`\n"
                    f"🎯 **الهدف الأول (TP1):** `{tp1:.2f}`\n"
                    f"🎯 **الهدف الثاني الرئيسي (TP2):** `{tp2:.2f}`\n\n"
                    f"⏱️ الفريم المعالج: {selected_frame}\n"
                    f"⚖️ نسبة العائد المحسوبة ميكانيكياً: `1:3 بالملي`\n"
                    f"🛡️ حالة البيانات: تمت معالجتها بالهيكلية الصارمة 100%"
                )
                
                bot.delete_message(chat_id, waiting_msg.message_id)
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("❓ تفاصيل تدفق السيولة؟", callback_data="request_analysis"))
                
                bot.send_message(chat_id, result_message, reply_markup=markup, parse_mode="Markdown")
                
            except Exception as e:
                bot.send_message(chat_id, f"❌ حدث خطأ أثناء معالجة البيانات الحركية: {str(e)}")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، يرجى إعادة بدء البوت عبر إرسال /start")

    elif call.data == "request_analysis":
        if chat_id in user_states and "full_analysis" in user_states[chat_id]:
            analysis_text = user_states[chat_id]["full_analysis"]
            bot.send_message(chat_id, f"📊 **التفسير الميكانيكي للشارت المباشر المستقر:**\n\n{analysis_text}", parse_mode="Markdown")
            user_states[chat_id] = {}
        else:
            bot.send_message(chat_id, "⚠️ انتهت صلاحية الجلسة.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
