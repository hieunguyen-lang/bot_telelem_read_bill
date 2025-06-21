from telegram.ext import MessageHandler, Filters
from core import handle_photo

def register_photo_handler(dp):
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
