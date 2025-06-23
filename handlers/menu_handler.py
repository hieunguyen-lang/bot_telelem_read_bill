from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from mysql_db_connector import AsyncMySQLConnector
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

db = AsyncMySQLConnector(
    host="localhost",
    user='root',
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

async def start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📥 Nhận lệnh /menu")
    search_keyboard = [
        [
            InlineKeyboardButton("👤 Tên khách", callback_data='search_khach'),
            InlineKeyboardButton("📞 SĐT", callback_data='search_sdt')
        ],
        [
            InlineKeyboardButton("🧾 Số lô", callback_data='search_so_lo'),
            InlineKeyboardButton("🧾e Số hoá đơn", callback_data='search_so_hoa_don')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(search_keyboard)
    await update.message.reply_text("\ud83d\udd0e Chọn cách tra cứu:", reply_markup=reply_markup)

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mapping = {
        'search_khach': "🔎 Nhập tên khách cần tìm trong bảng:",
        'search_sdt': "🔎 Nhập SĐT cần tìm trong bảng:",
        'search_so_lo': "🔎 Nhập số lô cần tìm trong bảng:",
        'search_so_hoa_don': "🔎 Nhập số hóa đơn cần tìm:"
    }

    message = mapping.get(query.data)
    if message:
        await query.edit_message_text(message, parse_mode="Markdown")
        context.user_data['search_mode'] = query.data.replace("search_", "")

async def handle_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_mode = context.user_data.get("search_mode")
    keyword = update.message.text.strip()

    if not search_mode:
        await update.message.reply_text("❌ Bạn chưa chọn cách tra cứu. Dùng /menu trước.")
        return

    results = search_hoa_don_rut(db, search_mode, keyword)
    if not results:
        await update.message.reply_text(f"❌ Không tìm thấy kế quả cho: *{keyword}*", parse_mode="Markdown")
        return

    text = format_results(results)
    await update.message.reply_text(f" Kết quả:\n{text}", parse_mode="Markdown")

def search_hoa_don_rut(db, field_type, keyword):
    field_map = {
        "so_lo": "so_lo",
        "so_dien_thoai": "so_dien_thoai",
        "ten_khach": "ten_khach",
        "so_hoa_don": "so_hoa_don"
    }

    if field_type not in field_map:
        raise ValueError("\u274c Trường tìm kiếm không hợp lệ.")

    query = f"""
        SELECT * FROM thong_tin_hoa_don
        WHERE {field_map[field_type]} LIKE %s
        ORDER BY thoi_gian DESC
        LIMIT 10
    """
    values = [f"%{keyword}%"]
    return db.fetchall(query, values)

def format_results(results):
    lines = []
    for i, item in enumerate(results, 1):
        thoi_gian = item['thoi_gian'].strftime("%Y-%m-%d %H:%M:%S") if item['thoi_gian'] else "?"
        lines.append(
            f"*#{i} - {item['ten_khach']}*\n"
            f"🕒 {thoi_gian}\n"
            f"📞 {item['so_dien_thoai']}\n"
            f"📄 Lô: `{item['so_lo']}` | Số Hóa đơn: `{item['so_hoa_don']}`\n"
            "-----------------------------"
        )
    return "\n".join(lines)
async def register_menu_handlers(application):
    application.add_handler(CommandHandler("menu", start_menu))
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_search))
