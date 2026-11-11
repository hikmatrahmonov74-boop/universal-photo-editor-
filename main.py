
import os
import io
import threading
import asyncio

from flask import Flask
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
web = Flask(__name__)

@web.route("/")
def home():
    return "Photo Editor ishlayapti!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Rasm yuboring.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    data = bytes(await file.download_as_bytearray())
    context.user_data["photo"] = data

    keyboard = [
        [InlineKeyboardButton("Aylantirish", callback_data="rotate"),
         InlineKeyboardButton("Akslantirish", callback_data="mirror")],
        [InlineKeyboardButton("Oq-qora", callback_data="gray"),
         InlineKeyboardButton("Tiniqlashtirish", callback_data="sharp")],
        [InlineKeyboardButton("Yorqinlik", callback_data="bright"),
         InlineKeyboardButton("Asl rasm", callback_data="original")]
    ]
    await update.message.reply_text("Tahrirlashni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("photo")
    if not data:
        await query.message.reply_text("Avval rasm yuboring.")
        return

    image = Image.open(io.BytesIO(data)).convert("RGB")
    action = query.data

    if action == "rotate":
        image = image.rotate(90, expand=True)
    elif action == "mirror":
        image = ImageOps.mirror(image)
    elif action == "gray":
        image = ImageOps.grayscale(image)
    elif action == "sharp":
        image = image.filter(ImageFilter.SHARPEN)
    elif action == "bright":
        image = ImageEnhance.Brightness(image).enhance(1.2)

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    output.seek(0)
    await query.message.reply_photo(photo=output, caption="Tayyor!")

async def bot():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan!")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(edit_photo))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    threading.Thread(
        target=lambda: web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))),
        daemon=True
    ).start()
    asyncio.run(bot())
