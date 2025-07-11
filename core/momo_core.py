
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
import uuid
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from gemi_ai import GeminiBillAnalyzer
from data_connect.mysql_db_connector import MySQLConnector
from data_connect.redis_connect import RedisDuplicateChecker
from ai_core.gpt_ai_filter import GPTBill_Analyzer
from rapidfuzz import fuzz

from helpers import helper, generate_qr
from helpers.bankpin import BankBin
from dotenv import load_dotenv
load_dotenv()  # Tự động tìm và load từ .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# ID của các group
GROUP_MOMO_ID = os.getenv("GROUP_MOMO_ID") 


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


    def send_format_guide(missing=None):
        message = "❌ Vui lòng sửa lại caption theo đúng định dạng yêu cầu.\n"
        if missing:
            display_missing = helper.format_missing_keys(missing)
            message += f"⚠️ Thiếu các trường sau: `{', '.join(display_missing)}`\n\n"

        message += (
            "📌 Ví dụ định dạng đúng:\n"
            "`Khach: {Nguyễn Văn A}`\n"
            "`Phi: {2%}`\n"
            "`ck_ra: {0}`\n"
            "`Stk: VPBANK - 0123456789 - Nguyễn Văn A`\n"
            "`Note: {Khách chuyển khoản hộ em}`"
        )
        return message

    # 🔄 Chuẩn hóa caption
    caption = normalize_caption(caption)

    # Check theo nhóm
    if str(chat_id) == GROUP_MOMO_ID:
        required_keys = ["khach", "phi", "ck_ra", "ck_vao", "stk", "note"]
    
        present_dict = helper.parse_message_momo(caption)
        present_keys =list(present_dict.keys())
        missing_keys = [key for key in required_keys if key not in present_keys]
        # Kiểm tra thiếu cả ck_ra và ck_vao
        if "ck_ra" in missing_keys and "ck_vao" in missing_keys:
            return None, "❌ Bạn thiếu cả ck_ra và ck_vao"
        # Kiểm tra thiếu các key khác (ngoài ck_ra / ck_vao)
        others_missing = [k for k in missing_keys if k not in ("ck_ra", "ck_vao")]
        if others_missing:
            errmess = send_format_guide(others_missing)
            return None, errmess
        if "ck_ra" not in missing_keys:
            if helper.parse_currency_input_int(present_dict['ck_ra']) == 0:
                return None, "❌  Bạn chưa điền ck_ra hợp lệ"
        if "ck_vao" not in missing_keys:
            if helper.parse_currency_input_int(present_dict['ck_vao']) == 0:
                return None, "❌  Bạn chưa điền ck_vao hợp lệ"
        validate, err  = helper.validate_stk_nganhang_chutk(present_dict.get('stk'))
        
        if  validate == False:
            return None, err
        
        return present_dict, None


    return {}, None

def handle_photo_momo(update, context):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    print(f"Ảnh gửi từ group {chat_title} (ID: {chat_id})")
    print()
    # if str(chat_id) not in [str(GROUP_MOMO_ID)]:
    #     print(f"⛔ Tin nhắn từ group lạ (ID: {chat_id}) → Bỏ qua")
    #     return
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
           
        handle_momo_bill(update, context)
            
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
      
        handle_momo_bill(update, context)

    timer = threading.Timer(3.0, process_media_group)
    media_group_storage[media_group_id]["timer"] = timer
    timer.start()

       
