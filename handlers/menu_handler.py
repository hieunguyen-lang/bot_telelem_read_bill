from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from mysql_db_connector import MySQLConnector
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
db = MySQLConnector(
    host="localhost",
    user='root',
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)
def start_menu(update, context):
    print("📥 Nhận lệnh /menu")
    keyboard = [
        [InlineKeyboardButton("📄 Bảng Đáo", callback_data='select_table_dao')],
        [InlineKeyboardButton("💸 Bảng Rút", callback_data='select_table_rut')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📌 Bạn muốn tra cứu trong bảng nào?", reply_markup=reply_markup)

def handle_button_click(update, context):
    query = update.callback_query
    query.answer()

    # Xử lý chọn bảng
    if query.data == 'select_table_dao':
        context.user_data['table_selected'] = 'dao'
        search_keyboard = [
            [
                InlineKeyboardButton("👤 Tên khách", callback_data='search_khach'),
                InlineKeyboardButton("🏦 STK", callback_data='search_stk')
            ],
            [
                InlineKeyboardButton("📞 SĐT", callback_data='search_sdt'),
                InlineKeyboardButton("🧾 Số lô", callback_data='search_so_lo')
            ],
            [
                InlineKeyboardButton("🔍 Tham chiếu", callback_data='search_tham_chieu')
            ]
        ]
        query.edit_message_text("📄 Đã chọn bảng **Đáo**.\nChọn cách tra cứu:", reply_markup=InlineKeyboardMarkup(search_keyboard), parse_mode="Markdown")

    elif query.data == 'select_table_rut':
        context.user_data['table_selected'] = 'rut'
        search_keyboard = [
            [
                InlineKeyboardButton("👤 Tên khách", callback_data='search_khach'),
                InlineKeyboardButton("🏦 STK", callback_data='search_stk')
            ],
            [
                InlineKeyboardButton("📞 SĐT", callback_data='search_sdt'),
                InlineKeyboardButton("🧾 Số lô", callback_data='search_so_lo')
            ],
            [
                InlineKeyboardButton("🔍 Tham chiếu", callback_data='search_tham_chieu')
            ]
        ]

        query.edit_message_text("💸 Đã chọn bảng **Rút**.\nChọn cách tra cứu:", reply_markup=InlineKeyboardMarkup(search_keyboard), parse_mode="Markdown")

    # Xử lý chọn kiểu tra cứu
    elif query.data == 'search_khach':
        table = context.user_data.get('table_selected')
        if not table:
            query.edit_message_text("⚠️ Bạn chưa chọn bảng dữ liệu.")
            return
        query.edit_message_text(f"🔎 Nhập tên khách cần tìm trong bảng `{table.upper()}`:", parse_mode="Markdown")
        context.user_data['search_mode'] = 'khach'

    elif query.data == 'search_stk':
        table = context.user_data.get('table_selected')
        if not table:
            query.edit_message_text("⚠️ Bạn chưa chọn bảng dữ liệu.")
            return
        query.edit_message_text(f"🔎 Nhập STK cần tìm trong bảng `{table.upper()}`:", parse_mode="Markdown")
        context.user_data['search_mode'] = 'stk'

    # Xử lý chọn kiểu tra cứu
    elif query.data == 'search_sdt':
        table = context.user_data.get('table_selected')
        if not table:
            query.edit_message_text("⚠️ Bạn chưa chọn bảng dữ liệu.")
            return
        query.edit_message_text(f"🔎 Nhập SĐT cần tìm trong bảng `{table.upper()}`:", parse_mode="Markdown")
        context.user_data['search_mode'] = 'sdt'

    elif query.data == 'search_so_lo':
        table = context.user_data.get('table_selected')
        if not table:
            query.edit_message_text("⚠️ Bạn chưa chọn bảng dữ liệu.")
            return
        query.edit_message_text(f"🔎 Nhập số lô cần tìm trong bảng `{table.upper()}`:", parse_mode="Markdown")
        context.user_data['search_mode'] = 'so_lo'
        
    # Xử lý chọn kiểu tra cứu
    elif query.data == 'search_tham_chieu':
        table = context.user_data.get('table_selected')
        if not table:
            query.edit_message_text("⚠️ Bạn chưa chọn bảng dữ liệu.")
            return
        query.edit_message_text(f"🔎 Nhập tham chiếu cần tìm trong bảng `{table.upper()}`:", parse_mode="Markdown")
        context.user_data['search_mode'] = 'tham_chieu'

def handle_text_search(update, context):
    search_mode = context.user_data.get("search_mode")
    keyword = update.message.text.strip()

    if not search_mode:
        update.message.reply_text("❌ Bạn chưa chọn cách tra cứu. Dùng /menu trước.")
        return

    # Ví dụ giả lập kết quả
    if search_mode == "khach":
        results = search_hoa_don_rut(db, "ten_khach", keyword)
        if not results:
            update.message.reply_text(f"❌ Không tìm thấy kết quả cho: *{keyword}*", parse_mode="Markdown")
            return
        print(results)
        text = format_results(results)
        update.message.reply_text(f"📋 Kết quả:\n{text}", parse_mode="Markdown")
        # TODO: Truy vấn database, trả kết quả thật
    elif search_mode == "stk":
        results = search_hoa_don_rut(db, "so_tai_khoan", keyword)
        if not results:
            update.message.reply_text(f"❌ Không tìm thấy kết quả cho: *{keyword}*", parse_mode="Markdown")
            return
        text = format_results(results)
        update.message.reply_text(f"📋 Kết quả:\n{text}", parse_mode="Markdown")
    elif search_mode == "sdt":
        results = search_hoa_don_rut(db, "so_dien_thoai", keyword)
        if not results:
            update.message.reply_text(f"❌ Không tìm thấy kết quả cho: *{keyword}*", parse_mode="Markdown")
            return
        text = format_results(results)
        update.message.reply_text(f"📋 Kết quả:\n{text}", parse_mode="Markdown")
    elif search_mode == "so_lo":
        results = search_hoa_don_rut(db, "so_lo", keyword)
        if not results:
            update.message.reply_text(f"❌ Không tìm thấy kết quả cho: *{keyword}*", parse_mode="Markdown")
            return
        text = format_results(results)
        update.message.reply_text(f"📋 Kết quả:\n{text}", parse_mode="Markdown")
    elif search_mode == "tham_chieu":
        results = search_hoa_don_rut(db, "so_tham_chieu", keyword)
        if not results:
            update.message.reply_text(f"❌ Không tìm thấy kết quả cho: *{keyword}*", parse_mode="Markdown")
            return
        text = format_results(results)
        update.message.reply_text(f"📋 Kết quả:\n{text}", parse_mode="Markdown")

def search_hoa_don_rut(db, field_type, keyword):
    """
    Tìm kiếm hóa đơn rút theo các trường:
    so_lo, so_tai_khoan, so_dien_thoai, ten_khach, so_tham_chieu
    """
    field_map = {
        "so_lo": "so_lo",
        "so_tai_khoan": "so_tai_khoan",
        "so_dien_thoai": "so_dien_thoai",
        "ten_khach": "ten_khach",
        "so_tham_chieu": "so_tham_chieu"
    }

    if field_type not in field_map:
        raise ValueError("❌ Trường tìm kiếm không hợp lệ.")

    query = f"""
        SELECT * FROM thong_tin_hoa_don_rut
        WHERE {field_map[field_type]} LIKE %s
        ORDER BY thoi_gian DESC
        LIMIT 10
    """
    values = [f"%{keyword}%"]

    return db.fetchall(query, values)

def format_results(results):
    if not results:
        return "❌ Không tìm thấy kết quả nào."

    lines = []
    for i, item in enumerate(results, 1):
        thoi_gian = item['thoi_gian'].strftime("%Y-%m-%d %H:%M:%S") if item['thoi_gian'] else "?"
        don_vi_ban = item.get('don_vi_ban') or "Không rõ"
        lines.append(
            f"*#{i} - {item['ten_khach']}*\n"
            f"🕒 {thoi_gian}\n"
            f"📞 {item['so_dien_thoai']}\n"
            f"💵 Rút: `{item['so_tien_rut']}` | CK: `{item['so_tien_chuyen_khoan']}`\n"
            f"🏦 {item['ngan_hang']} - {don_vi_ban}\n"
            f"📄 Mã GD: `{item['ma_giao_dich']}` | Lô: `{item['so_lo']}` | TC: `{item['so_tham_chieu']}`\n"
            f"📝 {item['ghi_chu']}\n"
            "-----------------------------"
        )

    return "\n".join(lines)
def register_menu_handlers(dp):
    dp.add_handler(CommandHandler("menu", start_menu))
    dp.add_handler(CallbackQueryHandler(handle_button_click))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_search))
