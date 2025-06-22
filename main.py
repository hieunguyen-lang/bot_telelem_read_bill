from telegram.ext import Updater
from handlers.photo_handler import register_photo_handler
from handlers.menu_handler import register_menu_handlers 
import os
from utils.report_sender import send_daily_report
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import pytz
load_dotenv()  # Tự động tìm và load từ .env
updater = Updater(
    token=os.getenv("TELEGRAM_TOKEN"),
    request_kwargs={'proxy_url': os.getenv("PROXY_URL")}
)

bot = updater.bot
chat_id = int(os.getenv("GROUP_DAO_ID"))  # từ .env
# Khởi tạo scheduler và job
scheduler = BackgroundScheduler()
scheduler.add_job(
    send_daily_report,
    'cron',
    hour=9,
    minute=0,
    args=[bot, chat_id],
    timezone=pytz.timezone("Asia/Ho_Chi_Minh")
)
scheduler.start()

dp = updater.dispatcher

register_photo_handler(dp)
register_menu_handlers(dp)

updater.start_polling()
updater.idle()
