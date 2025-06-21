from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def show_main_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🔍 Tra cứu theo tên khách", callback_data='search_khach')],
        [InlineKeyboardButton("🔍 Tra cứu theo STK", callback_data='search_stk')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("📋 Vui lòng chọn cách tra cứu:", reply_markup=reply_markup)

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    if query.data == "search_khach":
        context.user_data["search_mode"] = "khach"
        query.edit_message_text("📝 Nhập *tên khách* cần tra cứu:", parse_mode="Markdown")
    elif query.data == "search_stk":
        context.user_data["search_mode"] = "stk"
        query.edit_message_text("📝 Nhập *số tài khoản* cần tra cứu:", parse_mode="Markdown")

def handle_text_search(update, context):
    search_mode = context.user_data.get("search_mode")
    text = update.message.text.strip()

    if not search_mode:
        update.message.reply_text("⚠️ Vui lòng chọn mục tra cứu bằng lệnh /menu trước.")
        return

    # Tùy theo search_mode, truy vấn database
    if search_mode == "khach":
        # TODO: Truy vấn MySQL theo tên khách
        update.message.reply_text(f"🔍 Kết quả tìm theo khách: *{text}*", parse_mode="Markdown")
    elif search_mode == "stk":
        # TODO: Truy vấn MySQL theo STK
        update.message.reply_text(f"🔍 Kết quả tìm theo STK: *{text}*", parse_mode="Markdown")
