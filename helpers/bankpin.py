from unidecode import unidecode

class BankBin:
    """
    Tiện ích để tra cứu BIN của ngân hàng từ tên.
    Dùng chung trong toàn bộ project.
    """
    _BANK_BIN_MAP = {
        "abbank": "970425",
        "acb": "970416",
        "agribank": "970405",
        "anbinhcommercialjointstockbank": "970425",
        "asiacommercialbank": "970416",
        "bankforinvestmentanddevelopmentofvietnam": "970418",
        "banvietcommercialjontstockbank": "970454",
        "baovietbank": "970438",
        "baovietjointstockcommercialbank": "970438",
        "bidv": "970418",
        "cimb": "422589",
        "cimbbankvietnamlimited": "422589",
        "dab": "970406",
        "dongabank": "970406",
        "dongacommercialjointstockbank": "970406",
        "eib": "970431",
        "eximbank": "970431",
        "globalpetrocommercialjointstockbank": "970408",
        "gpbank": "970408",
        "hdbank": "970437",
        "hlo": "970442",
        "hongleongbankvietnam": "970442",
        "housingdevelopmentbank": "970437",
        "indovinabank": "970434",
        "ivb": "970434",
        "jointstockcommercialbankforforeigntradeofvietnam": "970436",
        "kienlongbank": "970452",
        "kienlongcommercialjointstockbank": "970452",
        "lienvietbank": "970449",
        "lienvietpostbank": "970449",
        "lpb": "970449",
        "maritimebank": "970426",
        "mb": "970422",
        "mbbank":"970422",
        "militarycommercialjointstockbank": "970422",
        "msb": "970426",
        "nab": "970428",
        "namabank": "970428",
        "namacommercialjointstockbank": "970428",
        "nasb": "970409",
        "nasbank": "970409",
        "nationalcitizenbank": "970419",
        "ncb": "970419",
        "northasiacommercialjointstockbank": "970409",
        "ocb": "970448",
        "oceanbank": "970414",
        "oricombank": "970448",
        "orientcommercialjointstockbank": "970448",
        "petrolimexgroupcommercialjointstockbank": "970430",
        "pgbank": "970430",
        "phuongdongbank": "970448",
        "pvcombank": "970412",
        "sacombank": "970403",
        "saigonbank": "970400",
        "saigonbankforindustryandtrade": "970400",
        "saigoncommercialjointstockbank": "970429",
        "saigonhanoicommercialjointstockbank": "970443",
        "saigonthuongtincommercialjointstockbank": "970403",
        "scb": "970429",
        "seabank": "970440",
        "shb": "970443",
        "shinhanbank": "970424",
        "southeastasiacommercialjointstockbank": "970440",
        "tcb": "970407",
        "techcombank": "970407",
        "unitedoverseabank": "970458",
        "uob": "970458",
        "vab": "970427",
        "vbard": "970405",
        "vcb": "970436",
        "TPB": "970423",
        "TPBank": "970423",
        "vib": "970441",
        "vibank": "970441",
        "vidpublic": "970439",
        "vienambankforagricultureandruraldevelopment": "970405",
        "vietabank": "970427",
        "vietacommercialjointstockbank": "970427",
        "vietbank": "970433",
        "vietcapitalbank": "970454",
        "vietcombank": "970436",
        "vietinbank": "970415",
        "vietnamexportimportcommercialjointstockbank": "970431",
        "vietnaminternationalcommercialjointstockbank": "970441",
        "vietnamjointstockcommercialbankforindustryandtrade": "970415",
        "vietnamprosperityjointstockcommercialbank": "970432",
        "vietnamrussiabank": "970421",
        "vietnamtechnologicalandcommercialjointstockbank": "970407",
        "vietnamthuongtincommercialjointstockbank": "970433",
        "vpbank": "970432",
        "vrb": "970421",
        "whhn": "970457",
        "wooribankhanoi": "970457",
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