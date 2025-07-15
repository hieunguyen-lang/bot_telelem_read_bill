
import base64
import uuid
import json
import re
import threading
import os
import gspread
import unicodedata
import html
import base64
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from gemi_ai import GeminiBillAnalyzer
from data_connect.mysql_db_connector import MySQLConnector
from data_connect.redis_connect import RedisDuplicateChecker
from ai_core.gpt_ai_filter import GPTBill_Analyzer
from rapidfuzz import fuzz

from dotenv import load_dotenv
from helpers import helper,generate_qr
from helpers.bankpin import BankBin
load_dotenv()  # Tự động tìm và load từ .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ID của các group
GROUP_DAO_ID = os.getenv("GROUP_DAO_ID")  # ID của group DAO
GROUP_RUT_ID = os.getenv("GROUP_RUT_ID")  # ID của group Rút tiền
GROUP_MOMO_ID = os.getenv("GROUP_MOMO_ID") 
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
            display_missing = helper.format_missing_keys(missing)
            message += f"⚠️ Thiếu các trường sau: `{', '.join(display_missing)}`\n\n"

        message += (
            "📌 Ví dụ định dạng đúng:\n"
            "`Khach: {Nguyễn Văn A}`\n"
            "`Sdt: {0912345678}`\n"
            "`Rut: {40.000M}` hoặc `Dao: {32.400M}`\n"
            "`Phi: {2%}`\n"
            "`TienPhi: {800.000}`\n"
            "`Tong: {40.800M}`\n"
            "`LichCanhBao: {15}`\n"
            "`ck_vao: {3.058M}`\n"
            "`rut_thieu: {0}`\n"
            "`Stk: VPBANK - 0123456789 - Nguyễn Văn A`\n"
            "`Note: {Khách chuyển khoản hộ em}`"
        )
        return message

    # 🔄 Chuẩn hóa caption
    caption = normalize_caption(caption)

    # Check theo nhóm
    if str(chat_id) == GROUP_DAO_ID:
        required_keys = ["khach", "sdt", "dao", "phi", "lich_canh_bao", "stk", "note"]
    
        present_dict = helper.parse_message_dao(caption)
        print("present_dict:",present_dict)
        present_keys =list(present_dict.keys())
        missing_keys = [key for key in required_keys if key not in present_keys]

        if missing_keys:
            errmess = send_format_guide(missing_keys)
            return None, errmess

        
        if 'dao' not in present_dict:
            return None, "❌ thiếu key 'dao'"
        validate, err  = helper.validate_stk_nganhang_chutk(present_dict.get('stk'))
        
        if  validate == False:
            return None, err
        has_ck_vao = "ck_vao" in present_dict
        has_rut_thieu = "rut_thieu" in present_dict
        has_ck_ra = "ck_ra" in present_dict
        has_rut_thua = "rut_thua" in present_dict


        # Nếu cả 2 loại cùng có → lỗi
        if (has_ck_vao or has_rut_thieu) and (has_ck_ra or has_rut_thua):
            return None,"❌ Lỗi: không được vừa có cả rút thiếu(ck_vao,rut_thieu) và rút thừa(ck_ra,rut_thua)."
        # Nếu có dấu hiệu rút thiếu
        if has_ck_vao or has_rut_thieu:
            if not (has_ck_vao and has_rut_thieu):
                return None,(
                    "❌ Lỗi: Để xử lý rút thiếu, bạn cần nhập **cả 2 trường**: `ck_vao` và `rut_thieu`. "
                    "Hiện tại dữ liệu đang thiếu 1 trong 2."
                )
            if helper.parse_currency_input_int(present_dict.get("ck_vao")) == 0 and helper.parse_currency_input_int(present_dict.get("rut_thieu"))==0:
                return None, "❌  ck_ vao và rut_ thieu không thể cùng bằng: 0"
            # ✅ Đã hợp lệ rút thiếu, nhưng lại có thêm `ck_ra` hoặc `rut_thua`
            if has_ck_ra or has_rut_thua:
                return None, (
                    "❌ Lỗi: Đã nhập rút thiếu (`ck_vao`, `rut_thieu`) nhưng lại có thêm trường rút thừa(`ck_ra`, `rut_thua`)."
                )
            return present_dict, None
        # Nếu có dấu hiệu rút thừa
        if has_ck_ra or has_rut_thua:
            if not (has_ck_ra and has_rut_thua):
                return None,(
                    "❌ Lỗi: Để xử lý rút thừa, bạn cần nhập **cả 2 trường**: `ck_ra` và `rut_thua`. "
                    "Hiện tại dữ liệu đang thiếu 1 trong 2."
                )
            elif helper.parse_currency_input_int(present_dict.get("ck_ra")) == 0 and helper.parse_currency_input_int(present_dict.get("rut_thua"))==0:
                return None, "❌  ck_ vao và rut_ thieu không thể cùng bằng: 0"
            # ✅ Đã hợp lệ rút thừa, nhưng lại có thêm `ck_vao` hoặc `rut_thieu`
            if has_ck_vao or has_rut_thieu:
                return None, (
                    "❌ Lỗi: Đã nhập rút thừa (`ck_ra`, `rut_thua`) nhưng lại có thêm trường rút thiếu(`ck_vao`, `rut_thieu`)."
                )
            return present_dict, None
        
        return None, "❌ Lỗi: Không tìm thấy thông tin giao dịch hợp lệ."

    elif str(chat_id) == GROUP_RUT_ID:  
        required_keys = ["khach", "sdt", "rut", "phi", "tong", "lich_canh_bao", "ck_vao", "stk", "note"]

        present_dict = helper.parse_message_rut(caption)
        print("present_dict:",present_dict)
        present_keys =list(present_dict.keys())
        missing_keys = [key for key in required_keys if key not in present_keys]

        if missing_keys:    
            errmess = send_format_guide(missing_keys)
            return None, errmess

        parsed = helper.parse_message_rut(caption)
        if 'rut' not in parsed:
    
            return None, "❌  thiếu key 'rut'"
        
        if helper.parse_currency_input_int(present_dict.get("ck_ra")) == 0:
            return None, "❌ ck_ ra không thể bằng: 0"
        
        validate, err  = helper.validate_stk_nganhang_chutk(present_dict.get('stk'))
        
        if  validate == False:
            return None, err
        return parsed, None

    return {}, None

