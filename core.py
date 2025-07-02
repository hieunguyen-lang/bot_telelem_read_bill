
import base64
import uuid
from helpers import helper
import json
import re
import threading
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import base64
from gemi_ai import GeminiBillAnalyzer
from mysql_db_connector import MySQLConnector
from redis_connect import RedisDuplicateChecker
from gemi_ai_filter import GPTBill_Analyzer
from rapidfuzz import fuzz
import unicodedata
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
#analyzer = GeminiBillAnalyzer()
analyzer = GPTBill_Analyzer()
db = MySQLConnector(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    port=os.getenv("MYSQL_ROOT_PORT"),
    database=os.getenv("MYSQL_DATABASE")
)
media_group_storage = {}
redis=RedisDuplicateChecker()
def validate_caption(update, chat_id, caption):
    if not caption:
        return None, "❌ Không tìm thấy nội dung để xử lý. Vui lòng thêm caption cho ảnh."

    def normalize_caption(raw_caption: str) -> str:
        lines = raw_caption.strip().splitlines()
        normalized = []
        for line in lines:
            line = line.strip()
            # Loại bỏ khoảng trắng giữa key và dấu :
            line = re.sub(r"(\w+)\s*:", r"\1:", line)
            normalized.append(line)
        return "\n".join(normalized)

    def extract_keys(caption_text):
        # Lấy các key ở đầu dòng (case-insensitive)
        return [match.group(1).lower() for match in re.finditer(r"(?m)^(\w+):", caption_text, re.IGNORECASE)]

    def send_format_guide(missing=None):
        message = "❌ Vui lòng sửa lại caption theo đúng định dạng yêu cầu.\n"
        if missing:
            message += f"⚠️ Thiếu các trường sau: `{', '.join(missing)}`\n\n"
        message += (
            "📌 Ví dụ:\n"
            "`Khach: {Đặng Huỳnh Duyệt}`\n"
            "`Sdt: {0969963324}`\n"
            f"`{'Dao' if str(chat_id) == GROUP_DAO_ID else 'Rut'}: {{19M990}}`\n"
            "`Phi: {2%}`\n"
            "`TienPhi: {400K}`\n"
            "`Tong: {19M590}`\n"
            "`LichCanhBao: {21}`\n"
            "`Note: {Chuyển khoản hộ em với}`"
        )
        update.message.reply_text(message, parse_mode="Markdown")

    # 🔄 Chuẩn hóa caption
    caption = normalize_caption(caption)

    # Check theo nhóm
    if str(chat_id) == GROUP_DAO_ID:
        required_keys = ['khach', 'sdt', 'dao', 'phi', 'tienphi', 'tong', 'lichcanhbao']
        present_keys = extract_keys(caption)
        missing_keys = [key for key in required_keys if key not in present_keys]

        if missing_keys:
            send_format_guide(missing_keys)
            return None, "❌ Thiếu key: " + ", ".join(missing_keys)

        parsed = helper.parse_message_dao(caption)
        if 'dao' not in parsed:
            update.message.reply_text("❌ Lỗi: Không tìm thấy trường 'Dao' sau khi parse.")
            return None, "❌ parse_message_dao thiếu key 'dao'"
        return parsed, None

    elif str(chat_id) == GROUP_RUT_ID:
        required_keys = ['khach', 'sdt', 'rut', 'phi', 'tienphi', 'tong', 'lichcanhbao']
        present_keys = extract_keys(caption)
        missing_keys = [key for key in required_keys if key not in present_keys]

        if missing_keys:
            send_format_guide(missing_keys)
            return None, "❌ Thiếu key: " + ", ".join(missing_keys)

        parsed = helper.parse_message_rut(caption)
        if 'rut' not in parsed:
            update.message.reply_text("❌ Lỗi: Không tìm thấy trường 'Rut' sau khi parse.")
            return None, "❌ parse_message_rut thiếu key 'rut'"
        return parsed, None

    return {}, None

