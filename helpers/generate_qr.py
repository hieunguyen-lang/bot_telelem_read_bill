from .qr_pay import QRPay
from unidecode import unidecode
from PIL import Image
from io import BytesIO
from helpers.bankpin import BankBin

def normalize_bank_name(name: str) -> str:
    return unidecode(name).lower().replace(" ", "").replace("-", "")

def generate_qr_binary(account_no: str, bank_name: str, amount_str: str,noi_dung= "Chuyển khoản", new_width_ratio=2.0) -> BytesIO:
    """
    Tạo QR code dạng BytesIO (không lưu file), với canvas rộng hơn.
    """
    account_no = account_no.strip()
    bank_name_norm = normalize_bank_name(bank_name)
    bank_bin = BankBin.get_bin(bank_name_norm)
    if not bank_bin:
        raise ValueError(f"❌ Ngân hàng '{bank_name}' không được hỗ trợ.")

    amount = int(amount_str.strip().replace(",", "").replace(".", ""))

    qr = QRPay(
        bin_id=bank_bin,
        consumer_id=account_no,
        service_code="ACCOUNT",
        transaction_amount=amount,
        purpose_of_transaction=noi_dung,
        point_of_initiation_method="STATIC"
    )

    # Tạo QR code ra ảnh PIL
    qr_img: Image.Image = qr.generate_qr_pay_pil()

    w, h = qr_img.size
    new_w = int(w * new_width_ratio)
    new_h = h

    canvas = Image.new("RGB", (new_w, new_h), color="white")
    x_offset = (new_w - w) // 2
    canvas.paste(qr_img, (x_offset, 0))

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer