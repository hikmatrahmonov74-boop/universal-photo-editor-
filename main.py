import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "Universal Photo Editor is running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Universal Photo Editor botiga xush kelibsiz!\n\n"
        "Rasm yoki skrinshot yuboring.\n"
        "Hozircha bot rasmlarni qabul qilishni sinovdan o'tkazmoqda."
    )

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Rasmingiz qabul qilindi! "
        "Keyingi versiyada rasmni tahrirlash funksiyalarini qo'shamiz."
    )

def run_bot():
    if not TOKEN:
        print("BOT_TOKEN topilmadi!")
        return

    bot = Application.builder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(filters.PHOTO, photo))
    bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