def handle_momo_bill(update, context):
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
        list_data=[]
        print(len(image_b64_list), "ảnh cần xử lý")
        list_row_insert_db = []
        list_invoice_key = []
        sum=0
        sum_tong_phi=0
        batch_id =str(uuid.uuid4())
        count_img=0
        seen_keys = set()
        ma_chuyen_khoan = str(uuid.uuid4())
        for img_b64 in image_b64_list:
            count_img += 1
            result = analyzer.analyze_bill_momo_gpt(img_b64)    
                
            key_check_dup = helper.generate_invoice_dien(result)
            duplicate = redis.is_duplicate_momo(key_check_dup)

            #duplicate = False
            if duplicate:
                print("[DUPLICATE KEY]"+str(key_check_dup))
                message.reply_text(
                    (
                        "🚫 Hóa đơn đã được gửi trước đó:\n"
                        "Vui lòng không gửi hóa đơn bên ở dưới!\n"
                        f"• Ảnh: `{count_img}` bị trùng\n"
                        f"• Key: `{key_check_dup}`\n"
                        f"• Tên Khách: `{result.get('ten_khach_hang')}`\n"
                        f"• Số tiền: `{result.get('so_tien')}`\n"
                        f"• Ngày giao dịch: `{result.get('thoi_gian')}`\n"
                    ),
                    parse_mode="Markdown"
                )
                return
            
            if key_check_dup in seen_keys:
                message.reply_text(
                    (
                        "🚫 Hóa đơn đã được gửi trước đó:\n"
                        "Có thể bạn gửi 2 hóa đơn bị trùng:\n"
                        f"• Ảnh: `{count_img}` bị trùng\n"
                        
                    ),
                    parse_mode="Markdown"
                )
                return
            seen_keys.add(key_check_dup)
            tong_phi_parse=helper.parse_currency_input_int(helper.safe_get(result, "tong_phi"))
            row = [
                timestamp,
                helper.safe_get(result, "nha_cung_cap"),
                helper.safe_get(result, "ten_khach_hang"),
                helper.safe_get(result, "ma_khach_hang"),
                helper.safe_get(result, "dia_chi"),
                helper.safe_get(result, "ky_thanh_toan"),
                helper.safe_get(result, "so_tien"),
                helper.safe_get(result, "ma_giao_dich"),
                helper.fix_datetime(result.get("thoi_gian")),
                helper.safe_get(result, "tai_khoan_the"),
                tong_phi_parse,
                helper.safe_get(result, "trang_thai"),
                batch_id,
                full_name,
                helper.safe_get(caption, "khach"),
                key_check_dup,
                int(helper.parse_percent(caption['phi'])  *(int(result.get("so_tien") or 0)- helper.parse_currency_input_int(helper.safe_get(result, "tong_phi")))),
                0,
                0,
                ma_chuyen_khoan,
                helper.safe_get(caption, "stk")
            ]

            print(row)
            
            list_invoice_key.append(key_check_dup)
            list_row_insert_db.append(row)
            sum += int(result.get("so_tien") or 0)
            sum_tong_phi +=tong_phi_parse
            # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"👤 Khách: {helper.safe_get(result, 'ten_khach_hang') or 'N/A'} | "
                f" Mã KH: {helper.safe_get(result, 'ma_khach_hang') or 'N/A'} | "
                f" Tiền: {helper.format_currency_vn(result.get('so_tien')) or '?'} | "
                f" Mã GD: {helper.safe_get(result, 'ma_giao_dich') or 'N/A'} | "
                f" Thời gian: {helper.fix_datetime(result.get('thoi_gian')) or 'N/A'}"
            )
        percent = helper.parse_percent(caption['phi'])   
        if  caption.get('ck_ra', 0) != 0:
            ck_ra_cal = (sum-sum_tong_phi) -  percent*(sum-sum_tong_phi)
            ck_ra_caption_int =helper.parse_currency_input_int(caption['ck_ra'])
            
            print("sum_tong_phi: ",int(percent*(sum-sum_tong_phi)))
            print("ck_ra_caption_int: ",ck_ra_caption_int)
            print("ck_ra_cal: ",int(ck_ra_cal))
            for row in list_row_insert_db:
                row[18] = int(ck_ra_cal)  
            if int(ck_ra_cal) != ck_ra_caption_int:
                message.reply_text(
                    "❗ Có vẻ bạn tính sai ck_ra rồi 😅\n"
                    f"👉 Tổng rút: {sum:,}đ\n"
                    f"👉 Phí phần trăm: {percent * 100:.2f}%\n"
                    f"👉 Tổng phí: {int(percent*(sum-sum_tong_phi)):,}đ\n\n"
                    f"👉 ck_ra đúng phải là: {int(ck_ra_cal):,}đ\n\n"
                    f"Sao chép nhanh: <code>{int(ck_ra_cal)}</code>",
                    parse_mode="HTML"
                )
                return
        if  caption.get('ck_vao', 0) != 0:
            ck_vao_cal =  int(percent*(sum-sum_tong_phi))
            ck_vao_caption_int =helper.parse_currency_input_int(caption['ck_vao'])
            
            print("sum_tong_phi: ",ck_vao_cal)
            print("ck_vao_caption_int: ",ck_vao_caption_int)
            print("ck_vao_cal: ",int(ck_vao_cal))
            for row in list_row_insert_db:
                row[17] = int(ck_vao_cal)
            if int(ck_vao_cal) != ck_vao_caption_int:
                message.reply_text(
                    "❗ Có vẻ bạn tính sai ck_ra rồi 😅\n"
                    f"👉 Tổng rút: {sum:,}đ\n"
                    f"👉 Phí phần trăm: {percent * 100:.2f}%\n"
                    f"👉 Tổng phí: {int(percent*(sum-sum_tong_phi)):,}đ\n\n"
                    f"👉 ck_vao đúng phải là: {int(ck_ra_cal):,}đ\n\n"
                    f"Sao chép nhanh: <code>{int(ck_vao_cal)}</code>",
                    parse_mode="HTML"
                )
                return
        
        
    
        _, err = insert_bill_rows(db,list_row_insert_db)
        if err:
            db.connection.rollback()
            message.reply_text(f"⚠️ Lỗi gửi vào db: {str(err)}")
            return
        for item in list_invoice_key:
            redis.mark_processed_momo(item)
        try:
            mess,photo = handle_sendmess(caption, res_mess, ck_ra_cal,ma_chuyen_khoan)
            helper.send_long_message(message,mess,photo)
        except Exception as e:
            for item in list_invoice_key:
                redis.mark_processed_momo(item)
            db.connection.rollback()
            raise e
            
        db.connection.commit()
    except Exception as e:
        db.connection.rollback()
        for item in list_invoice_key:
            redis.remove_invoice_momo(item)
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))

