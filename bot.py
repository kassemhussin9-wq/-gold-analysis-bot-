قم بتحليل الفريمين معاً ميكانيكياً وصياغة الرد باللغة العربية تماماً متضمناً جزأين:
        
        1. التوصية المختصرة (تظهر فوراً) وتتضمن إشارات بيع أو شراء واضحة جداً مع استخدام هذه الإيموجيات حصراً بناء على معطيات الشارت: (📈🔻 للبيع، 🟢🟢🟢📉 للشراء، ❌❌❌ للستوب لوز، 🎯 للأهداف). مع الالتزام بنسبة مخاطرة إلى عائد 1:3 ميكانيكياً.
        2. التحليل العميق والشامل بصيغة قالب "تحليل الذهب - EXODUS AI" لعام 2026 بتوقيت أبوظبي، ويتضمن الخلاصة التنفيذية (الاتجاه، الزخم، السيولة، التوافق)، المناطق المهمة (الدعوم والمقاومات الأقرب والتالية)، السيناريو الإيجابي والضاغط، وسبب الترجيح الفني المفصل بناء على مستويات الفير فاليو جاب (FVG)، والسيولة ومناطق كسر البنية الفنية.
        """
        
        response = model.generate_content([prompt, higher_img, lower_img])
        analysis_text = response.text
        
        # إرسال التقرير والتحليل الفني للمستخدم
        bot.send_message(chat_id, analysis_text)
        
        # إظهار سؤال المتابعة والأزرار التفاعلية النهائية للـ Loop التلقائي
        show_follow_up(chat_id)
        
    except Exception as e:
        # نظام الفولباك التلقائي للموديل الآخر في حال الضغط الميكانيكي على الحصة اليومية
        try:
            model_fallback = genai.GenerativeModel('gemini-1.5-flash')
            response = model_fallback.generate_content([prompt, higher_img, lower_img])
            bot.send_message(chat_id, response.text)
            show_follow_up(chat_id)
        except:
            bot.send_message(chat_id, "عذراً، تعذّر معالجة الصور حالياً بسبب ضغط الطلبات. أعد الإرسال بعد قليل. 🔄")

def show_follow_up(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔄 نفس الإطار الزمني", callback_data="loop_same"))
    markup.row(InlineKeyboardButton("⏱️ إطار زمني آخر", callback_data="loop_other"))
    bot.send_message(chat_id, "هل لديك صفقة أخرى جاهزة للقنص؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("loop_"))
def handle_loop(call):
    chat_id = call.message.chat.id
    if call.data == "loop_same":
        if chat_id in user_data:
            user_data[chat_id]["images"] = []
            user_data[chat_id]["expected"] = "Higher"
            bot.send_message(chat_id, "تم تصفير الذاكرة للإطار الحالي بنجاح. أرسل صورة الفريم الكبير فوراً لقنص صفقة جديدة:")
    elif call.data == "loop_other":
        show_timeframe_options(chat_id)

if name == "__main__":
    # استدعاء دالة الـ Keep-Alive لتجهيز السيرفر للعمل 24/7 دون توقف
    keep_alive()
    bot.infinity_polling()
