from telegram.ext import MessageHandler, filters
from core import handle_photo

async def register_photo_handler(application):
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)
    application.add_handler(photo_handler)