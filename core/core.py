
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
            "`ck_ra: {0}`\n"
            "`Stk: VPBANK - 0123456789 - Nguyễn Văn A`\n"
            "`Note: {Khách chuyển khoản hộ em}`"
        )
        return message

    # 🔄 Chuẩn hóa caption
    caption = normalize_caption(caption)

    # Check theo nhóm
    if str(chat_id) == GROUP_DAO_ID:
        required_keys = ["khach", "sdt", "dao", "phi", "tien_phi", "tong", "lich_canh_bao", "ck_vao", "ck_ra", "stk", "note"]
    
        present_dict = helper.parse_message_dao(caption)
        present_keys =list(present_dict.keys())
        missing_keys = [key for key in required_keys if key not in present_keys]

        if missing_keys:
            errmess = send_format_guide(missing_keys)
            return None, errmess

        parsed = helper.parse_message_dao(caption)
        if 'dao' not in parsed:
            
            return None, "❌ thiếu key 'dao'"
        #print(int(present_dict.get("ck_vao")))
        if helper.parse_currency_input_int(present_dict.get("ck_ra")) == 0 and helper.parse_currency_input_int(present_dict.get("ck_vao"))==0:
            return None, "❌  ck_ vao và ck_ ra không thể cùng bằng: 0"
        
        validate, err  = helper.validate_stk_nganhang_chutk(present_dict.get('stk'))
        
        if  validate == False:
            return None, err
        return parsed, None

    elif str(chat_id) == GROUP_RUT_ID:  
        required_keys = ["khach", "sdt", "rut", "phi", "tien_phi", "tong", "lich_canh_bao", "ck_vao", "ck_ra", "stk", "note"]

        present_dict = helper.parse_message_rut(caption)
        present_keys =list(present_dict.keys())
        missing_keys = [key for key in required_keys if key not in present_keys]

        if missing_keys:    
            errmess = send_format_guide(missing_keys)
            return None, errmess

        parsed = helper.parse_message_rut(caption)
        if 'rut' not in parsed:
    
            return None, "❌  thiếu key 'rut'"
        
        if helper.parse_currency_input_int(present_dict.get("ck_ra")) == 0 and helper.parse_currency_input_int(present_dict.get("ck_vao"))==0:
            return None, "❌  ck_ vao và ck_ ra không thể cùng bằng: 0"
        
        validate, err  = helper.validate_stk_nganhang_chutk(present_dict.get('stk'))
        
        if  validate == False:
            return None, err
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
        
            handle_selection_rut(update, context, selected_type="bill")

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
    print(f"Caption: {caption}")
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
        sum=0
        ten_ngan_hang=None
        tien_phi_int =helper.parse_currency_input_int(caption['tien_phi'])
        batch_id =str(uuid.uuid4())
        for img_b64 in image_b64_list:
            
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
                caption.get('lich_canh_bao'),
                str(tien_phi_int),
                batch_id,
                caption.get('note'),
                helper.contains_khach_moi(caption.get('note', '')),
                str(ck_ra_int),
                str(ck_vao_int),
                None,  # stk_cty
                None,  # stk_khach
                str(helper.parse_percent(caption.get('phi', '')))
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
            print("vào đây")
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
                cal_phi_dich_vu_html= html.escape(str(int(cal_phi_dich_vu)))
                message.reply_text(
                    "❗ Có vẻ bạn tính sai phí dịch vụ rồi 😅\n"
                    f"👉 Tổng rút: {sum:,}đ\n"
                    f"👉 Phí phần trăm: {percent * 100:.2f}%\n"
                    f"👉 Phí đúng phải là: {int(cal_phi_dich_vu):,}đ\n\n"
                    f"Sao chép nhanh: <code>{cal_phi_dich_vu_html}</code>",
                    parse_mode="HTML"
                )
                return   
        else:
            for row in list_row_insert_db:
                # Giả sử cột 'tien_phi' nằm ở index 16
                row[16] = tien_phi_int  
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
                return
            append_multiple_by_headers(sheet, list_data)
        except Exception as e:
            message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))
            return
        for item in list_invoice_key:
            redis.mark_processed(item)
        db.close()
        hanlde_sendmess_dao(message, caption, ck_ra_int, res_mess, ck_vao_int_html, ck_ra_int_html)
    except Exception as e:
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def hanlde_sendmess_dao(message, caption, ck_ra_int, res_mess, ck_vao_int_html, ck_ra_int_html):
    if res_mess:
        if caption.get('stk') != '':
                    stk_number, bank, name = helper.tach_stk_nganhang_chutk(caption.get('stk'))
                    stk_number = html.escape(stk_number)
                    bank = html.escape(bank)
                    ctk = html.escape(name)
                    qr_buffer =  generate_qr.generate_qr_binary(stk_number, bank, str(ck_ra_int))

                    reply_msg = "@tuantienti1989, @Hieungoc288\n"
                    reply_msg += f"<b>Bạn vui lòng kiểm tra lại thông tin một lần nữa, và đừng quên kiểm tra bank xem nhận được tiền chưa nhé:</b>\n"
                    reply_msg += f"🏦 STK: <code><b>{stk_number}</b></code>\n"
                    reply_msg += f"💳 Ngân hàng: <b>{bank}</b>\n"
                    reply_msg += f"👤 CTK: <b>{ctk}</b>\n"
                    if ck_ra_int_html:
                        reply_msg += f"💰 Tổng số tiền chuyển lại khách: <code><b>{ck_ra_int_html}</b></code> VND\n\n"
                    if ck_vao_int_html:
                        reply_msg += f"💰 Tổng số tiền nhận lại là: <code><b>{ck_ra_int_html}</b></code> VND\n\n"
                    reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                    message.reply_photo(
                            photo=qr_buffer,
                            caption=reply_msg,
                            parse_mode="HTML"
                        )
        else:
            reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
            message.reply_text(reply_msg,parse_mode="HTML")
    else:
        reply_msg = "⚠️ Không xử lý được hóa đơn nào."
        message.reply_text(reply_msg,parse_mode="HTML")

