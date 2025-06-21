from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from io import BytesIO
import base64
from gemi_ai import GeminiBillAnalyzer
import json
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import threading
import os
from dotenv import load_dotenv
load_dotenv()  # Tự động tìm và load từ .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ID của các group
GROUP_DAO_ID = os.getenv("GROUP_DAO_ID")  # ID của group DAO
GROUP_RUT_ID = os.getenv("GROUP_RUT_ID")  # ID của group Rút tiền
# ID của các Google Sheet
SHEET_DAO_ID = os.getenv("SHEET_DAO_ID")  # ID của Google Sheet cho group DAO
SHEET_RUT_ID = os.getenv("SHEET_RUT_ID")  # ID của Google Sheet cho group Rút tiền
# Cấu hình quyền truy cập
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("your-creds.json", scope)
client = gspread.authorize(creds)
print("🔑 GEMINI_API_KEY:", repr(GEMINI_API_KEY))
analyzer = GeminiBillAnalyzer(api_key=GEMINI_API_KEY)
media_group_storage = {}

def validate_caption(update,chat_id, caption):
    if not caption:
        return None, "❌ Không tìm thấy nội dung để xử lý. Vui lòng thêm caption cho ảnh."

    if str(chat_id) == GROUP_DAO_ID:
        parsed = parse_message_dao(caption)
        if 'dao' not in parsed:
            update.message.reply_text(
                "❌ Đây là group Đáo, vui lòng chỉ gửi thông tin **Đáo** theo đúng định dạng sau:\n\n"
                "🔹 *Khách:* Tên người đáo\n"
                "🔹 *Sdt:* Số điện thoại\n"
                "🔹 *Dao:* Số tiền đáo (ví dụ: 37tr710)\n"
                "🔹 *Phi:* Phí phần trăm (ví dụ: 2%)\n"
                "🔹 *TienPhi:* Số tiền phí (ví dụ: 750K)\n"
                "🔹 *RutThieu:* Số tiền rút thiếu (ví dụ: 20K)\n"
                "🔹 *Tong:* Tổng (ví dụ: 754K)\n"
                "🔹 *LichCanhBao:* Số lịch cần báo\n"
                "🔹 *Note:* Ghi chú thêm (nếu có)\n\n"
                "📌 Ví dụ:\n"
                "`Khach: Đặng Huỳnh Duyệt`\n"
                "`Sdt: 0969963324`\n"
                "`Dao: 37tr710`\n"
                "`Phi: 2%`\n"
                "`TienPhi: 750K`\n"
                "`RutThieu: 20K`\n"
                "`Tong: 754K`\n"
                "`LichCanhBao: 21`\n"
                "`Note: Chuyển khoản hộ em với`",
                parse_mode="Markdown"
            )
            return None
        return parsed, None

    elif str(chat_id) == GROUP_RUT_ID:
        parsed = parse_message_rut(caption)
        if 'rut' not in parsed:
            update.message.reply_text(
                "❌ Đây là group Rút, vui lòng chỉ gửi thông tin **rút tiền** theo đúng định dạng sau:\n\n"
                "🔹 *Khách:* Tên người rút\n"
                "🔹 *Sdt:* Số điện thoại\n"
                "🔹 *Rut:* Số tiền rút (ví dụ: 19tr990)\n"
                "🔹 *Phi:* Phí phần trăm (ví dụ: 2%)\n"
                "🔹 *TienPhi:* Số tiền phí (ví dụ: 400k)\n"
                "🔹 *ChuyenKhoan:* Số tiền chuyển khoản sau phí\n"
                "🔹 *LichCanhBao:* Số lịch cần báo\n"
                "🔹 *Note:* Ghi chú thêm (nếu có)\n\n"
                "📌 Ví dụ:\n"
                "`Khach: Đặng Huỳnh Duyệt`\n"
                "`Sdt: 0969963324`\n"
                "`Rut: 19tr990`\n"
                "`Phi: 2%`\n"
                "`TienPhi: 400k`\n"
                "`ChuyenKhoan: 19tr590`\n"
                "`LichCanhBao: 21`\n"
                "`Note: Chuyển khoản hộ em với`",
                parse_mode="Markdown"
            )
            return None
        return parsed, None

    return {}, None

