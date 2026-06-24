import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import google.generativeai as genai
from flask import Flask
from threading import Thread
import io
from PIL import Image

TOKEN = os.environ.get('TELEGRAM_TOKEN')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GOOGLE_API_KEY)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

user_data = {}

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(is_persistent=True, resize_keyboard=True)
    markup.append("▶️ Start Analysis")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Gold Analysis Bot. Please select your timeframe:", reply_markup=get_main_keyboard())
    show_timeframe_options(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "▶️ Start Analysis")
def handle_start_button(message):
    show_timeframe_options(message.chat.id)

def show_timeframe_options(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⏱️ Timeframe (H4 + M15)", callback_data="tf_h4_m15"))
    markup.row(InlineKeyboardButton("⏱️ Timeframe (H1 + M5)", callback_data="tf_h1_m5"))
    bot.send_message(chat_id, "Choose the timeframe for your trade:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tf_"))
def handle_timeframe_selection(call):
    chat_id = call.message.chat.id
    selection = call.data
    
    if selection == "tf_h4_m15":
        user_data[chat_id] = {"mode": "H4_M15", "images": [], "expected": "Higher"}
        bot.send_message(chat_id, "🎯 Sent the Higher Timeframe chart (H4):")
    elif selection == "tf_h1_m5":
        user_data[chat_id] = {"mode": "H1_M5", "images": [], "expected": "Higher"}
        bot.send_message(chat_id, "🎯 Sent the Higher Timeframe chart (H1):")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    if chat_id not in user_data or "mode" not in user_data[chat_id]:
        bot.reply_to(message, "Please click Start Analysis first.", reply_markup=get_main_keyboard())
        return

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image = Image.open(io.BytesIO(downloaded_file))
    
    state = user_data[chat_id]
    
    if state["expected"] == "Higher":
        state["images"].append(image)
        state["expected"] = "Lower"
        lower_tf = "M15" if state["mode"] == "H4_M15" else "M5"
        bot.send_message(chat_id, f"✅ Higher timeframe received. Now send the Lower timeframe chart ({lower_tf}):")
    
    elif state["expected"] == "Lower":
        state["images"].append(image)
        state["expected"] = "Done"
        bot.send_message(chat_id, "⏳ Processing charts and running technical analysis via Gemini AI...")
        execute_analysis(chat_id)

def execute_analysis(chat_id):
    try:
        state = user_data[chat_id]
        higher_img = state["images"][0]
        lower_img = state["images"][1]
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = "Analyze these two gold (XAUUSD) charts. Provide a detailed technical analysis in Arabic including entries, stop loss, take profit (Risk-Reward 1:3), support/resistance levels, and SMC/ICT principles like FVG, liquidity sweeps, and market structure shifts."
        
        response = model.generate_content([prompt, higher_img, lower_img])
        bot.send_message(chat_id, response.text)
        show_follow_up(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"Error: {str(e)}")
        show_follow_up(chat_id)

def show_follow_up(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔄 Same Timeframe", callback_data="loop_same"))
    markup.
    row(InlineKeyboardButton("⏱️ Other Timeframe", callback_data="loop_other"))
    bot.send_message(chat_id, "Do you have another trade setup?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("loop_"))
def handle_loop(call):
    chat_id = call.message.chat.id
    if call.data == "loop_same":
        if chat_id in user_data:
            user_data[chat_id]["images"] = []
            user_data[chat_id]["expected"] = "Higher"
            bot.send_message(chat_id, "Cleared. Please send the Higher timeframe chart:")
    elif call.data == "loop_other":
        show_timeframe_options(chat_id)

if name == "__main__":
    keep_alive()
    bot.infinity_polling()
