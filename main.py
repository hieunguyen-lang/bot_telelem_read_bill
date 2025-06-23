import os
import asyncio
import pytz
from dotenv import load_dotenv

from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest

from handlers.photo_handler import register_photo_handler
from handlers.menu_handler import register_menu_handlers
from utils.report_sender import send_daily_report
from apscheduler.schedulers.background import BackgroundScheduler


load_dotenv()

async def main():
    proxy = os.getenv("PROXY_URL")
    request = HTTPXRequest(proxy=proxy) if proxy else HTTPXRequest()

    application = (
        ApplicationBuilder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .request(request)
        .build()
    )

    # ✅ Fix lỗi timezone cho JobQueue nội bộ của telegram
    application.job_queue.scheduler.configure(timezone=pytz.timezone("Asia/Ho_Chi_Minh"))

    bot = application.bot
    chat_ids = [
        int(os.getenv("GROUP_DAO_ID")),
        int(os.getenv("GROUP_RUT_ID", 0))
    ]

    # ✅ Scheduler ngoài để gửi báo cáo (riêng, không phụ thuộc JobQueue)
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Ho_Chi_Minh"))
    scheduler.add_job(
        lambda: [send_daily_report(bot, chat_id) for chat_id in chat_ids],
        'cron',
        hour=9,
        minute=0,
    )
    scheduler.start()

    # ✅ Gọi handler async phải dùng await
    await register_photo_handler(application)
    await register_menu_handlers(application)

    # ✅ Chạy polling
    await application.run_polling()

if __name__ == "__main__":
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except RuntimeError:  # fallback cho Windows hoặc môi trường đã có loop
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(main())
