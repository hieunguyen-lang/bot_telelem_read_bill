from telegram.ext import Updater
from handlers.menu_handler import register_menu_handlers 
from handlers.cal_comission import register_hoahong_handlers
from handlers.share_group_handler import share_handler
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
chat_id_dao = int(os.getenv("GROUP_THONG_BAO"))  # từ .env

# Khởi tạo scheduler và job
scheduler = BackgroundScheduler()
scheduler.add_job(
    send_daily_report,
    'interval',
    minutes=360,
    args=[bot, chat_id_dao],
    timezone=pytz.timezone("Asia/Ho_Chi_Minh")  # vẫn cần pytz
)
scheduler.start()

dp = updater.dispatcher
share_handler(dp)
register_menu_handlers(dp)
register_hoahong_handlers(dp)

updater.start_polling()
updater.idle()
