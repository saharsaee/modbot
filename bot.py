from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import datetime
import os
from groq import Groq

TOKEN = os.environ.get("TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

QUESTIONS = [
    ("mood", "امروز از ۱ تا ۱۰ چه حسی داری؟"),
    ("energy", "امروز چقدر انرژی داری؟", [["کم", "متوسط", "زیاد"]]),
    ("sleep", "امشب چقدر خوابیدی؟ (ساعت)"),
    ("good_thing", "امروز یه چیز خوب که اتفاق افتاد چی بود؟"),
    ("feeling", "الان بیشتر چه حسی داری؟", [["اضطراب", "غم", "خستگی", "خوبم"]]),
]

def save_data(user_id, answers):
    try:
        with open("scores.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    today = str(datetime.date.today())
    if str(user_id) not in data:
        data[str(user_id)] = {}
    data[str(user_id)][today] = answers
    with open("scores.json", "w") as f:
        json.dump(data, f, ensure_ascii=False)

def get_ai_response(answers):
    summary = f"""
    حال کلی: {answers.get('mood')}/10
    انرژی: {answers.get('energy')}
    خواب: {answers.get('sleep')} ساعت
    چیز خوب: {answers.get('good_thing')}
    احساس: {answers.get('feeling')}
    """
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": "تو یه دستیار مهربان فارسی‌زبان هستی که به آدم‌ها کمک می‌کنی حالشون بهتر بشه. بر اساس اطلاعات روز، یه پیام کوتاه و دلگرم‌کننده بده."
            },
            {
                "role": "user",
                "content": summary
            }
        ]
    )
    return response.choices[0].message.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.from_user.first_name
    await update.message.reply_text(
        f"سلام {name}! 🌱\nمن هر روز ازت می‌پرسم حالت چطوره.\nبرای شروع بنویس /check"
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['step'] = 0
    context.user_data['answers'] = {}
    await ask_question(update, context)

async def ask_question(update, context):
    step = context.user_data['step']
    q = QUESTIONS[step]
    
    if len(q) == 3:
        keyboard = ReplyKeyboardMarkup(q[2], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(q[1], reply_markup=keyboard)
    else:
        await update.message.reply_text(q[1], reply_markup=ReplyKeyboardRemove())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'step' not in context.user_data:
        return
    
    step = context.user_data['step']
    answer = update.message.text
    key = QUESTIONS[step][0]
    context.user_data['answers'][key] = answer
    context.user_data['step'] += 1
    
    if context.user_data['step'] < len(QUESTIONS):
        await ask_question(update, context)
    else:
        answers = context.user_data['answers']
        save_data(update.message.from_user.id, answers)
        await update.message.reply_text("داره فکر می‌کنه... 🤔", reply_markup=ReplyKeyboardRemove())
        ai_response = get_ai_response(answers)
        await update.message.reply_text(f"✅ ثبت شد!\n\n{ai_response}")
        context.user_data.clear()

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("ربات شروع کرد...")
app.run_polling()
