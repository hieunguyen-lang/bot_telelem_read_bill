from telegram.ext import Updater, MessageHandler, Filters
from io import BytesIO
import base64
from gemi_ai import GeminiBillAnalyzer
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os

load_dotenv()  # Tự động tìm và load từ .env
TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY = os.getenv("PROXY_URL")
GEMINI = os.getenv("GEMINI_API_KEY")
# Cấu hình quyền truy cập
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("your-creds.json", scope)
client = gspread.authorize(creds)
analyzer = GeminiBillAnalyzer()

def handle_photo(update, context):
    file = update.message.photo[-1].get_file()
    bio = BytesIO()
    file.download(out=bio)
    base64_str = base64.b64encode(bio.getvalue()).decode("utf-8")

    result = analyzer.analyze_bill(base64_str)
    row = [
        update.message.date.strftime("%Y-%m-%d %H:%M:%S"),
        update.message.from_user.full_name,
        result.get("ten_ngan_hang"),
        result.get("ten_don_vi_ban"),
        result.get("dia_chi_don_vi_ban"),
        result.get("ngay_giao_dich"),
        result.get("gio_giao_dich"),
        result.get("tong_so_tien"),
        result.get("don_vi_tien_te"),
        result.get("loai_the"),
        result.get("ma_giao_dich"),
        result.get("ma_don_vi_chap_nhan"),
        result.get("so_lo"),
        result.get("so_tham_chieu"),
        result.get("loai_giao_dich"),
        update.message.caption or ""
    ]
    # Mở file bằng ID
    sheet = client.open_by_key(GEMINI).sheet1
    sheet.insert_row([
        "Thời gian", "Người gửi", "Ngân hàng", "Đơn vị bán", "Địa chỉ",
        "Ngày GD", "Giờ GD", "Tổng tiền", "Tiền tệ", "Loại thẻ",
        "Mã GD", "Mã ĐV chấp nhận", "Số lô", "Tham chiếu", "Loại GD", "Ghi chú"
    ], index=1)
    # Ghi 1 dòng mới vào cuối sheet
    sheet.append_row(row)
    msg = (
        "📄 Kết quả trích xuất hóa đơn:\n\n"
        f"🏦 Ngân hàng       : {result.get('ten_ngan_hang') or 'Không rõ'}\n"
        f"🏪 Đơn vị bán      : {result.get('ten_don_vi_ban') or 'Không rõ'}\n"
        f"📍 Địa chỉ         : {result.get('dia_chi_don_vi_ban') or 'Không rõ'}\n"
        f"🗓️ Ngày giao dịch  : {result.get('ngay_giao_dich') or 'Không rõ'}\n"
        f"⏰ Giờ giao dịch   : {result.get('gio_giao_dich') or 'Không rõ'}\n"
        f"💰 Tổng tiền       : {result.get('tong_so_tien') or 'Không rõ'} {result.get('don_vi_tien_te') or ''}\n"
        f"💳 Loại thẻ        : {result.get('loai_the') or 'Không rõ'}\n"
        f"🆔 Mã giao dịch(TID)    : {result.get('ma_giao_dich') or 'Không rõ'}\n"
        f"🏷️ Mã đơn vị(MID) : {result.get('ma_don_vi_chap_nhan') or 'Không rõ'}\n"
        f"📦 Số lô           : {result.get('so_lo') or 'Không rõ'}\n"
        f"🔁 Số tham chiếu   : {result.get('so_tham_chieu') or 'Không rõ'}\n"
        f"🔄 Loại giao dịch  : {result.get('loai_giao_dich') or 'Không rõ'}"
    )

    update.message.reply_text(msg)


updater = Updater(
    token=TOKEN,
    request_kwargs={'proxy_url': PROXY}
)

dp = updater.dispatcher
dp.add_handler(MessageHandler(Filters.photo, handle_photo))

updater.start_polling()
updater.idle()
