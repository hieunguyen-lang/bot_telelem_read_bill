from telegram import Bot
from datetime import datetime
import os
from mysql_db_connector import MySQLConnector
db = MySQLConnector(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)
def send_daily_report(bot: Bot, chat_id: int):
    query = """
        SELECT thoi_gian, ten_khach, so_dien_thoai, so_tien_rut, so_tien_chuyen_khoan, ngan_hang
        FROM thong_tin_hoa_don_rut
        ORDER BY thoi_gian DESC
        LIMIT 10
    """
    results = db.fetchall(query)

    if not results:
        bot.send_message(chat_id=chat_id, text="📉 Không có dữ liệu giao dịch gần đây.")
        return

    lines = []
    for i, row in enumerate(results, 1):
        tg = row["thoi_gian"].strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"*#{i} - {row['ten_khach']}*\n"
            f"🕒 {tg} | ☎ {row['so_dien_thoai']}\n"
            f"💰 Rút: `{row['so_tien_rut']}` | CK: `{row['so_tien_chuyen_khoan']}`\n"
            f"🏦 {row['ngan_hang']}\n"
            "-------------------"
        )

    report = "\n".join(lines)
    bot.send_message(chat_id=chat_id, text=f"📊 *Báo cáo giao dịch mới nhất:*\n\n{report}", parse_mode="Markdown")
