from .qr_pay import QRPay
from unidecode import unidecode
from PIL import Image
from io import BytesIO

BANK_BIN_MAP = {
    "vietcombank": "970436", "vcb": "970436",
    "bidv": "970418",
    "vietinbank": "970415", "ctg": "970415",
    "techcombank": "970407", "tech": "970407",
    "mb": "970422", "mbbank": "970422",
    "vp": "970432", "vpbank": "970432",
    "acb": "970416",
    "eximbank": "970431", "eib": "970431",
    "agribank": "970405", "vba": "970405",
    "sacombank": "970403", "stb": "970403",
    "seabank": "970440",
    "tpbank": "970423", "tp": "970423",
    "shb": "970443",
    "ocb": "970448", "orient": "970448",
    "vib": "970441",
    "hdbank": "970437", "hd": "970437",
    "bao-viet-bank": "970438", "baoviet": "970438",
    "pgbank": "970439",
    "ncb": "970419",
    "lienvietpostbank": "970449", "lpb": "970449",
    "scb": "970429",
    "abbank": "970425",
    "bacabank": "970409",
    "vietbank": "970433",
    "namabank": "970428", "nam-a": "970428",
    "banviet": "970454", "bvbank": "970454",
    "cbbank": "970444",
    "publicbank": "970439", "pb": "970439",
    "oceanbank": "970414",
    "gpbank": "970408",
    "pvn": "970430", "pvcombank": "970430"
}

def normalize_bank_name(name: str) -> str:
    return unidecode(name).lower().replace(" ", "").replace("-", "")

def generate_qr_binary(account_no: str, bank_name: str, amount_str: str, new_width_ratio=2.0) -> BytesIO:
    """
    Tạo QR code dạng BytesIO (không lưu file), với canvas rộng hơn.
    """
    account_no = account_no.strip()
    bank_name_norm = normalize_bank_name(bank_name)
    bank_bin = BANK_BIN_MAP.get(bank_name_norm)
    if not bank_bin:
        raise ValueError(f"❌ Ngân hàng '{bank_name}' không được hỗ trợ.")

    amount = int(amount_str.strip().replace(",", "").replace(".", ""))

    qr = QRPay(
        bin_id=bank_bin,
        consumer_id=account_no,
        service_code="ACCOUNT",
        transaction_amount=amount,
        purpose_of_transaction="Chuyen khoan",
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