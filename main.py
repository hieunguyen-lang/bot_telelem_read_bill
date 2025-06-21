from telegram.ext import Updater
from handlers.photo_handler import register_photo_handler
from handlers.menu_handler import register_menu_handlers
import os

updater = Updater(
    token=os.getenv("TELEGRAM_TOKEN"),
    request_kwargs={'proxy_url': os.getenv("PROXY_URL")}
)

dp = updater.dispatcher

register_photo_handler(dp)
register_menu_handlers(dp)

updater.start_polling()
updater.idle()
