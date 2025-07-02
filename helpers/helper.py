
from io import BytesIO
from PIL import Image
import base64
from rapidfuzz import fuzz
import re
import unicodedata
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