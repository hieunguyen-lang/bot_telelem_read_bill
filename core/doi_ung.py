
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
from data_connect.mysql_db_connector import MySQLConnector
from data_connect.redis_connect import RedisDuplicateChecker
from ai_core.gpt_ai_filter import GPTBill_Analyzer
from rapidfuzz import fuzz
import unicodedata
import html
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
            "`Doitac: {Nguyễn Văn A}`\n"
            "`Phi: {3.5%}`\n"
            "`Tong: {0}`\n"
            "`Note: {Lô này tổng 50.069.782 giá nhập vào 3.5%}`"
        )
        update.message.reply_text(message, parse_mode="Markdown")

    # 🔄 Chuẩn hóa caption
    caption = normalize_caption(caption)

  
    required_keys = ["doitac", "phi", "tong", "note"]
    
    present_dict = helper.parse_message_doiung(caption)
    present_keys =list(present_dict.keys())
    missing_keys = [key for key in required_keys if key not in present_keys]

    if missing_keys:
        send_format_guide(missing_keys)
        return None, "❌ Thiếu key: " + ", ".join(missing_keys)

    parsed = helper.parse_message(caption)
    
    return parsed, None



def handle_photo_doiung(update, context):
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
        if "@AI_RutTienNhanh_bot" not in caption:
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
           
        handle_momo_bill(update, context)
            
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
    
        #batch_id =str(uuid.uuid4())
        batch_id = "_".join([
        helper.safe_get(caption, "doitac"),
        helper.safe_get(caption, "phi"),
        
        ])
        for img_b64 in image_b64_list:
            
            result = analyzer.analyze_bill_momo_gpt(img_b64)    
                
            key_check_dup = helper.generate_invoice_dien(result)
            duplicate = redis.is_duplicate_doiung(key_check_dup)
            duplicate = False
            if duplicate:
                print("[DUPLICATE KEY]"+str(key_check_dup))
                message.reply_text(
                    (
                        "🚫 Hóa đơn đã được gửi trước đó:\n"
                        "Vui lòng không gửi hóa đơn bên ở dưới!\n"
                        f"• Key: `{key_check_dup}`\n"
                        f"• Tên Khách: `{result.get('ten_khach_hang')}`\n"
                        f"• Số tiền: `{result.get('so_tien')}`\n"
                        f"• Ngày giao dịch: `{helper.safe_get(result, 'tong_phi')}`"
                    ),
                    parse_mode="Markdown"
                )

                return
            
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
                int(helper.parse_percent(caption['phi'])  *(int(result.get("so_tien") or 0)- helper.parse_currency_input_int(helper.safe_get(result, "tong_phi")))),
                helper.safe_get(result, "trang_thai"),
                batch_id,
                full_name,
                helper.safe_get(caption, "phi"),
                helper.safe_get(caption, "doitac"),
                key_check_dup

            ]

            
            list_invoice_key.append(key_check_dup)
            list_row_insert_db.append(row)
            sum += int(result.get("so_tien") or 0)
            # Lưu lại kết quả để in ra cuối
            res_mess.append(
                f"👤 {helper.safe_get(result, 'ten_khach_hang')} - "
                f"💰 {helper.format_currency_vn(result.get('so_tien')) or '?'} - "
                f"📄 {helper.safe_get(result, 'ma_giao_dich') or ''} - "
                f"🧾 {helper.fix_datetime(result.get('thoi_gian')) or ''} - "
            )
        tong_int =helper.parse_currency_input_int(caption['tong'])
        
        print(sum)
        print(int(tong_int))
        percent = helper.parse_percent(caption['phi']) 
        if int(sum) == tong_int:
            _, err = insert_bill_rows(db,list_row_insert_db)
            if err:
                message.reply_text(f"⚠️ Hóa đơn đã được gửi trước đó: {str(err)}")
                return
            for item in list_invoice_key:
                redis.mark_processed_doiung(item)
            db.close()
            if res_mess:
                reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
            else:
                reply_msg = "⚠️ Không xử lý được hóa đơn nào."

            message.reply_text(reply_msg)
        else:
            sum_html = html.escape(str(int(sum)))
            message.reply_text(
                    "❗ Có vẻ bạn tính sai ck_ra rồi 😅\n"
                    f"👉 Tổng tôi tính là: {int(sum):,}đ\n"
                    f"Sao chép nhanh: <code>{sum_html}</code>",
                    parse_mode="HTML"
                )
            return   
       
    except Exception as e:
        message.reply_text("⚠️ Có lỗi xảy ra trong quá trình xử lí: " + str(e))


def insert_bill_rows(db, list_rows):
    print("Insert DB")
    query = """
        INSERT INTO doi_ung (
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
            phi_phan_tram,
            doi_tac,
            key_redis
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    rowcount, err = db.executemany(query, list_rows)
    return rowcount, err
    






