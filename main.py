
import os
import io
import threading
import asyncio
import httpx

from flask import Flask
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
POOF_API_KEY = os.getenv("POOF_API_KEY")
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
         InlineKeyboardButton("Asl rasm", callback_data="original")],
        [InlineKeyboardButton("AI: Fonni olib tashlash", callback_data="remove_bg")]
    ]
    await update.message.reply_text(
        "Tahrirlashni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = context.user_data.get("photo")
    if not data:
        await query.message.reply_text("Avval rasm yuboring.")
        return

    action = query.data

    if action == "remove_bg":
        if not POOF_API_KEY:
            await query.message.reply_text("Poof API kaliti sozlanmagan.")
            return

        status = await query.message.reply_text(
            "AI fonni olib tashlayapti. Kuting..."
        )

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(
                    "https://api.poof.bg/v1/remove",
                    headers={"x-api-key": POOF_API_KEY},
                    files={"file": ("photo.jpg", data, "image/jpeg")}
                )

            if response.status_code != 200:
                await status.edit_text(
                    f"AI xatosi: {response.status_code}. Qayta urinib ko'ring."
                )
                return

            output = io.BytesIO(response.content)
            output.name = "fon-siz.png"
            output.seek(0)

            await query.message.reply_document(
                document=output,
                filename="fon-siz.png",
                caption="Tayyor! Rasm foni olib tashlandi."
            )
            await status.delete()

        except Exception:
            await status.edit_text(
                "Xatolik yuz berdi. Keyinroq qayta urinib ko'ring."
            )
        return

    image = Image.open(io.BytesIO(data)).convert("RGB")

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
        target=lambda: web.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 10000))
        ),
        daemon=True
    ).start()
    asyncio.run(bot())
