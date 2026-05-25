from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import datetime
from groq import Groq

import os
TOKEN = os.environ.get("TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY ")


groq_client = Groq(api_key=GROQ_API_KEY)

def save_score(user_id, score):
    try:
        with open("scores.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    today = str(datetime.date.today())
    if str(user_id) not in data:
        data[str(user_id)] = {}
    
    data[str(user_id)][today] = score
    
    with open("scores.json", "w") as f:
        json.dump(data, f)

def get_ai_response(score):
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": "تو یه دستیار مهربان فارسی‌زبان هستی که به آدم‌ها کمک می‌کنی حالشون بهتر بشه. کوتاه و صمیمی جواب بده."
            },
            {
                "role": "user",
                "content": f"امروز حالم از ۱ تا ۱۰ عدد {score} هست. یه پیام کوتاه و دلگرم‌کننده بده."
            }
        ]
    )
    return response.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 🌱\nمن هر روز ازت می‌پرسم حالت چطوره.\nبرای شروع بنویس /check"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['waiting'] = True
    await update.message.reply_text("امروز از ۱ تا ۱۰ چه حسی داری؟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting'):
        score = update.message.text
        user_id = update.message.from_user.id
        save_score(user_id, score)
        
        await update.message.reply_text("داره فکر می‌کنه... 🤔")
        ai_response = get_ai_response(score)
        
        await update.message.reply_text(f"امتیاز امروزت: {score}\n\n{ai_response}")
        context.user_data['waiting'] = False

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("ربات شروع کرد...")
app.run_polling()