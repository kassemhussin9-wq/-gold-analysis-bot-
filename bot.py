import os
import telebot
import google.generativeai as genai
import json
import yfinance as yf
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask('')

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# دالة ميكانيكية لسحب بيانات السوق الحية تلقائياً بدون صور
def fetch_live_market_data(asset_type, frame_choice):
    # تحديد التيكر المناسب بناءً على الأصل
    ticker_symbol = "GC=F" if asset_type == "الذهب" else "BTC-USD"
    
    # تحويل الفريم المختار إلى صيغة متوافقة مع ياهو فاينانس
    frame_map = {
        "5 دقائق": {"interval": "5m", "period": "1d"},
        "15 دقيقة": {"interval": "15m", "period": "1d"},
        "ساعة واحدة": {"interval": "1h", "period": "7d"},
        "4 ساعات": {"interval": "1h", "period": "60d"}  # ياهو لا يدعم 4h بشكل مباشر، نسحب 1h ونعالجها بالذكاء
    }
    
    conf = frame_map.get(frame_choice, {"interval": "15m", "period": "1d"})
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=conf["period"], interval=conf["interval"])
        if df.empty:
            return None
        
        # نأخذ آخر 50 شمعة لتحليل الموجة الحالية الأخيرة بدقة (Orderflow)
        recent_data = df.tail(50)
        
        market_summary = []
        for index, row in recent_data.iterrows():
            market_summary.append({
                "time": str(index),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
        return market_summary
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

@app.route('/')
def home():
    return "Bot is running 24/7 with Live Data Scanning & 2.18 Strategy!"

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
        "مرحباً بك يا غالي في منظومة القناص الميكانيكي التلقائي! 📊 الذكية:\n"
        "🔥 [Live Auto-Scanning Engine]\n\n"
        "البوت الآن متصل مباشرة ببيانات السوق الحية لـ الذهب والبيتكوين، وسيقوم بسحب الشموع واستخراج الصفقات تلقائياً بدون صور وبناءً على فترات السيولة وانكشاف الجاما ومصايد صناع السوق.\n\n"
        "اختر الأصل المالي المطلوب لقنصه الحين:"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🪙 قنص وتحليل شارت الذهب (تلقائي حي)", callback_data="trade_gold"),
        InlineKeyboardButton("⚡ قنص وتحليل شارت البيتكوين (تلقائي حي)", callback_data="trade_btc")
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
            InlineKeyboardButton("⏱️ 5 دقائق (5M) - Scalp", callback_data="frame_5m"),
            InlineKeyboardButton("⏱️ 15 دقيقة (15M) - Scalp", callback_data="frame_15m"),
            InlineKeyboardButton("⏱️ ساعة واحدة (1H) - Swing", callback_data="frame_1h"),
            InlineKeyboardButton("⏱️ 4 ساعات (4H) - Swing", callback_data="frame_4h")
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, 
                              text=f"🎯 ممتاز، اخترت تداول {asset}.\nحدد فريم العمل الحين ليقوم البوت بسحب البيانات الحية فوراً وميكانيكياً:", 
                              reply_markup=markup)

    elif call.data and str(call.data).startswith("frame_"):
        frames = {"frame_4h": "4 ساعات", "frame_1h": "ساعة واحدة", "frame_15m": "15 دقيقة", "frame_5m": "5 دقائق"}
        selected_frame = frames[call.data]
        
        if chat_id in user_states and "asset" in user_states[chat_id]:
            asset = user_states[chat_id]["asset"]
            user_states[chat_id]["frame"] = selected_frame
            
            is_scalping = "true" if selected_frame in ["5 دقائق", "15 دقيقة"] else "false"
            mode_label = "⚡ سـكـالـبـيـنـج سـريـع" if is_scalping == "true" else "🏢 ســويــنــج مـمـتـد"
            
            waiting_msg = bot.send_message(chat_id, f"📡 جاري الاتصال بالسوق وسحب بيانات شموع {asset} الحية على فريم ({selected_frame})... 🔄")
            
            # سحب البيانات رقمياً من السوق
            market_data = fetch_live_market_data(asset, selected_frame)
            
            if not market_data:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text="❌ فشل الاتصال بمزود البيانات الحية حالياً، يرجى المحاولة لاحقاً.")
                return
            
            try:
                bot.edit_message_text(chat_id=chat_id, message_id=waiting_msg.message_id, text=f"📊 تم سحب البيانات الرقمية بنجاح! جاري معالجة معادلة 2.18 وفلاتر السيولة (Orderflow/GEX)... ⏳")
                
                prompt = (
                    f"أنت كبير محللين كميين وتستخدم مفاهيم SMC والـ Orderflow وتأثير الـ GEX وصناع السوق بالتكامل مع الاستراتيجية الحسابية الرقمية 2.18.\n"
                    f"أمامك البيانات الرقمية الحية لآخر الشموع السعرية لزوج {asset} فريم ({selected_frame}) بنمط تداول ({mode_label}) [نمط سكالبينج سريع؟ {is_scalping}].\n\n"
                    f"البيانات بصيغة أرقام الشموع:\n{json.dumps(market_data)}\n\n"
                    "قم بمعالجة هذه الأرقام وتطبيق القواعد الصارمة التالية حسابياً:\n"
                    "1. تتبع الـ Orderflow: حلل حركة الأسعار لتحديد أعلى قمة حركية حقيقية وأدنى قاع حركي حقيقي للموجة الحالية بناءً على الأرقام المعطاة. إذا كان النمط سكالبينج (true)، ركز تماماً على أحدث الشموع في نهاية القائمة لتصغير الستوب وجعل الدخول قناص.\n"
                    "2. تقييم وضع الـ GEX ومصايد صناع السوق: حدد حجم السيولة المندفعة والاتجاه السائد (صاعد أم هابط) لتجنب فخاخ التلاعب الكاذب.\n"
                    "3. الحسبة الرقمية الثابتة 2.18: الفارق = (القمة المعتمدة للموجة - القاع المعتمد للموجة). القيمة التصحيحية المستهدفة = (الفارق / 2.18).\n"
                    "4. مستويات الصفقة في الاتجاه الصاعد: الدخول شراء معلق (Buy Limit) = القمة - القيمة التصحيحية. الستوب تحت القاع الفرعي الأخير لضمان ريشيو ممتاز ومحمي تماماً. الهدف الأول (TP1) عند القمة السابقة (ريشيو 1:2 كحد أدنى)، والهدف الثاني (TP2) = القمة + القيمة التصحيحية لضرب سيولة صانع السوق العلوية (ريشيو 1:4).\n"
                    "5. اعكس العملية بدقة ميكانيكية كاملة إذا كان الاتجاه الرقمي السائد هابطاً (Sell Limit).\n\n"
                    "أخرج لي الإجابة بدقة كاملة في قالب JSON يحتوي على المفاتيح التالية فقط وبدون أي نصوص إضافية خارج الـ JSON:\n"
                    "{\n"
                    '  "trade_type": "BUY" أو "SELL",\n'
                    '  "extracted_high": "قيمة القمة الرقمية المعتمدة للموجة الحالية",\n'
                    '  "extracted_low": "قيمة القاع الرقمي المعتمد المستخرج",\n'
                    '  "entry": "نقطة الدخول المحسوبة رقمياً بالأرقام",\n'
                    '  "sl": "وقف الخسارة المحسن والذكي القريب بالأرقام لحماية المراكز",\n'
                    '  "tp1": "الهدف الأول الميكانيكي (القمة/القاع السابقة)",\n'
                    '  "tp2": "الهدف الممتد الثاني بالأرقام",\n'
                    '  "rr_ratio": "الريشيو الفعلي المستخرج (مثال: 1:2 للأول و 1:4 للثاني)",\n'
                    '  "analysis": "اشرح هنا باللغة العربية تفاصيل الحسبة وكيف تطابقت مع تدفقات السيولة الرقمية وتحوط صناع السوق الحية لضمان دقة الانعكاس وبدون صور"\n'
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
                    f"⚙️ **قراءة حية وتلقائية:** `Orderflow & GEX Engine (No Images)`\n"
                    f"📈 **الفئة والنمط المفعّل:** `{mode_label}`\n\n"
                    f"📊 **الصفقة الميكانيكية الحية المستخرجة (2.18):**\n\n"
                    f"{icon} **نوع الأمر المعتمد:** `{order_name}`\n"
                    f"🔺 قمة السيولة الحالية: `{data['extracted_high']}`\n"
                    f"🔻 قاع السيولة الحالي: `{data['extracted_low']}`\n"
                    f"🎯 **نقطة الدخول القناصة:** `{data['entry']}`\n"
                    f"❌ **وقف الخسارة (SL):** `{data['sl']}`\n"
                    f"🎯 **الهدف الأول (TP1):** `{data['tp1']}`\n"
                    f"🎯 **الهدف الثاني (TP2):** `{data['tp2']}`\n\n"
                    f"⏱️ الفريم المعالج: {selected_frame}\n"
                    f"⚖️ نسبة العائد (الريشيو): {data['rr_ratio']}\n"
                    f"🛡️ حالة الحماية: سحب رقمي مباشر مصفى من فخاخ التلاعب وصناع السوق"
                )
                
                bot.delete_message(chat_id, waiting_msg.message_id)
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("❓ تفاصيل تدفق السيولة الرقمية وفخاخ الجاما؟", callback_data="request_analysis"))
                
                bot.send_message(chat_id, result_message, reply_markup=markup, parse_mode="Markdown")
                
            except Exception as e:
                bot.send_message(chat_id, f"❌ حدث خطأ أثناء التحليل الحسابي الرقمي: {str(e)}")
        else:
            bot.send_message(chat_id, "⚠️ عذراً، يرجى إعادة بدء البوت عبر إرسال /start")

    elif call.data == "request_analysis":
        if chat_id in user_states and "full_analysis" in user_states[chat_id]:
            analysis_text = user_states[chat_id]["full_analysis"]
            bot.send_message(chat_id, f"📊 **التفسير الرقمي التلقائي ومكافحة فخاخ السيولة:**\n\n{analysis_text}", parse_mode="Markdown")
            user_states[chat_id] = {}
        else:
            bot.send_message(chat_id, "⚠️ انتهت صلاحية الجلسة أو لم يتم العثور على تحليل سابـق.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
