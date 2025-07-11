import base64
import re
import unicodedata
import html
from unidecode import unidecode
from rapidfuzz import fuzz
from io import BytesIO
from PIL import Image
from datetime import datetime
from helpers.bankpin import BankBin
DISPLAY_KEYS = {
    "khach": "Khach",
    "sdt": "Sdt",
    "rut": "Rut",
    "dao": "Dao",
    "phi": "Phi",
    "tien_phi": "TienPhi",
    "tong": "Tong",
    "lich_canh_bao": "LichCanhBao",
    "ck_vao": "ck_vao",
    "ck_ra": "ck_ra",
    "stk": "Stk",
    "note": "Note"
}
def format_missing_keys(missing):
    return [DISPLAY_KEYS.get(k, k) for k in missing]

def process_telegram_photo_to_base64(message_photo, max_width=800, quality=70) -> str:
    file = message_photo.get_file()
    bio = BytesIO()
    file.download(out=bio)
    bio.seek(0)

    image = Image.open(bio)

    if image.mode != "L":
        image = image.convert("L")

    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

    #image.save("resized_image.jpg", format="JPEG", quality=quality)

    resized_bio = BytesIO()
    image.save(resized_bio, format="JPEG", quality=quality)
    resized_bio.seek(0)

    return base64.b64encode(resized_bio.getvalue()).decode("utf-8")


def extract_amount_after_fee(text, threshold=80):
    try:
        # Danh sách các cụm mô tả hành động còn lại / chuyển lại
        keywords = [
            "còn lại", "chuyển lại", "thanh toán lại", "trả lại",
            "gửi lại", "chuyển cho khách", "trả khách", "chuyển khách"
        ]

        # Tìm tất cả các đoạn có dạng "cụm từ + số tiền"
        matches = re.findall(r'([\w\s\-]{4,30})\s+([\d.,]+[kKmM])', text)
        for phrase, amount in matches:
            for keyword in keywords:
                if fuzz.partial_ratio(keyword, phrase.lower()) >= threshold:
                    return amount
    except Exception as e:
        print(f"❌ Lỗi extract: {e}")
    return None

def parse_currency_input_int(value):
    """
    Chuyển chuỗi tiền tệ (kể cả có hậu tố k/m, dấu chấm, đ, ₫...) thành số nguyên.
    """
    if not value:
        return 0

    try:
        if isinstance(value, (int, float)):
            return int(value)

        s = str(value).strip().lower().replace(",", ".").replace(" ", "")
        
        # Nếu có hậu tố k/m
        km_match = re.match(r"([\d\.]+)([km])", s)
        if km_match:
            num, suffix = km_match.groups()
            num = float(num)
            if suffix == "k":
                num *= 1_000
            elif suffix == "m":
                num *= 1_000_000
            return int(num)

        # Không có hậu tố → giữ lại toàn bộ số
        digits_only = re.sub(r"[^\d]", "", s)
        return int(digits_only) if digits_only else 0

    except:
        return 0
def parse_percent(value: str) -> float:
    if not value:
        return 0.0
    try:
        cleaned = value.strip().replace(',', '.')
        if '%' in cleaned:
            cleaned = cleaned.replace('%', '')
            return float(cleaned) / 100
        else:
            return float(cleaned) / 100 if float(cleaned) > 1 else float(cleaned)
    except ValueError:
        return 0.0
    
def remove_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def contains_khach_moi(text: str, threshold: int = 85) -> bool:
    normalized = remove_accents(text).lower()
    # kiểm tra từng cụm từ
    words = normalized.split()
    for i in range(len(words) - 1):
        phrase = f"{words[i]} {words[i+1]}"
        if fuzz.ratio(phrase, "khach moi") >= threshold:
            return True
    return False