def handle_selection_rut(update, context,sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.username
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
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
        tien_phi_int =helper.parse_currency_input_int(caption['tien_phi'])
        batch_id = str(uuid.uuid4())
        for img_b64 in image_b64_list:
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
            
            row = [
                timestamp,
                full_name,
                caption.get('khach'),
                caption.get('sdt'),
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
                caption.get('lich_canh_bao'),
                str(tien_phi_int),
                batch_id,
                caption.get('note'),
                helper.contains_khach_moi(caption.get('note', '')),
                str(ck_ra_int),
                str(ck_vao_int),
                None,  # stk_cty
                None,  # stk_khach
                str(helper.parse_percent(caption.get('phi', '')))
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
                    cal_phi_dich_vu_html= html.escape(str(int(cal_phi_dich_vu)))
                    message.reply_text(
                        "❗ Có vẻ bạn tính sai phí dịch vụ rồi 😅\n"
                        f"👉 Tổng rút: {sum:,}đ\n"
                        f"👉 Phí phần trăm: {percent * 100:.2f}%\n"
                        f"👉 Phí đúng phải là: {int(cal_phi_dich_vu):,}đ\n\n"
                        f"Sao chép nhanh: /<code>{cal_phi_dich_vu_html}</code>",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print("Lỗi khi gửi message:", e)
                return
        else:
            
            for row in list_row_insert_db:
                # Giả sử cột 'tien_phi' nằm ở index 16
                row[16] = tien_phi_int 
        is_tienmat  = helper.is_cash_related(caption['note'])
        # Gán stk_khach và stk_cty mặc định
        stk_khach = None
        stk_cty = None
        print("-----------------Gán stk--------------")
        if ck_ra_int == 0 and ck_vao_int !=0:
            stk_khach = ''
            stk_cty = caption.get("stk")
        elif ck_ra_int != 0 and ck_vao_int ==0:
            stk_khach = caption.get("stk")
            stk_cty = ''
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
                return
            append_multiple_by_headers(sheet, list_data)
        except Exception as e:
            message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))
            return  
        for item in list_invoice_key:
            redis.mark_processed(item)
        db.close()
        hanlde_sendmess_rut(message, caption, ck_ra_int, res_mess)
    except Exception as e:
        print(str(e))
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def hanlde_sendmess_rut(message, caption, ck_ra_int, res_mess):
    if res_mess:
        if caption.get('stk') != '':
                    stk_number, bank, name = helper.tach_stk_nganhang_chutk(caption.get('stk'))
                    stk_number = html.escape(stk_number)
                    bank = html.escape(bank)
                    ctk = html.escape(name)
                    ck_ra_int_html= html.escape(str(helper.format_currency_vn(ck_ra_int)))
                        
                    qr_buffer =  generate_qr.generate_qr_binary(stk_number, bank, str(ck_ra_int))

                    reply_msg = "@tuantienti1989, @Hieungoc288\n\n"
                    reply_msg += f"<b>Bạn vui lòng kiểm tra lại thông tin và chuyển khoản theo nội dung dưới đây:</b>\n"
                    reply_msg += f"🏦 STK: <code>{stk_number}</code>\n"
                    reply_msg += f"💳 Ngân hàng: <b>{bank}</b>\n"
                    reply_msg += f"👤 CTK: <b>{ctk}</b>\n"
                    reply_msg += f"💰 Tổng số tiền chuyển lại khách: <code>{ck_ra_int_html}</code> VND\n\n"
                    reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                    message.reply_photo(
                            photo=qr_buffer,
                            caption=reply_msg,
                            parse_mode="HTML"
                        )
        else:
            reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
            message.reply_text(reply_msg,parse_mode="HTML")
    else:
        reply_msg = "⚠️ Không xử lý được hóa đơn nào."
        message.reply_text(reply_msg,parse_mode="HTML")

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
            khach_moi,
            ck_ra,
            ck_vao,
            stk_khach,
            stk_cty,
            phan_tram_phi
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    rowcount, err = db.executemany(query, list_rows)
    return rowcount, err
    






