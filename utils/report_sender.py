from telegram import Bot
from datetime import datetime,timedelta
import os
from data_connect.mysql_db_connector import MySQLConnector
import pytz
from helpers import helper 
db = MySQLConnector(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    port=os.getenv("MYSQL_ROOT_PORT"),
    database=os.getenv("MYSQL_DATABASE")
)
def send_long_message(bot, chat_id, text, parse_mode=None):
    MAX_LENGTH = 4096
    if len(text) <= MAX_LENGTH:
        bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    else:
        # Cắt thành nhiều đoạn
        while len(text) > 0:
            part = text[:MAX_LENGTH]
            # Cắt tại dấu xuống dòng gần nhất để tránh vỡ format Markdown
            last_newline = part.rfind('\n')
            if last_newline != -1:
                part = text[:last_newline]
                text = text[last_newline + 1:]
            else:
                text = text[MAX_LENGTH:]
            bot.send_message(chat_id=chat_id, text=part, parse_mode=parse_mode)

def send_daily_report(bot: Bot, chat_id: int):
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)
    tomorrow = now + timedelta(days=1)
    tomorrow_day = str(tomorrow.day)
    print(f"Đang gửi báo cáo hàng ngày cho ngày {tomorrow_day}...")
    query = """
        SELECT
            MAX(nguoi_gui) AS nguoi_gui,
            MAX(ten_khach) AS ten_khach,
            MAX(thoi_gian) AS thoi_gian,
            so_dien_thoai,
            sum(tong_so_tien) AS tong_tien
        FROM
            thong_tin_hoa_don
        WHERE
            lich_canh_bao = %s
        GROUP BY
            so_dien_thoai;

    """
    results = db.fetchall(query, (tomorrow_day,))
    print(results)
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
            f"🗓 Ngày GD: {row['thoi_gian']} - ☎ {row['so_dien_thoai']}\n"
            f"🗓 Tổng tiền đáo/rút: {helper.format_currency_vn(row['tong_tien'])} vnđ\n"
            "-------------------"
        )

    tomorrow_str = tomorrow.strftime('%d/%m/%Y')
    report = "\n".join(lines)
    final_message = (
        f"📆 *Lịch hẹn ngày mai ({tomorrow_str})*: "
        f"Dưới đây là danh sách khách có giao dịch đáo/rút bạn cần lưu ý:\n\n{report}"
    )

    send_long_message(bot, chat_id, final_message, parse_mode="Markdown")