def handle_photo(update, context):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    print(f"Ảnh gửi từ group {chat_title} (ID: {chat_id})")
    
  
    if str(chat_id) not in [str(GROUP_DAO_ID), str(GROUP_RUT_ID), str(GROUP_MOMO_ID)]:
        
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
            message.reply_text(error_msg,parse_mode="Markdown")
            return

        context.user_data["image_data"] = [img_b64]
        context.user_data["caption"] = parsed
        # Gọi xử lý luôn (giả sử luôn là hóa đơn)
        if str(chat_id) == GROUP_DAO_ID:
           
            handle_selection_dao(update, context, selected_type="bill")
            
        elif str(chat_id) == GROUP_RUT_ID:
        
            handle_selection_rut(update, context)

        return
    
    if media_group_id not in media_group_storage:
        # Ảnh đầu tiên của media group → parse caption luôn
        parsed, error_msg = validate_caption(update, chat_id, message.caption)
        if error_msg:
            message.reply_text(error_msg,parse_mode="Markdown")
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
            handle_selection_rut(update, context)

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
    date_send = message.date
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
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
        ck_vao_int = helper.parse_currency_input_int(caption.get("ck_vao"))
        rut_thieu = helper.parse_currency_input_int(caption.get("rut_thieu"))
        ck_ra_int = helper.parse_currency_input_int(caption.get("ck_ra"))
        rut_thua = helper.parse_currency_input_int(caption.get("rut_thua"))
        batch_id =str(uuid.uuid4())
        count_img =0
        ma_chuyen_khoan = helper.base62_uuid4()
        percent = helper.parse_percent(caption.get('phi', '0'))
        for img_b64 in image_b64_list:
            count_img += 1
            if helper.is_bill_ket_toan_related(caption.get("note")) ==False:
                result = analyzer.analyze_bill_version_new_gpt(img_b64)    
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
            else:
                result = analyzer.analyze_bill_kettoan_gpt(img_b64)
                ten_ngan_hang= result.get("ten_ngan_hang")

            invoice_key = helper.generate_invoice_key_simple(result, ten_ngan_hang)
            duplicate = redis.is_duplicate(invoice_key)
            #duplicate = False
            if duplicate:
                print("[DUPLICATE KEY]"+str(invoice_key))
                message.reply_text(
                    f"🚫 Hóa đơn đã được gửi trước đó:\n"
                    f"Vui lòng không gửi hóa đơn bên ở dưới!\n"
                    f"• Ảnh Thứ: `{count_img}` bị trùng:"
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
            tong_so_tien = int(result.get("tong_so_tien"))
            row = [
                timestamp,
                full_name,
                caption['khach'],
                caption['sdt'],
                "DAO",
                ten_ngan_hang,
                result.get("ngay_giao_dich"),
                result.get("gio_giao_dich"),
                tong_so_tien,
                result.get("so_the"),
                result.get("tid"),
                result.get("mid"),
                result.get("so_lo"),
                result.get("so_hoa_don"),    
                result.get("ten_may_pos"),
                caption.get('lich_canh_bao'),
                int(percent * tong_so_tien),
                batch_id,
                caption.get('note'),
                helper.contains_khach_moi(caption.get('note', '')),
                ck_ra_int,
                ck_vao_int,
                None,  # stk_cty
                None,  # stk_khach
                str(percent),
                invoice_key,
                ma_chuyen_khoan,
                date_send.replace(day=int(caption.get('lich_canh_bao')))
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
                "PHÍ DV": 0,
            }
            
            list_data.append(data)
            list_invoice_key.append(invoice_key)
            list_row_insert_db.append(row)
            sum += int(result.get("tong_so_tien") or 0)
            # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"🏦 Ngân hàng: {ten_ngan_hang or 'Không rõ'} | "
                f"👤 Khách: {caption.get('khach', 'N/A')} | "
                f"💰 Tổng tiền: {helper.format_currency_vn(result.get('tong_so_tien')) or '?'} | "
                f" TID: {result.get('tid') or '?'} | "
                f" HĐ: {result.get('so_hoa_don') or 'N/A'} | "
                f" Lô: {result.get('so_lo') or 'N/A'} | "
                f" Máy POS: {result.get('ten_may_pos') or 'N/A'}"
            )
            
        if sum >10000000:
            cal_phi_dich_vu = int(sum * percent)
            print("sum: ",sum)    
            print("percent: ",percent)
            print("cal_phi_dich_vu: ",cal_phi_dich_vu)
            if rut_thieu and ck_vao_int:
                cal_ck_vao = int(cal_phi_dich_vu + rut_thieu)
                if cal_ck_vao != ck_vao_int:
                    try:
                        message.reply_text(
                            "❗ Có vẻ bạn tính sai ck_vao rồi 😅\n\n"
                            f"👉 Tổng Đáo: {sum:,}đ\n\n"
                            f"👉 Phí phần trăm: {percent * 100:.2f}%\n\n"
                            f"👉 Phí đúng phải là: <code>{cal_phi_dich_vu:,}</code>đ\n\n"
                            f"👉 Rút thiếu là: <code>{rut_thieu:,}</code>đ\n\n"
                            f"👉 ck_vao đúng phải là {sum:,} - {cal_phi_dich_vu:,}: <code>{int(cal_ck_vao):,}</code>đ\n\n",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Lỗi khi gửi message:", e)
                    return   
            elif rut_thua and ck_ra_int:  
                cal_ck_ra = int(rut_thua - cal_phi_dich_vu)
                if cal_ck_ra != ck_ra_int:
                    try:
                        message.reply_text(
                            "❗ Có vẻ bạn tính sai ck_ra rồi 😅\n\n"
                            f"👉 Tổng Đáo: {sum:,}đ\n\n"
                            f"👉 Phí phần trăm: {percent * 100:.2f}%\n\n"
                            f"👉 Phí đúng phải là: <code>{cal_phi_dich_vu:,}</code>đ\n\n"
                            f"👉 Rút thừa là: <code>{rut_thua:,}</code>đ\n\n"
                            f"👉 ck_ra đúng phải là {rut_thua:,}đ - {cal_phi_dich_vu:,}đ: <code>{int(cal_ck_ra):,}</code>đ\n\n",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Lỗi khi gửi message:", e)
                    return  
           
                    
        else:
            if rut_thieu and ck_vao_int:
                cal_ck_vao = int(200000 + rut_thieu)
                if cal_ck_vao != ck_vao_int:
                    try:
                        message.reply_text(
                            "❗ Có vẻ bạn tính sai ck_vao rồi 😅\n\n"
                            f"👉 Tổng rút: {sum:,}đ dưới 10M phí = 200,000đ\n\n"
                            f"👉 Rút thiếu là: <code>{rut_thieu:,}</code>đ\n\n"
                            f"👉 ck_vao đúng phải là 200,000đ + {rut_thieu:,} = <code>{int(cal_ck_vao):,}</code>đ\n\n",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Lỗi khi gửi message:", e)
                    return 
            if rut_thua and ck_ra_int:
                cal_ck_ra = int(rut_thua - 200000)
                if cal_ck_ra != ck_ra_int:
                    try:
                        message.reply_text(
                            "❗ Có vẻ bạn tính sai ck_vao rồi 😅\n\n"
                            f"👉 Tổng rút: {sum:,}đ dưới 10M phí = 200,000đ\n\n"
                            f"👉 Rút thừa là: <code>{rut_thua:,}</code>đ\n\n"
                            f"👉 ck_ra đúng phải là {rut_thua:,}đ - 200,200đ = <code>{int(cal_ck_ra):,}</code>đ\n\n",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print("Lỗi khi gửi message:", e)
                    return
            total_phi = 200000
            so_dong = len(list_row_insert_db)

            if so_dong > 0:
                phi_moi_dong = total_phi // so_dong  # chia đều
                du = total_phi % so_dong             # phần dư nếu có

                for i, row in enumerate(list_row_insert_db):
                    # Thêm 1 đơn vị dư cho những dòng đầu tiên
                    row[16] = phi_moi_dong + (1 if i < du else 0) 
        is_tienmat  = helper.is_cash_related(caption['note'])    
        # Gán stk_khach và stk_cty mặc định
        stk_khach = None
        stk_cty = None
        ck_vao_int_html=None
        ck_ra_int_html= None
        print("-----------------Gán stk--------------")
        
        if ck_ra_int == 0 and ck_vao_int !=0:
            stk_khach = ''
            stk_cty = caption.get("stk")
            ck_vao_int_html= html.escape(str(helper.format_currency_vn(ck_vao_int)))
        elif ck_ra_int != 0 and ck_vao_int ==0:
            stk_khach = caption.get("stk")
            stk_cty = ''
            ck_ra_int_html= html.escape(str(helper.format_currency_vn(ck_ra_int)))
        elif is_tienmat:
            stk_khach = ''
            stk_cty = "Tiền mặt"
        print("ck_vao_int: ",ck_vao_int)
        print("ck_ra_int: ",ck_ra_int)
        print("stk_khach: ",stk_khach)
        print("stk_cty: ",stk_cty)
        for row in list_row_insert_db:
            if stk_khach is not None:
                row[22] = stk_khach  # vị trí stk_khach
            if stk_cty is not None:
                row[23] = stk_cty    # vị trí stk_cty
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
            _, err = insert_bill_rows(db,list_row_insert_db)
            if err:
                message.reply_text(f"⚠️ Hóa đơn đã được gửi trước đó: {str(err)}")
                db.connection.rollback()
                return
            append_multiple_by_headers(sheet, list_data)
            if len(res_mess) == 0:
              reply_msg = "⚠️ Không xử lý được hóa đơn nào."
              message.reply_text(reply_msg)
              return  
            mess,photo = hanlde_sendmess_dao( caption, ck_ra_int, res_mess, ck_vao_int_html, ck_ra_int_html,ma_chuyen_khoan)
            helper.send_long_message(message,mess,photo)
            for item in list_invoice_key:
                redis.mark_processed(item)
        except Exception as e:
            db.connection.rollback()
            for item in list_invoice_key:
                redis.remove_invoice(item)
            message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))
            return
        try:
            db.connection.commit()
        except :
            db.connection.rollback()
            for item in list_invoice_key:
                redis.remove_invoice(item)
            raise 
    except Exception as e:
        
        db.connection.rollback()
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def hanlde_sendmess_dao( caption, ck_ra_int, res_mess, ck_vao_int_html, ck_ra_int_html,ma_chuyen_khoan):
    if caption.get('stk') != '':
                    stk_number, bank, name = helper.tach_stk_nganhang_chutk(caption.get('stk'))
                    stk_number = html.escape(stk_number)
                    bank = html.escape(bank)
                    ctk = html.escape(name)
                    qr_buffer =  generate_qr.generate_qr_binary(stk_number, bank, str(ck_ra_int),ma_chuyen_khoan)

                    if ck_ra_int_html:
                        reply_msg = f"<b>Bạn vui lòng kiểm tra thật kỹ lại các thông tin trước khi chuyển khoản ra  cho khách hàng, và check lại xem số liệu đã đúng chưa nhé !</b>\n\n"
                    if ck_vao_int_html:
                        reply_msg = f"<b>Bạn vui lòng kiểm tra thật kỹ lại các thông tin trước khi đưa cho khách chuyển khoản phí về công ty, và đừng quên kiểm tra bank xem nhận được tiền phí dịch vụ chưa nhé !</b>\n\n"
                    reply_msg += f"🏦 STK: <code><b>{stk_number}</b></code>\n\n"
                    reply_msg += f"💳 Ngân hàng: <b>{bank}</b>\n\n"
                    reply_msg += f"👤 CTK: <b>{ctk}</b>\n\n"
                    reply_msg += f"📝 Nội dung:  <code><b>{ma_chuyen_khoan}</b> </code>\n\n"
                    if ck_ra_int_html:
                        reply_msg += f"💰 Tổng số tiền chuyển lại khách: <code><b>{ck_ra_int_html}</b></code> VND\n\n"
                    if ck_vao_int_html:
                        reply_msg += f"💰 Tổng số tiền nhận lại là: <code><b>{ck_vao_int_html}</b></code> VND\n\n"
                    reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                    return  reply_msg,qr_buffer
    else:
        reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        return reply_msg,None

def handle_selection_rut(update, context,sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.username
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    date_send = message.date
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(caption)
    ck_vao_int = helper.parse_currency_input_int(caption.get("ck_vao"))
    ck_ra_int = helper.parse_currency_input_int(caption.get("ck_ra"))
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
        batch_id = str(uuid.uuid4())
        ma_chuyen_khoan = helper.base62_uuid4()
        count_img=0
        percent = helper.parse_percent(caption.get('phi', '0'))
        for img_b64 in image_b64_list:
            count_img +=1
            if helper.is_bill_ket_toan_related(caption.get("note")) ==False:        
                result = analyzer.analyze_bill_version_new_gpt(img_b64)
                    
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
            else:
                result = analyzer.analyze_bill_kettoan_gpt(img_b64)
            invoice_key = helper.generate_invoice_key_simple(result, ten_ngan_hang)
            duplicate = redis.is_duplicate(invoice_key)
            #duplicate = False
            print("-------------Duplicate: ",duplicate)
            if duplicate ==True:
                print("[DUPLICATE KEY]"+str(invoice_key))
                message.reply_text(
                    f"🚫 Hóa đơn đã được gửi trước đó:\n"
                    f"Vui lòng không gửi hóa đơn bên ở dưới!\n"
                    f"• Ảnh Thứ: `{count_img}` bị trùng:"
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
            tong_so_tien = int(result.get("tong_so_tien"))
            
            row = [
                timestamp,
                full_name,
                caption.get('khach'),
                caption.get('sdt'),
                "RUT",
                ten_ngan_hang,
                result.get("ngay_giao_dich"),
                result.get("gio_giao_dich"),
                tong_so_tien,
                result.get("so_the"),
                result.get("tid"),
                result.get("mid"),
                result.get("so_lo"),
                result.get("so_hoa_don"),
                result.get("ten_may_pos"),
                caption.get('lich_canh_bao'),
                int(percent * tong_so_tien),
                batch_id,
                caption.get('note'),
                helper.contains_khach_moi(caption.get('note', '')),
                ck_ra_int,
                ck_vao_int,
                None,  # stk_cty
                None,  # stk_khach
                str(percent),
                invoice_key,
                ma_chuyen_khoan,
                date_send.replace(day=int(caption.get('lich_canh_bao')))
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
                "PHÍ DV": 0,
            }
            
            
            list_invoice_key.append(invoice_key)
            list_data.append(data)
            list_row_insert_db.append(row)
            sum += int(result.get("tong_so_tien") or 0)

                # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"🏦 Ngân hàng: {ten_ngan_hang or 'MPOS'} | "
                f"👤 Khách: {caption.get('khach', 'N/A')} | "
                f" Tổng tiền: {helper.format_currency_vn(result.get('tong_so_tien')) or '?'} | "
                f" TID: {result.get('tid') or '?'} | "
                f" HĐ: {result.get('so_hoa_don') or ''} | "
                f" Lô: {result.get('so_lo') or ''} | "
                f" Máy POS: {result.get('ten_may_pos') or ''}"
            )
            
        if sum >10000000:
            cal_phi_dich_vu = int(sum * percent) 
            cal_ck_ra = int(sum - cal_phi_dich_vu)
            print("sum: ",sum)    
            print("percent: ",percent)
            print("cal_phi_dich_vu: ",cal_phi_dich_vu)  
            
            if cal_ck_ra !=ck_ra_int:
                try:
                    message.reply_text(
                        "❗ Có vẻ bạn tính sai ck_ra rồi 😅\n\n"
                        f"👉 Tổng rút: {sum:,}đ\n\n"
                        f"👉 Phí phần trăm: {percent * 100:.2f}%\n\n"
                        f"👉 Phí đúng phải là: <code>{cal_phi_dich_vu:,}</code>đ\n\n"
                        f"👉 ck_ra đúng phải là {sum:,} - {cal_phi_dich_vu:,}: <code>{int(cal_ck_ra):,}</code>đ\n\n",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print("Lỗi khi gửi message:", e)
                return
        else:
            cal_ck_ra = int(sum - 200000)
            if cal_ck_ra !=ck_ra_int:
                try:
                    message.reply_text(
                        "❗ Có vẻ bạn tính sai ck_ra rồi 😅\n\n"
                        f"👉 Tổng rút: {sum:,}đ dưới 10M phí = 200,000đ\n\n"
                        f"👉 ck_ra đúng phải là {sum:,} -200,000đ = <code>{int(cal_ck_ra):,}</code>đ\n\n",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print("Lỗi khi gửi message:", e)
                return
            
            total_phi = 200000
            so_dong = len(list_row_insert_db)

            if so_dong > 0:
                phi_moi_dong = total_phi // so_dong  # chia đều
                du = total_phi % so_dong             # phần dư nếu có

                for i, row in enumerate(list_row_insert_db):
                    # Thêm 1 đơn vị dư cho những dòng đầu tiên
                    row[16] = phi_moi_dong + (1 if i < du else 0) 

        is_tienmat  = helper.is_cash_related(caption['note'])
        # Gán stk_khach và stk_cty mặc định
        stk_khach = None
        stk_cty = None
        ck_vao_int_html=None
        ck_ra_int_html= None
        print("-----------------Gán stk--------------")
        if ck_ra_int == 0 and ck_vao_int !=0:
            stk_khach = ''
            stk_cty = caption.get("stk")
            ck_vao_int_html= html.escape(str(helper.format_currency_vn(ck_vao_int)))
        elif ck_ra_int != 0 and ck_vao_int ==0:
            stk_khach = caption.get("stk")
            stk_cty = ''
            ck_ra_int_html= html.escape(str(helper.format_currency_vn(ck_ra_int)))
        elif is_tienmat:
            stk_khach = ''
            stk_cty = "Tiền mặt"
        print("ck_vao_int: ",ck_vao_int)
        print("ck_ra_int: ",ck_ra_int)
        print("stk_khach: ",stk_khach)
        print("stk_cty: ",stk_cty)
        for row in list_row_insert_db:
            if stk_khach is not None:
                row[22] = stk_khach  # vị trí stk_khach
            if stk_cty is not None:
                row[23] = stk_cty    # vị trí stk_cty
                
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
            _, err = insert_bill_rows(db,list_row_insert_db)
            if err:
                message.reply_text(f"⚠️ Hóa đơn đã được gửi trước đó: {str(err)}")
                db.connection.rollback()
                return
            append_multiple_by_headers(sheet, list_data)
            if len(res_mess) == 0:
              reply_msg = "⚠️ Không xử lý được hóa đơn nào."
              message.reply_text(reply_msg)
              return 
            mess,photo=hanlde_sendmess_rut( caption, ck_ra_int, res_mess,ck_vao_int_html, ck_ra_int_html,ma_chuyen_khoan)
            helper.send_long_message(message,mess,photo)
            for item in list_invoice_key:
                redis.mark_processed(item)
        except Exception as e:
            db.connection.rollback()
            for item in list_invoice_key:
                redis.remove_invoice(item)
            message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))
            return  
        
        
        try:
            db.connection.commit()
        except :
            db.connection.rollback()
            for item in list_invoice_key:
                redis.remove_invoice(item)
            raise 
    except Exception as e:
        db.connection.rollback()
        print(str(e))
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def hanlde_sendmess_rut( caption, ck_ra_int, res_mess,ck_vao_int_html, ck_ra_int_html,ma_chuyen_khoan):
    if caption.get('stk') != '':
                    stk_number, bank, name = helper.tach_stk_nganhang_chutk(caption.get('stk'))
                    stk_number = html.escape(stk_number)
                    bank = html.escape(bank)
                    ctk = html.escape(name)
                    ck_ra_int_html= html.escape(str(helper.format_currency_vn(ck_ra_int)))
                        
                    qr_buffer =  generate_qr.generate_qr_binary(stk_number, bank, str(ck_ra_int),ma_chuyen_khoan)

                    
                    if ck_ra_int_html:
                        reply_msg = f"<b>Bạn vui lòng kiểm tra thật kỹ lại các thông tin trước khi chuyển khoản ra  cho khách hàng, và check lại xem số liệu đã đúng chưa nhé !</b>\n\n"
                    if ck_vao_int_html:
                        reply_msg = f"<b>Bạn vui lòng kiểm tra thật kỹ lại các thông tin trước khi đưa cho khách chuyển khoản phí về công ty, và đừng quên kiểm tra bank xem nhận được tiền phí dịch vụ chưa nhé !</b>\n\n"
                    reply_msg += f"🏦 STK: <code>{stk_number}</code>\n\n"
                    reply_msg += f"💳 Ngân hàng: <b>{bank}</b>\n\n"
                    reply_msg += f"👤 CTK: <b>{ctk}</b>\n\n"
                    reply_msg += f"📝 Nội dung:  <code><b>{ma_chuyen_khoan}</b> </code>\n\n"
                    if ck_ra_int_html:
                        reply_msg += f"💰 Tổng số tiền chuyển lại khách: <code><b>{ck_ra_int_html}</b></code> VND\n\n"
                    if ck_vao_int_html:
                        reply_msg += f"💰 Tổng số tiền nhận lại là: <code><b>{ck_vao_int_html}</b></code> VND\n\n"
                    reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                    return  reply_msg,qr_buffer
    else:
        reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        return reply_msg,None

        

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
            phi_per_bill,
            batch_id,
            caption_goc,
            khach_moi,
            ck_ra,
            ck_vao,
            stk_khach,
            stk_cty,
            phan_tram_phi,
            key_redis,
            ma_chuyen_khoan,
            lich_canh_bao_datetime
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    rowcount, err = db.executemany(query, list_rows)
    return rowcount, err
    






