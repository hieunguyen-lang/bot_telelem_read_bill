from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from mysql_db_connector import MySQLConnector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Kết nối DB
db = MySQLConnector(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

# Bắt đầu menu tra cứu
def start_menu_hh(update: Update, context: CallbackContext):
    print("📥 Nhận lệnh /menu")
    
    search_keyboard = [[
        InlineKeyboardButton("👤 Tổng hợp hoa hồng của bạn", callback_data='hoahong_self')
    ]]
    reply_markup = InlineKeyboardMarkup(search_keyboard)

    update.message.reply_text("🔎 Chọn cách tra cứu:", reply_markup=reply_markup)

# Xử lý khi nhấn nút
def handle_button_click_hoahong(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    print("📲 Callback nhận được:", query.data)

    if query.data == 'hoahong_self':
        username = query.from_user.username

        now = datetime.now()

        time_ranges = {
            "1 tháng": now - timedelta(days=30),
            "3 tháng": now - timedelta(days=90),
            "6 tháng": now - timedelta(days=180),
            "1 năm": now - timedelta(days=365),
        }

        reply_lines = [f"📊 *Tổng hoa hồng của* `{username}`:\n"]

        for label, from_date in time_ranges.items():
            tong = search_hoa_hong_theo_thoi_gian(db, username, from_date, now)
            reply_lines.append(f"• {label}: `{tong:,.0f}` đ")

        query.message.reply_text("\n".join(reply_lines), parse_mode="Markdown")


# Truy vấn DB
def search_hoa_hong_theo_thoi_gian(db, nguoi_gui, from_date, to_date):
    """
    Tổng hợp MAX(tong_so_tien) mỗi so_lo trong khoảng thời gian và tính tổng
    """
    query = """
        SELECT SUM(tong_tien_theo_lo) AS tong_hoa_hong
        FROM (
            SELECT MAX(tong_so_tien) AS tong_tien_theo_lo
            FROM thong_tin_hoa_don
            WHERE nguoi_gui = %s AND thoi_gian BETWEEN %s AND %s
            GROUP BY so_lo
        ) AS tong_theo_lo
    """
    result = db.fetchone(query, [nguoi_gui, from_date, to_date])
    return result["tong_hoa_hong"] if result and result["tong_hoa_hong"] else 0


# Đăng ký handler với Dispatcher
def register_hoahong_handlers(dp):
    dp.add_handler(CommandHandler("hoahong", start_menu_hh))
    dp.add_handler(CallbackQueryHandler(handle_button_click_hoahong, pattern='^hoahong_'))
