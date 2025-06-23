
import base64
import time
import json
import re
import threading
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# from telegram.ext import Updater, MessageHandler, Filters
from io import BytesIO
from gemi_ai import GeminiBillAnalyzer
from mysql_db_connector import AsyncMySQLConnector
import  asyncio
from concurrent.futures import ThreadPoolExecutor

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
db = AsyncMySQLConnector(
    host="localhost",
    user='root',
    password=os.getenv("MYSQL_ROOT_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)
media_group_storage = {}

async def validate_caption(update,chat_id, caption):
    if not caption:
        return None, "❌ Không tìm thấy nội dung để xử lý. Vui lòng thêm caption cho ảnh."

    if str(chat_id) == GROUP_DAO_ID:
        # ⚠️ Bắt buộc mỗi dòng đều phải có nháy ' hoặc "
        required_keys = ['Khach', 'Sdt', 'Dao', 'Phi', 'TienPhi','Tong','LichCanhBao']
        for key in required_keys:
            pattern = rf"{key}:\s*(?:['\"])?(.+?)(?:['\"])?(?:\n|$)"
            if not re.search(pattern, caption, re.IGNORECASE):
                await update.message.reply_text(
                    "Vui lòng sửa lại caption theo đúng định dạng yêu cầu."
                    "📌 Ví dụ:\n"
                    "`Khach: {Đặng Huỳnh Duyệt}`\n"
                    "`Sdt: {0969963324}`\n"
                    "`Dao: {19M990}`\n"
                    "`Phi: {2%}`\n"
                    "`TienPhi: {400K}`\n"
                    "`Tong: {19M590}`\n"
                    "`LichCanhBao: {21}`\n"
                    "`Note: {Chuyển khoản hộ em với}`",
                    parse_mode="Markdown"
                    )
                return None, "None"
            
        parsed = parse_message_dao(caption)
        if 'dao' not in parsed:
            await update.message.reply_text(
                    "Vui lòng sửa lại caption theo đúng định dạng yêu cầu."
                    "📌 Ví dụ:\n"
                    "`Khach: {Đặng Huỳnh Duyệt}`\n"
                    "`Sdt: {0969963324}`\n"
                    "`Dao: {19M990}`\n"
                    "`Phi: {2%}`\n"
                    "`TienPhi: {400K}`\n"
                    "`Tong: {19M590}`\n"
                    "`LichCanhBao: {21}`\n"
                    "`Note: {Chuyển khoản hộ em với}`",
                    parse_mode="Markdown"
                    )
            return None, "None"
        return parsed, None

    elif str(chat_id) == GROUP_RUT_ID:
        # ⚠️ Bắt buộc mỗi dòng đều phải có nháy ' hoặc "
        required_keys = ['Khach', 'Sdt', 'Rut', 'Phi', 'TienPhi','Tong','LichCanhBao']
        for key in required_keys:
            pattern = rf"{key}:\s*(?:['\"])?(.+?)(?:['\"])?(?:\n|$)"
            if not re.search(pattern, caption, re.IGNORECASE):
                await update.message.reply_text(
                    "Vui lòng sửa lại caption theo đúng định dạng yêu cầu."
                    "📌 Ví dụ:\n"
                    "`Khach: {Đặng Huỳnh Duyệt}`\n"
                    "`Sdt: {0969963324}`\n"
                    "`Rut: {19M990}`\n"
                    "`Phi: {2%}`\n"
                    "`TienPhi: {400K}`\n"
                    "`Tong: {19M590}`\n"
                    "`LichCanhBao: {21}`\n"
                    "`Note: {Chuyển khoản hộ em với}`",
                    parse_mode="Markdown"
                    )
                return None, "None"
        parsed = parse_message_rut(caption)
        if 'rut' not in parsed:
            await update.message.reply_text(
                    "Vui lòng sửa lại caption theo đúng định dạng yêu cầu."
                    "📌 Ví dụ:\n"
                    "`Khach: {Đặng Huỳnh Duyệt}`\n"
                    "`Sdt: {0969963324}`\n"
                    "`Rut: {19M990}`\n"
                    "`Phi: {2%}`\n"
                    "`TienPhi: {400K}`\n"
                    "`Tong: {19M590}`\n"
                    "`LichCanhBao: {21}`\n"
                    "`Note: {Chuyển khoản hộ em với}`",
                    parse_mode="Markdown"
                    )
            return None, "None"
        return parsed, None

    return {}, None

async def handle_photo(update, context):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    print(f"Ảnh gửi từ group {chat_title} (ID: {chat_id})")
    message = update.message
    media_group_id = message.media_group_id or f"single_{message.message_id}"
    user_id = message.from_user.id

    # Tải ảnh
    try:
        file = await message.photo[-1].get_file()
        bio = BytesIO()
        await file.download_to_memory(out=bio)
        img_b64 = base64.b64encode(bio.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"❌ Lỗi khi xử lý ảnh: {e}")
        return

    # 👉 Ảnh đơn
    if message.media_group_id is None:
        parsed, error_msg = await validate_caption(update, chat_id, message.caption)
        if error_msg:
            return

        context.user_data["image_data"] = [img_b64]
        context.user_data["caption"] = parsed

        if str(chat_id) == GROUP_DAO_ID:
            await handle_selection_dao(update, context, selected_type="bill")
        elif str(chat_id) == GROUP_RUT_ID:
            await handle_selection_rut(update, context, selected_type="bill")
        return

    # 👉 Media group
    if media_group_id not in media_group_storage:
        parsed, error_msg = await validate_caption(update, chat_id, message.caption)
        if error_msg:
            return

        media_group_storage[media_group_id] = {
            "images": [img_b64],
            "task": asyncio.create_task(
                delayed_process_media_group(media_group_id, chat_id, update, context)
            ),
            "caption": parsed
        }
    else:
        # Ảnh tiếp theo đến → chỉ thêm ảnh, KHÔNG tạo lại task
        media_group_storage[media_group_id]["images"].append(img_b64)


# ⏳ Xử lý media group sau khi chờ 3s
async def delayed_process_media_group(media_group_id, chat_id, update, context):
    try:
        print(f"✅ Task xử lý media_group {media_group_id} đang chạy sau 5s...")
        await asyncio.sleep(5)  # chờ gom ảnh xong
        data = media_group_storage.pop(media_group_id)
        context.user_data["image_data"] = data["images"]
        context.user_data["caption"] = data["caption"]

        if str(chat_id) == GROUP_DAO_ID:
            print("Đây là group Đáo")
            await handle_selection_dao(update, context, selected_type="bill")
        elif str(chat_id) == GROUP_RUT_ID:
            print("Đây là group Rút")
            await handle_selection_rut(update, context, selected_type="bill")

    except asyncio.CancelledError:
        print(f"⛔ Task xử lý media_group {media_group_id} bị hủy.")

async def append_multiple_by_headers(sheet, data_dict_list):
    headers = sheet.row_values(1)

    # ⚠️ Chỉ dòng đầu có giá trị 'KẾT TOÁN'
    if data_dict_list and "KẾT TOÁN" in data_dict_list[0]:
        value = data_dict_list[0]["KẾT TOÁN"]
        for i, item in enumerate(data_dict_list):
            item["KẾT TOÁN"] = value if i == 0 else ""

    rows_to_append = []
    for data_dict in data_dict_list:
        row_data = [""] * len(headers)
        for i, h in enumerate(headers):
            value = data_dict.get(h, "")
            if h in {"SỐ HÓA ĐƠN", "SỐ LÔ", "TID"} and isinstance(value, str) and value.startswith("0"):
                row_data[i] = f'="{value}"'
            else:
                row_data[i] = str(value)
        rows_to_append.append(row_data)

    if rows_to_append:
        start_row = len(sheet.get_all_values()) + 1
        await sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        end_row = start_row + len(rows_to_append) - 1

        if "KẾT TOÁN" in headers and end_row > start_row:
            col_idx = headers.index("KẾT TOÁN") + 1
            await sheet.merge_cells(start_row, col_idx, end_row, col_idx)

        print(f"✅ Đã ghi và gộp {len(rows_to_append)} dòng vào Google Sheet.")
    
async def handle_selection_dao(update, context, selected_type="bill",sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.username
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(f"Đang xử lý ảnh từ {full_name} ({message.from_user.id}) - {timestamp}")
    print(f"Caption: {caption}")

    if selected_type == "bill":
        if not image_b64_list:
            await message.reply_text("❌ Không tìm thấy ảnh nào để xử lý.")
            return
        res_mess = []  # Để lưu kết quả trả về từ từng ảnh

        # Mở Google Sheet trước khi lặp
        spreadsheet = client.open_by_key(sheet_id)
        list_data=[]
        list_row = []
        sum=0
        print("len:",str(len(image_b64_list)))
        for img_b64 in image_b64_list:
            print("Gửi ảnh đến LLM")
            result = await asyncio.wait_for(analyzer.analyze_bill(img_b64), timeout=10)
            print("Kết quả trả về: ", result)
            #await asyncio.sleep(1.5)  # ✅ Không dùng time.sleep
            if result is None:
                continue

            ten_ngan_hang = result.get("ten_ngan_hang")
            
            row = [
                timestamp,
                full_name,
                caption['khach'],
                caption['sdt'],
                "DAO",
                result.get("ten_ngan_hang"),
                result.get("ngay_giao_dich"),
                result.get("gio_giao_dich"),
                result.get("tong_so_tien"),
                result.get("so_the"),
                result.get("tid"),
                result.get("so_lo"),
                result.get("so_hoa_don"),    
                result.get("ten_may_pos"),
                message.caption
            ]
        
            data = {
                "NGÀY": timestamp,
                "NGƯỜI GỬI": full_name,
                "HỌ VÀ TÊN KHÁCH": caption['khach'],
                "SĐT KHÁCH": caption['sdt'],
                "ĐÁO / RÚT": "Đáo",
                "SỐ TIỀN": result.get("tong_so_tien"),
                "KẾT TOÁN": "kết toán",
                "SỐ THẺ THẺ ĐÁO / RÚT": result.get("so_the"),
                "TID": result.get("tid"),
                "SỐ LÔ": result.get("so_lo"),
                "SỐ HÓA ĐƠN": result.get("so_hoa_don"),
                "GIỜ GIAO DỊCH": result.get("gio_giao_dich"),
                "TÊN POS": result.get("ten_may_pos"),
                "PHÍ DV": caption['tien_phi'],
            }
            if result.get("so_hoa_don") is not None:
                list_data.append(data)
                print("➡️ Chuẩn bị insert MySQL...")
                await insert_bill_row(db, row)
                print("✅ Đã insert xong")
                sum += int(result.get("tong_so_tien") or 0)
                # Lưu lại kết quả để in ra cuối
                res_mess.append(
                    f"🏦 {result.get('ten_ngan_hang') or 'Không rõ'} - "
                    f"👤 {caption['khach']} - "
                    f"💰 {result.get('tong_so_tien') or '?'} - "
                    f"💰 {result.get('tid') or '?'} - "
                    f"📄 {result.get('so_hoa_don') or ''} - "
                    f"🧾 {result.get('so_lo') or ''} - "
                    f"🖥️ {result.get('ten_may_pos') or ''}"
                )
            
        for item in list_data:
            item["KẾT TOÁN"] = sum
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
                sheet = spreadsheet.worksheet("Unknown")
            # Ghi dữ liệu
        await append_multiple_by_headers(sheet, list_data)
        db.close()
        if res_mess:
            reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        else:
            reply_msg = "⚠️ Không xử lý được hóa đơn nào."
        print(res_mess)
        print(reply_msg)
        await message.reply_text(reply_msg)
        


async def handle_selection_rut(update, context, selected_type="bill",sheet_id=SHEET_RUT_ID):
    message = update.message
    full_name = message.from_user.username
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    image_b64_list = context.user_data.get("image_data", [])
    caption = context.user_data.get("caption", "")  # 👈 lấy caption
    print(caption)

    if selected_type == "bill":
        if not image_b64_list:
            await message.reply_text("❌ Không tìm thấy ảnh nào để xử lý.")
            return
        res_mess = []  # Để lưu kết quả trả về từ từng ảnh

        # Mở Google Sheet trước khi lặp
        spreadsheet = client.open_by_key(sheet_id)
        list_data=[]
        print(len(image_b64_list), "ảnh cần xử lý")
        sum= 0
        
        for img_b64 in image_b64_list:
            print("Gửi ảnh đến LLM")
            result = await analyzer.analyze_bill(img_b64)
            print("Gửi ảnh đến LLM")

            if result is None:
                continue
            ten_ngan_hang = result.get("ten_ngan_hang")


            row = [
                timestamp,
                full_name,
                caption['khach'],
                caption['sdt'],
                "DAO",
                result.get("ten_ngan_hang"),
                result.get("ngay_giao_dich"),
                result.get("gio_giao_dich"),
                result.get("tong_so_tien"),
                result.get("so_the"),
                result.get("tid"),
                result.get("so_lo"),
                result.get("so_hoa_don"),    
                result.get("ten_may_pos"),
                message.caption
            ]
              # Ghi vào MySQL
            data = {
                "NGÀY": timestamp,
                "NGƯỜI GỬI": full_name,
                "HỌ VÀ TÊN KHÁCH": caption['khach'],
                "SĐT KHÁCH": caption['sdt'],
                "ĐÁO / RÚT": "Rút",
                "SỐ TIỀN": result.get("tong_so_tien"),
                "KẾT TOÁN": "kết toán",
                "SỐ THẺ THẺ ĐÁO / RÚT": result.get("so_the"),
                "TID": result.get("tid"),
                "SỐ LÔ": result.get("so_lo"),
                "SỐ HÓA ĐƠN": result.get("so_hoa_don"),
                "GIỜ GIAO DỊCH": result.get("gio_giao_dich"),
                "TÊN POS": result.get("ten_may_pos"),
                "PHÍ DV": caption['tien_phi'],
            }
            if result.get("so_hoa_don") is not None:
                list_data.append(data)
                await insert_bill_row(db, row)
                sum += int(result.get("tong_so_tien") or 0)

                # Lưu lại kết quả để in ra cuối
                res_mess.append(
                    f"🏦 {result.get('ten_ngan_hang') or 'Không rõ'} - "
                    f"👤 {caption['khach']} - "
                    f"💰 {result.get('tong_so_tien') or '?'} - "
                    f"💰 {result.get('tid') or '?'} - "
                    f"📄 {result.get('so_hoa_don') or ''} - "
                    f"🧾 {result.get('so_lo') or ''} - "
                    f"🖥️ {result.get('ten_may_pos') or ''}"
                )
        for item in list_data:
            item["KẾT TOÁN"] = sum
            # Ghi dữ liệu
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
                sheet = spreadsheet.worksheet("Unknown")
        await append_multiple_by_headers(sheet, list_data)


        db.close()
        if res_mess:
            reply_msg = "✅ Đã xử lý các hóa đơn:\n\n" + "\n".join(res_mess)
        else:
            reply_msg = "⚠️ Không xử lý được hóa đơn nào."

        await message.reply_text(reply_msg)


async def insert_bill_row(db: AsyncMySQLConnector, row):
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
            so_lo,
            so_hoa_don,
            ten_may_pos,
            caption_goc
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    await db.execute(query, row)

def parse_message_rut(text):
    data = {}
    if not text:
        return None

    patterns = {
        "khach": r"Khach:\s*\{(.+?)\}",
        "sdt": r"Sdt:\s*\{(\d{9,11})\}",
        "rut": r"Rut:\s*\{(.+?)\}",
        "phi": r"Phi:\s*\{([\d.]+%)\}",
        "tien_phi": r"(?:TienPhi|DienPhi):\s*\{(.+?)\}",
        "chuyen_khoan": r"ChuyenKhoan:\s*\{(.+?)\}",
        "lich_canh_bao": r"LichCanhBao:\s*\{(\d+)\}",
        "stk": r"STK:\s*(?:\{)?(.+?)(?:\})?(?:\n|$)",
        "note": r"Note:\s*\{(.+?)\}"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    # Nếu không có note mà dòng cuối có thể là ghi chú
    last_line = text.strip().split('\n')[-1]
    if 'note' not in data and not any(k.lower() in last_line.lower() for k in ['khach:', 'stk:', 'chuyenkhoan:', '{']):
        data['note'] = last_line.strip()

    return data


def parse_message_dao(text):
    data = {}
    if not text:
        return None

    # Các pattern tương ứng với định dạng: Trường: {giá trị}
    patterns = {
        "khach": r"Khach:\s*\{(.+?)\}",
        "sdt": r"Sdt:\s*\{(\d{9,11})\}",
        "dao": r"Dao:\s*\{([\d.,a-zA-Z ]+)\}",
        "phi": r"Phi:\s*\{([\d.]+%)\}",
        "tien_phi": r"TienPhi:\s*\{([\d.,a-zA-Z ]+)\}",
        "rut_thieu": r"RutThieu:\s*\{([\d.,a-zA-Z ]+)\}",
        "tong": r"Tong:\s*\{([\d.,a-zA-Z ]+)\}",
        "lich_canh_bao": r"LichCanhBao:\s*\{(\d+)\}",
        "note": r"Note:\s*\{(.+?)\}"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    # Nếu không có note mà dòng cuối là ghi chú thì gán
    last_line = text.strip().split('\n')[-1]
    if 'note' not in data and not any(k in last_line.lower() for k in ['khach:', 'stk:', 'chuyenkhoan:', '{']):
        data['note'] = last_line.strip()

    return data