def handle_sendmess( caption, res_mess, ck_ra_cal,ma_chuyen_khoan):
    if res_mess:
            if caption.get('stk') != '':
                stk_number, bank, name = helper.tach_stk_nganhang_chutk(caption.get('stk'))
                stk_number = html.escape(stk_number)
                bank = html.escape(bank)
                ctk = html.escape(name)

                ck_ra_int_html = html.escape(str(helper.format_currency_vn(int(ck_ra_cal))))
                qr_buffer =  generate_qr.generate_qr_binary(stk_number, bank, str(int(ck_ra_cal)),ma_chuyen_khoan)

                reply_msg = f"<b>Bạn vui lòng kiểm tra lại thông tin và chuyển khoản theo nội dung dưới đây:</b>\n\n"
                reply_msg += f"🏦 STK: <code>{stk_number}</code>\n\n"
                reply_msg += f"💳 Ngân hàng: <b>{bank}</b>\n\n"
                reply_msg += f"👤 CTK: <b>{ctk}</b>\n\n"
                reply_msg += f"💰 Tổng số tiền chuyển lại khách: <code>{ck_ra_int_html}</code> VND\n\n"

                reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                return  reply_msg,qr_buffer
            else:
                reply_msg += "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
                return reply_msg,None
    else:
        reply_msg = "⚠️ Không xử lý được hóa đơn nào."

        return reply_msg,None
        


def insert_bill_rows(db, list_rows):
    print("Insert DB")
    query = """
        INSERT INTO hoa_don_dien (
            update_at,
            nha_cung_cap,
            ten_khach_hang,
            ma_khach_hang,
            dia_chi,
            ky_thanh_toan,
            so_tien,
            ma_giao_dich,
            thoi_gian,
            tai_khoan_the,
            tong_phi,
            trang_thai,
            batch_id,
            nguoi_gui,
            ten_zalo,
            key_redis,
            phi_cong_ty_thu,
            ck_vao,
            ck_ra,
            ma_chuyen_khoan,
            so_tk
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    rowcount, err = db.executemany(query, list_rows)
    return rowcount, err
    






