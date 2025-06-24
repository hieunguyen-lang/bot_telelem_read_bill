from telegram import Bot
from datetime import datetime,timedelta
import os
from mysql_db_connector import MySQLConnector
import pytz
db = MySQLConnector(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    port=os.getenv("MYSQL_ROOT_PORT"),
    database=os.getenv("MYSQL_DATABASE")
)

def send_daily_report(bot: Bot, chat_id: int):
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)
    tomorrow = now + timedelta(days=1)
    tomorrow_day = str(tomorrow.day)
    print(f"Đang gửi báo cáo hàng ngày cho ngày {tomorrow_day}...")
    query = """
        SELECT nguoi_gui, ten_khach, ngay_giao_dich, so_dien_thoai
        FROM thong_tin_hoa_don
        WHERE lich_canh_bao = %s
    """
    results = db.fetchall(query, (tomorrow_day,))

    if not results:
        bot.send_message(
            chat_id=chat_id,
            text="✅ Hiện tại chưa có khách nào có lịch đáo/rút vào *ngày mai*. Bạn có thể yên tâm nghỉ ngơi nhé 😊",
            parse_mode="Markdown"
        )
        return

    lines = []
    for i, row in enumerate(results, 1):
        lines.append(
            f"*#{i} - {row['ten_khach']}*\n"
            f"👤 Gửi bởi: @{row['nguoi_gui']}\n"
            f"🗓 Ngày GD: {row['ngay_giao_dich']} | ☎ {row['so_dien_thoai']}\n"
            "-------------------"
        )

    tomorrow_str = tomorrow.strftime('%d/%m/%Y')
    report = "\n".join(lines)

    bot.send_message(
        chat_id=chat_id,
        text=f"📆 *Lịch hẹn ngày mai ({tomorrow_str})*: Dưới đây là danh sách khách có giao dịch đáo/rút bạn cần lưu ý:\n\n" + report,
        parse_mode="Markdown"
    )