def handle_photo(update, context):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    print(f"Ảnh gửi từ group {chat_title} (ID: {chat_id})")
    
    # ❌ Bỏ qua nếu tin nhắn không đến từ group hợp lệ
    # print(chat_id, type(chat_id))
    # print(GROUP_DAO_ID, type(GROUP_DAO_ID))
    # print(GROUP_RUT_ID, type(GROUP_RUT_ID))
    if str(chat_id) not in [str(GROUP_DAO_ID), str(GROUP_RUT_ID)]:
        print(f"⛔ Tin nhắn từ group lạ (ID: {chat_id}) → Bỏ qua")
        return
    message = update.message
    media_group_id = message.media_group_id or f"single_{message.message_id}"
    if message.media_group_id is None or media_group_id not in media_group_storage:
        caption = message.caption or ""
        if "{" not in caption or "}" not in caption:
            return  # hoặc gửi cảnh báo
     # 👉 Bỏ qua nếu tin nhắn không có ảnh
    if not message or not message.photo:
        print("⛔ Tin nhắn không có ảnh, bỏ qua.")
        return
    
    user_id = message.from_user.id

    # Tải ảnh trước (phải làm trước khi xử lý ảnh đơn)
    
    img_b64 = helper.process_telegram_photo_to_base64(message.photo[-1])
    
    
    
    # 👉 Ảnh đơn → gán trực tiếp thành list
    if message.media_group_id is None:
        parsed, error_msg = validate_caption(update,chat_id, message.caption)
        if error_msg:
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


def append_multiple_by_headers(sheet, data_dict_list):
    print("Append rows")
    headers = sheet.row_values(1)
    num_columns = len(headers)

    # ⚠️ Gán lại KẾT TOÁN nếu có
    if data_dict_list and "KẾT TOÁN" in data_dict_list[0]:
        value = data_dict_list[0]["KẾT TOÁN"]
        for i, item in enumerate(data_dict_list):
            item["KẾT TOÁN"] = value if i == 0 else ""

    # Chuẩn bị dữ liệu
    rows_to_append = []
    for data_dict in data_dict_list:
        row_data = [""] * num_columns
        for i, h in enumerate(headers):
            value = data_dict.get(h, "")
            if h in {"SỐ HÓA ĐƠN", "SỐ LÔ", "TID"} and isinstance(value, str) and value.startswith("0"):
                row_data[i] = f'="{value}"'
            else:
                row_data[i] = str(value)
        rows_to_append.append(row_data)

    if not rows_to_append:
        print("⚠️ Không có dữ liệu để ghi.")
        return

    # 📌 Tìm dòng cuối có dữ liệu thực sự
    existing_values = sheet.get_all_values()
    last_row_index = len(existing_values) + 1  # +1 vì ghi bắt đầu dòng tiếp theo

    # ✅ Ghi dữ liệu theo từng dòng
    for i, row in enumerate(rows_to_append):
        sheet.update(
            f"A{last_row_index + i}:{chr(64 + num_columns)}{last_row_index + i}",
            [row],
            value_input_option="USER_ENTERED"
        )

    print(f"✅ Đã ghi {len(rows_to_append)} dòng vào từ dòng {last_row_index}.")

       
