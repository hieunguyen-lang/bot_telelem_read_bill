from telegram.ext import MessageHandler, Filters,CommandHandler
from core.momo_core import handle_photo

def register_momo_handler(dp):
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