def parse_message_rut(text):
    data = {}
    if not text:
        return None

    patterns = {
        "khach": r"Khach\s*[:\-]\s*\{(.+?)\}",
        "sdt": r"Sdt\s*[:\-]\s*\{?(\d{9,11})\}?",
        "rut": r"Rut\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "phi": r"Phi\s*[:\-]\s*\{(.+?)\}",
        "tien_phi": r"TienPhi\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "tong": r"Tong\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "lich_canh_bao": r"LichCanhBao\s*[:\-]\s*\{(\d+)\}",
        "ck_vao": r"ck[_\s]?vao\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "ck_ra": r"ck[_\s]?ra\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "stk": r"Stk\s*[:\-]\s*(?:\{)?([^\n\}]+)(?:\})?",
        "note": r"Note\s*[:\-]\s*\{(.+?)\}"
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
        "khach": r"Khach\s*[:\-]\s*\{(.+?)\}",
        "sdt": r"Sdt\s*[:\-]\s*\{?(\d{9,11})\}?",
        "dao": r"Dao\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "phi": r"Phi\s*[:\-]\s*\{(.+?)\}",
        "tien_phi": r"TienPhi\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "tong": r"Tong\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "lich_canh_bao": r"LichCanhBao\s*[:\-]\s*\{(\d+)\}",
        "ck_vao": r"ck[_\s]?vao\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "ck_ra": r"ck[_\s]?ra\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "stk": r"Stk\s*[:\-]\s*(?:\{)?([^\n\}]+)(?:\})?",
        "note": r"Note\s*[:\-]\s*\{(.+?)\}"
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

def parse_message_momo(text):
    data = {}
    if not text:
        return None

    # Các pattern tương ứng với định dạng: Trường: {giá trị}
    patterns = {
        "khach": r"Khach\s*[:\-]\s*\{(.+?)\}",
        "phi": r"Phi\s*[:\-]\s*\{(.+?)\}",
        "ck_ra": r"ck[_\s]?ra\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "stk": r"Stk\s*[:\-]\s*(?:\{)?([^\n\}]+)(?:\})?",
        "note": r"Note\s*[:\-]\s*\{(.+?)\}"
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

def parse_message_doiung(text):
    data = {}
    if not text:
        return None

    # Các pattern tương ứng với định dạng: Trường: {giá trị}
    patterns = {
        "doitac": r"Doitac\s*[:\-]\s*\{(.+?)\}",
        "phi": r"Phi\s*[:\-]\s*\{(.+?)\}",
        "tong": r"Tong\s*[:\-]\s*\{([\d.,a-zA-Z ]+)\}",
        "note": r"Note\s*[:\-]\s*\{(.+?)\}"
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


def format_currency_vn(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except:
        return str(0)  # fallback nếu lỗi
    
def generate_invoice_key_simple(result: dict, ten_ngan_hang: str) -> str:
    """
    Tạo khóa duy nhất kiểm tra duplicate hóa đơn.
    Ưu tiên các trường gần như không thể trùng nhau trong thực tế:
    - Số hóa đơn
    - Số lô
    - Mã máy POS (TID)
    - MID
    - Ngày + Giờ giao dịch
    - Tên ngân hàng
    """
    print("[Tạo key redis]")
    def safe_get(d, key):
        return (d.get(key) or '').strip().lower()

    key = "_".join([
        safe_get(result, "sdt"),
        safe_get(result, "so_hoa_don"),
        safe_get(result, "so_lo"),
        safe_get(result, "gio_giao_dich"),
        safe_get(result, "tong_so_tien"),
        ten_ngan_hang
    ])
    print("[KEY]: ",key)
    return key
def safe_get(d, key):
        return (d.get(key) or '').strip().lower()


def remove_accents(s: str) -> str:
    """
    Loại bỏ dấu tiếng Việt & ký tự đặc biệt
    """
    s = unicodedata.normalize('NFD', s)
    s = s.encode('ascii', 'ignore').decode('utf-8')
    s = re.sub(r'\s+', '', s)  # bỏ toàn bộ khoảng trắng
    return s

def generate_invoice_dien(result: dict) -> str:
    print("[Tạo key redis]")

    def safe_get(d, key):
        return (d.get(key) or '').strip().lower()

    parts = [
        safe_get(result, "ten_khach_hang"),
        safe_get(result, "ma_khach_hang"),
        safe_get(result, "dia_chi"),
        safe_get(result, "so_tien"),
        safe_get(result, "ma_giao_dich"),
    ]

    parts_clean = [remove_accents(p) for p in parts]

    key = "_".join(parts_clean)

    print("[KEY]:", key)
    return key

def normalize_text(text):
    # Chuyển về lowercase, loại bỏ dấu tiếng Việt
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')  # Loại bỏ dấu
    return text

def is_cash_related(text, threshold=80):
    cash_keywords = [
        "tien mat", "tm", "khach dua", "dua tien", "tien khach dua",
        "thanh toan tien mat", "dua bang tien mat", "giao tien mat"
    ]

    norm_text = normalize_text(text)

    for keyword in cash_keywords:
        if fuzz.partial_ratio(keyword, norm_text) >= threshold:
            return True
    return False

def is_bill_ket_toan_related(text, threshold=80):
    cash_keywords = [
        "kết toán", "bill kết toán", "ket toan", "bill kt", "hoa don kt", "bang ke kt",
        "hóa đơn kết toán", "bill hóa đơn kết toán", "bảng kê kết toán",
    ]

    norm_text = normalize_text(text)

    for keyword in cash_keywords:
        if fuzz.partial_ratio(keyword, norm_text) >= threshold:
            return True
    return False


def fix_datetime(value) -> str:
    """
    Chuyển định dạng thời gian đầu vào thành 'YYYY-MM-DD HH:MM:SS'.
    Nếu None hoặc định dạng không đúng → trả về thời gian hiện tại.
    """
    if not value:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    value = value.strip()
    formats = [
        "%H:%M - %d/%m/%Y",  # có dấu -
        "%H:%M %d/%m/%Y",    # không dấu -
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    # fallback
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def tach_stk_nganhang_chutk(text: str):
    """
    Tách số tài khoản, tên ngân hàng và chủ tài khoản từ text.
    Trả về: (so_tai_khoan, ten_ngan_hang, chu_tai_khoan)

    Nếu text None/rỗng hoặc không hợp lệ: trả ('', '', '')
    """
    if not text:
        return '', '', ''

    text = text.strip()
    text = text.replace('.', '')
    text = text.replace(',', '')
    # Sử dụng regex để tìm STK
    match = re.search(r'\b\d{6,15}\b', text)
    if not match:
        return '', '', ''

    so_tai_khoan = match.group()
    phan_con_lai = text.replace(so_tai_khoan, '', 1).strip()

    # Bỏ dấu '-' nếu có
    if phan_con_lai.startswith('-'):
        phan_con_lai = phan_con_lai[1:].strip()

    # Tách phần còn lại theo dấu '-'
    parts = [p.strip() for p in phan_con_lai.split('-', 1)]

    if len(parts) == 2:
        ten_ngan_hang, chu_tai_khoan = parts
    elif len(parts) == 1:
        ten_ngan_hang, chu_tai_khoan = parts[0], ''
    else:
        ten_ngan_hang, chu_tai_khoan = '', ''

    return so_tai_khoan, ten_ngan_hang, chu_tai_khoan


def normalize_bank_name(name: str) -> str:
    """Chuẩn hoá tên ngân hàng để so khớp key trong map."""
    return unidecode(name).lower().replace(" ", "").replace("-", "")


def validate_stk_nganhang_chutk(text: str) -> tuple[bool, str]:
    """
    Kiểm tra text có đúng định dạng: STK - Ngân hàng - Chủ TK
    Và tên ngân hàng có hợp lệ không.
    Trả về: (True, "") hoặc (False, "lý do lỗi")
    """
    if not text or not text.strip():
        return False, "❌ Chuỗi trống."

    text = text.strip()

    parts = text.split('-')
    if len(parts) != 3:
        return False, "❌ Định dạng không hợp lệ. Cần đúng dạng: STK - Ngân hàng - Chủ TK."

    stk_raw, bank_raw, ctk_raw = [p.strip() for p in parts]
    print(stk_raw)
    print(bank_raw)
    print(ctk_raw)
    if not stk_raw:
        return False, "❌ Thiếu số tài khoản."
    if not re.fullmatch(r'[\d\.]{6,19}', stk_raw):
        return False, f"❌ Số tài khoản không hợp lệ (phải là 6–19 chữ số): {stk_raw}"
    
    if not bank_raw:
        return False, "❌ Thiếu tên ngân hàng."

    bank_norm = normalize_bank_name(bank_raw)
    if not BankBin.exists(bank_norm):
        return False, f"❌ Ngân hàng không hợp lệ hoặc không được hỗ trợ: {bank_raw}"

    if not ctk_raw:
        return False, "❌ Thiếu tên chủ tài khoản."

    return True, ""


def send_long_message(message, full_text, photo=None, max_len=1024):
    """
    Gửi full_text (str) kèm ảnh QR (nếu có), tự động chia nhỏ nếu quá dài.
    """
    if not full_text:
        message.reply_text("⚠️ Không xử lý được hóa đơn nào.", parse_mode="HTML")
        return

    # Cắt thành nhiều phần
    chunks = []
    while full_text:
        if len(full_text) <= max_len:
            chunks.append(full_text.strip())
            break

        split_pos = full_text.rfind('\n', 0, max_len)
        if split_pos == -1:
            split_pos = max_len

        chunks.append(full_text[:split_pos].strip())
        full_text = full_text[split_pos:].strip()

    # Gửi ảnh + phần đầu tiên
    if photo:
        message.reply_photo(
            photo=photo,
            caption=chunks.pop(0),
            parse_mode="HTML"
        )

    # Gửi phần còn lại
    for part in chunks:
        message.reply_text(part, parse_mode="HTML")