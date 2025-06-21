from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters

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

def handle_text_search(update, context):
    search_mode = context.user_data.get("search_mode")
    keyword = update.message.text.strip()

    if not search_mode:
        update.message.reply_text("❌ Bạn chưa chọn cách tra cứu. Dùng /menu trước.")
        return

    # Ví dụ giả lập kết quả
    if search_mode == "khach":
        update.message.reply_text(f"🔎 Đang tìm theo tên khách: *{keyword}*", parse_mode="Markdown")
        # TODO: Truy vấn database, trả kết quả thật
    elif search_mode == "stk":
        update.message.reply_text(f"🔎 Đang tìm theo STK: *{keyword}*", parse_mode="Markdown")

def register_menu_handlers(dp):
    dp.add_handler(CommandHandler("menu", start_menu))
    dp.add_handler(CallbackQueryHandler(handle_button_click))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_search))
