from unidecode import unidecode

class BankBin:
    """
    Tiện ích để tra cứu BIN của ngân hàng từ tên.
    Dùng chung trong toàn bộ project.
    """
    _BANK_BIN_MAP = {
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

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Chuẩn hoá tên ngân hàng: bỏ dấu, viết thường, bỏ khoảng trắng, dấu -
        """
        return unidecode(name).lower().replace(" ", "").replace("-", "")

    @classmethod
    def get_bin(cls, name: str) -> str | None:
        """
        Trả về BIN tương ứng nếu hợp lệ, hoặc None.
        """
        key = cls.normalize_name(name)
        return cls._BANK_BIN_MAP.get(key)

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        Kiểm tra xem tên ngân hàng đã được hỗ trợ chưa.
        """
        return cls.get_bin(name) is not None

    @classmethod
    def all_supported(cls) -> dict:
        """
        Trả về dict chứa tất cả ngân hàng & BIN.
        """
        return cls._BANK_BIN_MAP.copy()