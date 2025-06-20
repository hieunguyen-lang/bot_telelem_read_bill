from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Admin\Documents\tool\bottele_check_bill\tesseract.exe"
def extract_bill_info(image_path):
    # Xử lý ảnh
    img = Image.open(image_path).convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(3)
    img = img.point(lambda x: 0 if x < 150 else 255, '1')
    img.save("processed_hdbank_bill.jpg")  # Lưu lại để kiểm tra

    # OCR tiếng Việt + Anh
    text = pytesseract.image_to_string(img, lang="eng")
    print (f"📄 Đã trích xuất văn bản:\n{text}\n")
    return extract_all_info(text)
    
def extract_all_info(text):
    # Tên chủ thẻ (ví dụ: LÊ THỊ DUNG)
    name = re.search(r"LÊ THỊ DUNG", text, re.IGNORECASE)
    name = name.group(0) if name else None

    # Ngày giờ (dạng dd/mm/yyyy hh:mm:ss)
    datetime = re.search(r"(\d{1,2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})", text)
    datetime = datetime.group(1) if datetime else None

    # Số lô (BATCH No/SỐ LÔ)
    batch = re.search(r"BATCH\s*No\S*\s*[:\-]?\s*([0-9]+)", text, re.IGNORECASE)
    batch = batch.group(1) if batch else None

    # TID
    tid = re.search(r"TID[:\s]*([0-9]+)", text)
    tid = tid.group(1) if tid else None

    # Số thẻ (4 số cuối, ví dụ: xxxx1234)
    card = re.search(r"SỐ THẺ[:\s]*([0-9Xx*]{4,})", text)
    card = card.group(1) if card else None

    # Số hóa đơn
    invoice = re.search(r"SỐ HÓA ĐƠN[:\s]*([0-9]+)", text)
    invoice = invoice.group(1) if invoice else None

    # Tên POS (tên đại lý, ví dụ: XE VẬN TẢI VẠN KIÊN 2)
    pos = re.search(r"TÊN ĐẠI LÝ[:\s]*(.+)", text)
    pos = pos.group(1).strip() if pos else None

    # Số tiền (TỔNG CỘNG hoặc TỔNG KẾT)
    total = re.search(r"TỔNG CỘNG\s*VND?([\d,\.]+)", text, re.IGNORECASE)
    if not total:
        total = re.search(r"TỔNG KẾT\s*VND?([\d,\.]+)", text, re.IGNORECASE)
    total = total.group(1) if total else None

    return {
        "name": name,
        "datetime": datetime,
        "batch": batch,
        "tid": tid,
        "card": card,
        "invoice": invoice,
        "pos": pos,
        "total": total,
        "raw_text": text
    }
if __name__ == "__main__":
    info = extract_bill_info(r"C:\Users\Admin\Documents\tool\bottele_check_bill\hdbank.jpg")  # Đổi thành tên file ảnh của bạn
    print("====== THÔNG TIN HÓA ĐƠN ======")
    print(f"👤 Chủ thẻ      : {info.get('name')}")
    print(f"🕒 Ngày giờ     : {info.get('datetime')}")
    print(f"🏢 Tên POS      : {info.get('pos')}")
    print(f"🆔 TID          : {info.get('tid')}")
    print(f"🔢 Số lô        : {info.get('batch')}")
    print(f"💳 Số thẻ       : {info.get('card')}")
    print(f"🧾 Số hóa đơn   : {info.get('invoice')}")
    print(f"💰 Số tiền      : {info.get('total')}")
    print("===============================")