def handle_photo(update, context):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    print(f"Ảnh gửi từ group {chat_title} (ID: {chat_id})")
    message = update.message
    media_group_id = message.media_group_id or f"single_{message.message_id}"
    user_id = message.from_user.id

    # Tải ảnh trước (phải làm trước khi xử lý ảnh đơn)
    file = message.photo[-1].get_file()
    bio = BytesIO()
    file.download(out=bio)
    img_b64 = base64.b64encode(bio.getvalue()).decode("utf-8")
    
    
    # 👉 Ảnh đơn → gán trực tiếp thành list
    if message.media_group_id is None:
        parsed, error_msg = validate_caption(update,chat_id, message.caption)
        if error_msg:
            update.message.reply_text(error_msg, parse_mode="Markdown")
            return

        context.user_data["image_data"] = [img_b64]
        context.user_data["caption"] = parsed
        # Gọi xử lý luôn (giả sử luôn là hóa đơn)
        if str(chat_id) == GROUP_DAO_ID:
           
            handle_selection_dao(update, context, selected_type="bill")
            
        elif str(chat_id) == GROUP_RUT_ID:
        
            handle_selection_rut(update, context, selected_type="bill")

        return
    
    if media_group_id not in media_group_storage:
        # Ảnh đầu tiên của media group → parse caption luôn
        parsed, error_msg = validate_caption(update, chat_id, message.caption)
        if error_msg:
            update.message.reply_text(error_msg, parse_mode="Markdown")
            return

        media_group_storage[media_group_id] = {
            "images": [img_b64],
            "timer": None,
            "user_id": user_id,
            "context": context,
            "caption": parsed
        }
    else:
        # Các ảnh tiếp theo → chỉ cần thêm ảnh
        media_group_storage[media_group_id]["images"].append(img_b64)

    # ✅ Dù là ảnh đầu hay tiếp theo → luôn reset lại timer
    if media_group_storage[media_group_id]["timer"]:
        media_group_storage[media_group_id]["timer"].cancel()

    def process_media_group():
        context.user_data["image_data"] = media_group_storage[media_group_id]["images"]
        context.user_data["caption"] = media_group_storage[media_group_id]["caption"]
        del media_group_storage[media_group_id]
        if str(chat_id) == GROUP_DAO_ID:
            print("Đây là group Đáo")
            handle_selection_dao(update, context, selected_type="bill")
        elif str(chat_id) == GROUP_RUT_ID:
            print("Đây là group Rút")
            handle_selection_rut(update, context, selected_type="bill")

    timer = threading.Timer(3.0, process_media_group)
    media_group_storage[media_group_id]["timer"] = timer
    timer.start()


def handle_selection_dao(update, context, selected_type="bill",sheet_id=SHEET_DAO_ID):
    message = update.message
    full_name = message.from_user.full_name
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(f"Đang xử lý ảnh từ {full_name} ({message.from_user.id}) - {timestamp}")
    print(f"Caption: {caption}")

    if selected_type == "bill":
        if not image_b64_list:
            message.reply_text("❌ Không tìm thấy ảnh nào để xử lý.")
            return
        res_mess = []  # Để lưu kết quả trả về từ từng ảnh

        # Mở Google Sheet trước khi lặp
        spreadsheet = client.open_by_key(sheet_id)

        for img_b64 in image_b64_list:
            result = analyzer.analyze_bill(img_b64)
            if result is None:
                continue

            ten_ngan_hang = result.get("ten_ngan_hang")

            row = [
                timestamp,
                full_name,
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
                message.caption or ""
            ]
            
            # Xác định sheet theo ngân hàng
            if ten_ngan_hang == "MB":
                sheet = spreadsheet.worksheet("MB Bank")
            elif ten_ngan_hang == "HDBank":
                sheet = spreadsheet.worksheet("HD Bank")
            elif ten_ngan_hang == "VPBank":
                sheet = spreadsheet.worksheet("VP Bank")
            elif ten_ngan_hang is None:
                sheet = spreadsheet.worksheet("MPOS")
            else:
                sheet = spreadsheet.worksheet("Unknown")  # fallback nếu cần

            # Ghi dữ liệu
            sheet.append_row(row)
            # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"🏦 {result.get('ten_ngan_hang') or 'Không rõ'} - "
                f"💰 {result.get('tong_so_tien') or '?'} {result.get('don_vi_tien_te') or ''} - "
                f"{result.get('ngay_giao_dich')} {result.get('gio_giao_dich')}"
            )
        if res_mess:
            reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        else:
            reply_msg = "⚠️ Không xử lý được hóa đơn nào."

        message.reply_text(reply_msg)


