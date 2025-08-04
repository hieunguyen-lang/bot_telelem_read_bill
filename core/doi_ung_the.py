
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
GROUP_DOI_UNG_THE_ID = os.getenv("GROUP_DOI_UNG_THE_ID")

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

def validate_caption( caption):
    
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
            "`Khach: Nguyễn Văn A`,\n"
            "`Phi: 2%`,\n"
            "`ck_ra: 3.058M`,\n"
            "`Stk: VPBANK - 0123456789 - Nguyễn Văn A`,\n"
            "`Note: Khách chuyển khoản hộ em`,"
        )
        return message

    # 🔄 Chuẩn hóa caption
    caption = normalize_caption(caption)
    required_keys = ["khach", "phi", "ck_ra", "stk", "note"]

    present_dict, errmes = helper.parse_message(caption)
    if errmes:
        return None, errmes
    print("present_dict:",present_dict)
    present_keys =list(present_dict.keys())
    missing_keys = [key for key in required_keys if key not in present_keys]

    if missing_keys:    
        errmess = send_format_guide(missing_keys)
        return None, errmess
        
    if helper.parse_currency_input_int(present_dict.get("ck_ra")) == 0:
        return None, "❌ ck_ ra không thể bằng: 0"
        
    validate, err  = helper.validate_stk_nganhang_chutk(present_dict.get('stk'))
        
    if  validate == False:
             None, err
    return present_dict, None


def handle_photo_doi_ung_the(update, context):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    print(f"Ảnh gửi từ group {chat_title} (ID: {chat_id})")
    
  
    if str(chat_id) not in [str(GROUP_DOI_UNG_THE_ID)]:
        
        print(f"⛔ Tin nhắn từ group lạ (ID: {chat_id}) → Bỏ qua")
        return
    message = update.message
    media_group_id = message.media_group_id or f"single_{message.message_id}"
    if message.media_group_id is None or media_group_id not in media_group_storage:
        caption = message.caption or ""
        if "@AI_RutTienNhanh_bot" not in caption :
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
        parsed, error_msg = validate_caption( message.caption)
        if error_msg:
            message.reply_text(error_msg,parse_mode="Markdown")
            return

        context.user_data["image_data"] = [img_b64]
        context.user_data["caption"] = parsed
        # Gọi xử lý luôn (giả sử luôn là hóa đơn)

        handle_selection(update, context)

        return
    
    if media_group_id not in media_group_storage:
        # Ảnh đầu tiên của media group → parse caption luôn
        parsed, error_msg = validate_caption( message.caption)
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
        
        handle_selection(update, context)

    timer = threading.Timer(3.0, process_media_group)
    media_group_storage[media_group_id]["timer"] = timer
    timer.start()




def handle_selection(update, context):
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
            result = analyzer.analyze_bill_version_new_gpt(img_b64)   
                
            if result.get("ten_ngan_hang") is None:
                ten_ngan_hang="MPOS"
            else:
                ten_ngan_hang = result.get("ten_ngan_hang")
            
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
                int(percent * tong_so_tien),
                batch_id,
                caption.get('note'),
                ck_ra_int,
                None,  # stk_khach
                str(percent),
                invoice_key,
                ma_chuyen_khoan
            ]
              # Ghi vào MySQL
    
            
            
            list_invoice_key.append(invoice_key)
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
       
            
        total_phi = 200000
        so_dong = len(list_row_insert_db)

        if so_dong > 0:
            phi_moi_dong = total_phi // so_dong  # chia đều
            du = total_phi % so_dong             # phần dư nếu có

            for i, row in enumerate(list_row_insert_db):
                # Thêm 1 đơn vị dư cho những dòng đầu tiên
                row[13] = phi_moi_dong + (1 if i < du else 0) 
        # Gán stk_khach và stk_cty mặc định
        stk_khach = None
        ck_ra_int_html= None
        print("-----------------Gán stk--------------")
        if ck_ra_int !=0:
            stk_khach = caption.get("stk")
            ck_ra_int_html= html.escape(str(helper.format_currency_vn(ck_ra_int)))
        
        print("ck_vao_int: ",ck_vao_int)
        print("ck_ra_int: ",ck_ra_int)
        print("stk_khach: ",stk_khach)
        for row in list_row_insert_db:
            if stk_khach is not None:
                row[17] = stk_khach  # vị trí stk_khach

        try:
            _, err = insert_bill_rows(db,list_row_insert_db)
            if err:
                message.reply_text(f"⚠️ Hóa đơn đã được gửi trước đó: {str(err)}")
                db.connection.rollback()
                return
            if len(res_mess) == 0:
              reply_msg = "⚠️ Không xử lý được hóa đơn nào."
              message.reply_text(reply_msg)
              return 
            mess,photo=hanlde_sendmess_rut( caption, ck_ra_int, res_mess, ck_ra_int_html,ma_chuyen_khoan)
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

def hanlde_sendmess_rut( caption, ck_ra_int, res_mess, ck_ra_int_html,ma_chuyen_khoan):
    if caption.get('stk') != '':
                    stk_number, bank, name = helper.tach_stk_nganhang_chutk(caption.get('stk'))
                    stk_number = html.escape(stk_number)
                    bank = html.escape(bank)
                    ctk = html.escape(name)
                    ck_ra_int_html= html.escape(str(helper.format_currency_vn(ck_ra_int)))
                        
                    qr_buffer =  generate_qr.generate_qr_binary(stk_number, bank, str(ck_ra_int),ma_chuyen_khoan)

                    
                    reply_msg = f"<b>Bạn vui lòng kiểm tra thật kỹ lại các thông tin trước khi chuyển khoản ra  cho khách hàng, và check lại xem số liệu đã đúng chưa nhé !</b>\n\n"
                    reply_msg += f"🏦 STK: <code>{stk_number}</code>\n\n"
                    reply_msg += f"💳 Ngân hàng: <b>{bank}</b>\n\n"
                    reply_msg += f"👤 CTK: <b>{ctk}</b>\n\n"
                    reply_msg += f"📝 Nội dung:  <code><b>{ma_chuyen_khoan}</b> </code>\n\n"
                    reply_msg += f"💰 Tổng số tiền chuyển lại khách: <code><b>{ck_ra_int_html}</b></code> VND\n\n"
                    reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                    return  reply_msg,qr_buffer
    else:
        reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        return reply_msg,None

        

def insert_bill_rows(db, list_rows):
    print("Insert DB")
    query = """
        INSERT INTO hoa_don_doi_tac (
            thoi_gian,
            nguoi_gui,
            ten_khach,
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
            phi_per_bill,
            batch_id,
            caption_goc,
            ck_ra,
            stk_khach,
            phan_tram_phi,
            key_redis,
            ma_chuyen_khoan
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    rowcount, err = db.executemany(query, list_rows)
    return rowcount, err
    