def handle_selection_dao(update, context, selected_type="bill",sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.username
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(f"Đang xử lý ảnh từ {full_name} ({message.from_user.id}) - {timestamp}")
    print(f"Caption: {caption}")

    try:
        if not image_b64_list:
            message.reply_text("❌ Không tìm thấy ảnh nào để xử lý.")
            return
        res_mess = []  # Để lưu kết quả trả về từ từng ảnh

        # Mở Google Sheet trước khi lặp
        spreadsheet = client.open_by_key(sheet_id)
        list_data=[]
        print(len(image_b64_list), "ảnh cần xử lý")
        list_row_insert_db = []
        list_invoice_key = []
        sum=0
        ten_ngan_hang=None
        tien_phi_int =helper.parse_currency_input_int(caption['tien_phi'])
        batch_id =str(uuid.uuid4())
        for img_b64 in image_b64_list:
            
            result = analyzer.analyze_bill_gpt(img_b64)
            
            if result.get("ten_ngan_hang") is None and result.get("so_hoa_don") is None and result.get("so_lo") is None and result.get("so_the") is None:
                print("Cả ten_ngan_hang và so_hoa_don so_lo so_the None")
                continue
            if result.get("so_lo") is None and result.get("mid") is None and result.get("tid") is None and result.get("so_the") is None:
                print("Cả so_lo và mid so_the tid ")
                continue
            if result.get("so_lo") is None and result.get("mid") is None:
                print("Cả so_lo và mid ")
                continue
            if result.get("so_lo") is None and result.get("tid") is None:
                print("Cả so_lo và tid ")
                continue
            if result.get("loai_giao_dich") is  None : 
                print("loai_giao_dich none")
                continue
            if result.get("loai_giao_dich") is not None and result.get("loai_giao_dich") =='Kết Toán': 
                print("Đây là hóa đơn kết toán")
                continue
            if result.get("ten_ngan_hang") is None:
                ten_ngan_hang="MPOS"
            else:
                ten_ngan_hang = result.get("ten_ngan_hang")
            
            
            row = [
                timestamp,
                full_name,
                caption['khach'],
                caption['sdt'],
                "DAO",
                ten_ngan_hang,
                result.get("ngay_giao_dich"),
                result.get("gio_giao_dich"),
                result.get("tong_so_tien"),
                result.get("so_the"),
                result.get("tid"),
                result.get("mid"),
                result.get("so_lo"),
                result.get("so_hoa_don"),    
                result.get("ten_may_pos"),
                caption['lich_canh_bao'],
                str(tien_phi_int),
                batch_id,
                caption['note'],
                caption["stk"],
                helper.contains_khach_moi(caption['note']),
                0,
                str(helper.parse_percent(caption['phi']))
            ]
        
            data = {
                "NGÀY": timestamp,
                "NGƯỜI GỬI": full_name,
                "HỌ VÀ TÊN KHÁCH": caption['khach'],
                "SĐT KHÁCH": caption['sdt'],
                "ĐÁO / RÚT": "Đáo",
                "SỐ TIỀN": helper.format_currency_vn(result.get("tong_so_tien")),
                "KẾT TOÁN": "kết toán",
                "SỐ THẺ THẺ ĐÁO / RÚT": result.get("so_the"),
                "TID": result.get("tid"),
                "SỐ LÔ": result.get("so_lo"),
                "SỐ HÓA ĐƠN": result.get("so_hoa_don"),
                "GIỜ GIAO DỊCH": result.get("gio_giao_dich"),
                "TÊN POS": result.get("ten_may_pos"),
                "PHÍ DV": tien_phi_int,
            }
            invoice_key = helper.generate_invoice_key_simple(result, ten_ngan_hang)
            duplicate = redis.is_duplicate(invoice_key)
            #duplicate = False
            if duplicate:
                print("[DUPLICATE KEY]"+str(invoice_key))
                message.reply_text(
                    f"🚫 Hóa đơn đã được gửi trước đó:\n"
                    f"Vui lòng không gửi hóa đơn bên ở dưới!\n"
                    f"• Key: `{invoice_key}`\n"
                    f"• Ngân hàng: `{ten_ngan_hang}`\n"
                    f"• Số HĐ: `{result.get('so_hoa_don')}`\n"
                    f"• Số lô: `{result.get('so_lo')}`\n"
                    f"• TID: `{result.get('tid')}`\n"
                    f"• MID: `{result.get('mid')}`\n"
                    f"• Ngày giao dịch : `{result.get('ngay_giao_dich')}`\n"
                    f"• Giờ giao dịch: `{result.get('gio_giao_dich')}`\n"
                    f"• Khách: *{caption.get('khach', 'Không rõ')}*",
                    parse_mode="Markdown"
                )
                return
            list_data.append(data)
            list_invoice_key.append(invoice_key)
            list_row_insert_db.append(row)
            sum += int(result.get("tong_so_tien") or 0)
            # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"🏦 {ten_ngan_hang or 'Không rõ'} - "
                f"👤 {caption['khach']} - "
                f"💰 {helper.format_currency_vn(result.get('tong_so_tien')) or '?'} - "
                f"💰 {result.get('tid') or '?'} - "
                f"📄 {result.get('so_hoa_don') or ''} - "
                f"🧾 {result.get('so_lo') or ''} - "
                f"🖥️ {result.get('ten_may_pos') or ''}"
            )
            
        if sum >10000000:
            print(caption)
            percent = helper.parse_percent(caption['phi'])
            
            cal_phi_dich_vu = sum * percent
            print("sum >10Tr")
            print("sum: ",sum)    
            print("percent: ",percent)
            print("cal_phi_dich_vu: ",cal_phi_dich_vu)
            if int(cal_phi_dich_vu) != tien_phi_int:
                message.reply_text(
                    "❗ Có vẻ bạn tính sai phí dịch vụ rồi 😅\n"
                    f"👉 Tổng rút: {sum:,}đ\n"
                    f"👉 Phí phần trăm: {percent * 100:.2f}%\n"
                    f"👉 Phí đúng phải là: {int(cal_phi_dich_vu):,}đ\n\n"
                    f"Sao chép nhanh: /{int(cal_phi_dich_vu)}"
                )
                return   
        else:
            for row in list_row_insert_db:
                # Giả sử cột 'tien_phi' nằm ở index 16
                row[16] = tien_phi_int      
        ck_khach  = helper.extract_amount_after_fee(caption['note'])
        for row in list_row_insert_db:
                
                if ck_khach:
                    row[21] = helper.parse_currency_input_int(ck_khach) 
                else:
                    row[21] = int(sum - int(tien_phi_int))
        for item in list_data:
            item["KẾT TOÁN"] = sum
            
            
        # Xác định sheet theo ngân hàng
        if ten_ngan_hang == "MB":
            sheet = spreadsheet.worksheet("MB Bank")
        elif ten_ngan_hang == "HDBank":
            sheet = spreadsheet.worksheet("HD Bank")
        elif ten_ngan_hang == "VPBank":
            sheet = spreadsheet.worksheet("VP Bank")
        elif ten_ngan_hang =="MPOS":
            sheet = spreadsheet.worksheet("MPOS")
        elif ten_ngan_hang is None:
            sheet = spreadsheet.worksheet("MPOS")
        else:
            sheet = spreadsheet.worksheet("MPOS")
        try:
            insert_bill_rows(db,list_row_insert_db)
            append_multiple_by_headers(sheet, list_data)
        except Exception as e:
            message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))
            return
        for item in list_invoice_key:
            redis.mark_processed(item)
        db.close()
        if res_mess:
            reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        else:
            reply_msg = "⚠️ Không xử lý được hóa đơn nào."

        message.reply_text(reply_msg)
    except Exception as e:
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def handle_selection_rut(update, context, selected_type="bill",sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.username
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(caption)
    try:
        if not image_b64_list:
            message.reply_text("❌ Không tìm thấy ảnh nào để xử lý.")
            return
        res_mess = []  # Để lưu kết quả trả về từ từng ảnh

        # Mở Google Sheet trước khi lặp
        spreadsheet = client.open_by_key(sheet_id)
        list_data=[]
        print(len(image_b64_list), "ảnh cần xử lý")
        list_row_insert_db = []
        list_invoice_key = []

        sum= 0
        ten_ngan_hang=None
        tien_phi_int =helper.parse_currency_input_int(caption['tien_phi'])
        batch_id = str(uuid.uuid4())
        for img_b64 in image_b64_list:
                    
            result = analyzer.analyze_bill_gpt(img_b64)
                  
            if result.get("ten_ngan_hang") is None and result.get("so_hoa_don") is None and result.get("so_lo") is None and result.get("so_the") is None:
                print("Cả ten_ngan_hang và so_hoa_don None")
                continue
            if result.get("so_lo") is None and result.get("mid") is None and result.get("tid") is None and result.get("so_the") is None:
                print("Cả so_lo và mid so_the tid ")
                continue
            if result.get("so_lo") is None and result.get("mid") is None:
                print("Cả so_lo và mid ")
                continue
            if result.get("so_lo") is None and result.get("tid") is None:
                print("Cả so_lo và tid ")
                continue
            if result.get("loai_giao_dich") is  None : 
                print("loai_giao_dich none")
                continue
            if result.get("loai_giao_dich") is not None and result.get("loai_giao_dich") =='Kết Toán': 
                print("Đây là hóa đơn kết toán")
                continue
            if result.get("ten_ngan_hang") is None:
                ten_ngan_hang="MPOS"
            else:
                ten_ngan_hang = result.get("ten_ngan_hang")
            
            
            row = [
                timestamp,
                full_name,
                caption['khach'],
                caption['sdt'],
                "RUT",
                ten_ngan_hang,
                result.get("ngay_giao_dich"),
                result.get("gio_giao_dich"),
                result.get("tong_so_tien"),
                result.get("so_the"),
                result.get("tid"),
                result.get("mid"),
                result.get("so_lo"),
                result.get("so_hoa_don"),    
                result.get("ten_may_pos"),
                caption['lich_canh_bao'],
                str(tien_phi_int),
                batch_id,
                caption['note'],
                caption["stk"],
                helper.contains_khach_moi(caption['note']),
                0,
                str(helper.parse_percent(caption['phi']))
            ]
              # Ghi vào MySQL
            
            data = {
                "NGÀY": timestamp,
                "NGƯỜI GỬI": full_name,
                "HỌ VÀ TÊN KHÁCH": caption['khach'],
                "SĐT KHÁCH": caption['sdt'],
                "ĐÁO / RÚT": "Rút",
                "SỐ TIỀN": helper.format_currency_vn(result.get("tong_so_tien")),
                "KẾT TOÁN": "kết toán",
                "SỐ THẺ THẺ ĐÁO / RÚT": result.get("so_the"),
                "TID": result.get("tid"),
                "SỐ LÔ": result.get("so_lo"),
                "SỐ HÓA ĐƠN": result.get("so_hoa_don"),
                "GIỜ GIAO DỊCH": result.get("gio_giao_dich"),
                "TÊN POS": result.get("ten_may_pos"),
                "PHÍ DV": tien_phi_int,
            }
            invoice_key = helper.generate_invoice_key_simple(result, ten_ngan_hang)
            duplicate = redis.is_duplicate(invoice_key)
            #duplicate = False
            print("-------------Duplicate: ",duplicate)
            if duplicate ==True:
                print("[DUPLICATE KEY]"+str(invoice_key))
                message.reply_text(
                    f"🚫 Hóa đơn đã được gửi trước đó:\n"
                    f"Vui lòng không gửi hóa đơn bên ở dưới!\n"
                    f"• Key: `{invoice_key}`\n"
                    f"• Ngân hàng: `{ten_ngan_hang}`\n"
                    f"• Số HĐ: `{result.get('so_hoa_don')}`\n"
                    f"• Số lô: `{result.get('so_lo')}`\n"
                    f"• TID: `{result.get('tid')}`\n"
                    f"• MID: `{result.get('mid')}`\n"
                    f"• Ngày giao dịch : `{result.get('ngay_giao_dich')}`\n"
                    f"• Giờ giao dịch: `{result.get('gio_giao_dich')}`\n"
                    f"• Khách: *{caption.get('khach', 'Không rõ')}*",
                    parse_mode="Markdown"
                )
                return
            list_invoice_key.append(invoice_key)
            list_data.append(data)
            list_row_insert_db.append(row)
            sum += int(result.get("tong_so_tien") or 0)

                # Lưu lại kết quả để in ra cuối
            res_mess.append(
                    f"🏦 {ten_ngan_hang or 'MPOS'} - "
                    f"👤 {caption['khach']} - "
                    f"💰 {helper.format_currency_vn(result.get('tong_so_tien')) or '?'} - "
                    f"💰 {result.get('tid') or '?'} - "
                    f"📄 {result.get('so_hoa_don') or ''} - "
                    f"🧾 {result.get('so_lo') or ''} - "
                    f"🖥️ {result.get('ten_may_pos') or ''}"
            )
            
        if sum >10000000:
           
            percent = helper.parse_percent(caption['phi'])
            cal_phi_dich_vu = sum * percent 
            print("sum >10Tr")
            print("sum: ",sum)    
            print("percent: ",percent)
            print("cal_phi_dich_vu: ",int(cal_phi_dich_vu))  
            print("tien_phi_int: ",tien_phi_int)
            if int(cal_phi_dich_vu) != tien_phi_int:
                try:
                    message.reply_text(
                        "❗ Có vẻ bạn tính sai phí dịch vụ rồi 😅\n"
                        f"👉 Tổng rút: {sum:,}đ\n"
                        f"👉 Phí phần trăm: {percent * 100:.2f}%\n"
                        f"👉 Phí đúng phải là: {int(cal_phi_dich_vu):,}đ\n\n"
                        f"Sao chép nhanh: /{int(cal_phi_dich_vu)}"
                    )
                except Exception as e:
                    print("Lỗi khi gửi message:", e)
                return
        else:
            
            for row in list_row_insert_db:
                # Giả sử cột 'tien_phi' nằm ở index 16
                row[16] = tien_phi_int 
        ck_khach  = helper.extract_amount_after_fee(caption['note'])
        for row in list_row_insert_db:
                
                if ck_khach:
                    row[21] = helper.parse_currency_input_int(ck_khach) 
                else:
                    row[21] = int(sum - int(tien_phi_int))
        for item in list_data:
            item["KẾT TOÁN"] = sum

        # Xác định sheet theo ngân hàng
        if ten_ngan_hang == "MB":
                sheet = spreadsheet.worksheet("MB Bank")
        elif ten_ngan_hang == "HDBank":
                sheet = spreadsheet.worksheet("HD Bank")
        elif ten_ngan_hang == "VPBank":
                sheet = spreadsheet.worksheet("VP Bank")
        elif ten_ngan_hang == "MPOS":
                sheet = spreadsheet.worksheet("MPOS")
        elif ten_ngan_hang is None:
            sheet = spreadsheet.worksheet("MPOS")
        else:
                sheet = spreadsheet.worksheet("MPOS")

        try:
            insert_bill_rows(db,list_row_insert_db)
            append_multiple_by_headers(sheet, list_data)
        except Exception as e:
            message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))
            return  
        for item in list_invoice_key:
            redis.mark_processed(item)
        db.close()
        if res_mess:
            reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        else:
            reply_msg = "⚠️ Không xử lý được hóa đơn nào."
        message.reply_text(reply_msg)
    except Exception as e:
        print(str(e))
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def insert_bill_rows(db, list_rows):
    print("Insert DB")
    query = """
        INSERT INTO thong_tin_hoa_don (
            thoi_gian,
            nguoi_gui,
            ten_khach,
            so_dien_thoai,
            type_dao_rut,
            ngan_hang,
            ngay_giao_dich,
            gio_giao_dich,
            tong_so_tien,
            so_the,
            tid,
            mid,
            so_lo,
            so_hoa_don,
            ten_may_pos,
            lich_canh_bao,
            tien_phi,
            batch_id,
            caption_goc,
            stk_khach,
            khach_moi,
            ck_khach_rut,
            phan_tram_phi
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s,%s,%s,%s,%s,%s,%s ,%s)
    """
    db.executemany(query, list_rows)