def handle_selection_rut(update, context, selected_type="bill",sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.full_name
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(caption['khach'])

    if selected_type == "bill":
        if not image_b64_list:
            message.reply_text("❌ Không tìm thấy ảnh nào để xử lý.")
            return
        res_mess = []  # Để lưu kết quả trả về từ từng ảnh

        # Mở Google Sheet trước khi lặp
        spreadsheet = client.open_by_key(sheet_id)
        colname = [
            "Thời gian ghi nhận",        # timestamp
            "Người gửi",                 # full_name
            "Tên khách",                 # caption['khach']
            "Số điện thoại",             # caption['sdt']
            "Số tiền rút",               # caption['rut']
            "Phần trăm phí",            # caption['phi']
            "Số tiền phí",              # caption['tien_phi']
            "Số tiền chuyển khoản",     # caption['chuyen_khoan']
            "Lịch cảnh báo",            # caption['lich_canh_bao']
            "Số tài khoản",             # caption['stk']
            "Ghi chú",                  # caption['note']
            "Ngân hàng",                # result["ten_ngan_hang"]
            "Đơn vị bán hàng",          # result["ten_don_vi_ban"]
            "Địa chỉ đơn vị",           # result["dia_chi_don_vi_ban"]
            "Ngày giao dịch",           # result["ngay_giao_dich"]
            "Giờ giao dịch",            # result["gio_giao_dich"]
            "Tổng số tiền",             # result["tong_so_tien"]
            "Đơn vị tiền tệ",           # result["don_vi_tien_te"]
            "Loại thẻ",                 # result["loai_the"]
            "Mã giao dịch",             # result["ma_giao_dich"]
            "Mã đơn vị chấp nhận",      # result["ma_don_vi_chap_nhan"]
            "Số lô",                    # result["so_lo"]
            "Số tham chiếu",            # result["so_tham_chieu"]
            "Loại giao dịch",           # result["loai_giao_dich"]
            "Caption gốc"               # message.caption
        ]
        sheet1 = spreadsheet.worksheet("MB Bank")
        sheet1.append_row(colname)
        print(len(image_b64_list), "ảnh cần xử lý")
        for img_b64 in image_b64_list:
            result = analyzer.analyze_bill(img_b64)
            if result is None:
                continue
            ten_ngan_hang = result.get("ten_ngan_hang")


            row = [
                timestamp,
                full_name,
                caption['khach'],
                caption['sdt'],
                caption['rut'],
                caption['phi'],
                caption['tien_phi'],
                caption['chuyen_khoan'],
                caption['lich_canh_bao'],
                caption['stk'],
                caption['note'],
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
                message.caption or ""
            ]
            
            
            # Xác định sheet theo ngân hàng
            if ten_ngan_hang == "MB":
                sheet = spreadsheet.worksheet("MB Bank")
            elif ten_ngan_hang == "HDBank":
                sheet = spreadsheet.worksheet("HD Bank")
            elif ten_ngan_hang == "VPBank":
                sheet = spreadsheet.worksheet("VP Bank")
            elif ten_ngan_hang is None:
                sheet = spreadsheet.worksheet("MPOS")
            else:
                sheet = spreadsheet.worksheet("Unknown")  # fallback nếu cần

            # Ghi dữ liệu
            sheet.append_row(row)
            # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"🏦 {result.get('ten_ngan_hang') or 'Không rõ'} - "
                f"💰 {result.get('tong_so_tien') or '?'} {result.get('don_vi_tien_te') or ''} - "
                f"{result.get('ngay_giao_dich')} {result.get('gio_giao_dich')}"
            )
        if res_mess:
            reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        else:
            reply_msg = "⚠️ Không xử lý được hóa đơn nào."

        message.reply_text(reply_msg)

def parse_message_rut(text):
    data = {}
    if not text:
        return None
    patterns = {
        "khach": r"Khach:\s*(.+)",
        "sdt": r"SDT:\s*(\d+)",
        "rut": r"RUT:\s*([\d.]+[MK]?)",
        "phi": r"Phi:\s*([\d.]+%)",
        "tien_phi": r"(?:DienPhi|TienPhi):\s*([\d.]+[MK]?)",
        "chuyen_khoan": r"Chuyenkhoan:\s*([\d.]+[MK]?)",
        "lich_canh_bao": r"LichCanhBao:\s*(\d+)",
        "stk": r"STK:\s*(.+)",
        "note": r"Note:\s*(.+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    # Nếu không có Note nhưng có dòng ghi chú cuối cùng → gán vào 'note'
    last_line = text.strip().split('\n')[-1]
    if 'note' not in data and not any(k in last_line for k in ['Khach:', 'STK:', 'Chuyenkhoan:']):
        data['note'] = last_line.strip()

    return data


def parse_message_dao(text):
    data = {}
    if not text:
        return None
    patterns = {
        "khach": r"Khach:\s*(.+)",
        "sdt": r"SDT:\s*(\d+)",
        "dao": r"Dao:\s*([\d.]+[MK]?)",
        "phi": r"Phi:\s*([\d.]+%)",
        "tien_phi": r"TienPhi:\s*([\d.]+%)",
        "rut_thieu": r"RutThieu:\s*([\d.]+[MK]?)",
        "tong": r"Tong:\s*([\d.]+[MK]?)",
        "lich_canh_bao": r"LichCanhBao:\s*(\d+)",
        "note": r"Note:\s*(.+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    # Nếu không có Note nhưng có dòng ghi chú cuối cùng → gán vào 'note'
    last_line = text.strip().split('\n')[-1]
    if 'note' not in data and not any(k in last_line for k in ['Khach:', 'STK:', 'Chuyenkhoan:']):
        data['note'] = last_line.strip()

    return data

updater = Updater(
    token=TELEGRAM_TOKEN,
    request_kwargs={'proxy_url': PROXY_URL}
)

dp = updater.dispatcher
# Thứ tự rất quan trọng: handler kiểm tra group phải đứng trước
dp.add_handler(MessageHandler(Filters.photo, handle_photo))


updater.start_polling()
updater.idle()

