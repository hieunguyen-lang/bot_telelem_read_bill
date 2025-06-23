from telegram.ext import Application, ApplicationBuilder
from handlers.photo_handler import register_photo_handler
from handlers.menu_handler import register_menu_handlers 
from utils.report_sender import send_daily_report
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
import pytz

load_dotenv()  # Load config từ file .env

# Khởi tạo bot application (v20+)
application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).proxy_url(os.getenv("PROXY_URL")).build()

bot = application.bot
chat_ids = [
    int(os.getenv("GROUP_DAO_ID")),
    int(os.getenv("GROUP_RUT_ID", 0))  # Thêm group khác nếu có
]

# Lên lịch gửi báo cáo mỗi ngày
scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: [send_daily_report(bot, chat_id) for chat_id in chat_ids],
    'cron',
    hour=9,
    minute=0,
    timezone=pytz.timezone("Asia/Ho_Chi_Minh")
)
scheduler.start()

# Đăng ký các handler
register_photo_handler(application)
register_menu_handlers(application)

# Bắt đầu bot
application.run_polling()
