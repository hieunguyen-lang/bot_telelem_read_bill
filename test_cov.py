from gemi_ai import GeminiBillAnalyzer

if __name__ == "__main__":
    analyzer = GeminiBillAnalyzer(api_key="AIzaSyDr7eBWYiltQcIFGz6TvU8KMyUzls3VCFg")
    invoice_extraction_prompt = """
    Bạn là một chuyên gia phân tích hóa đơn tài chính. Hãy phân tích hình ảnh hóa đơn được cung cấp và trích xuất các thông tin sau vào định dạng JSON. Nếu một trường thông tin không xuất hiện hoặc không thể xác định rõ ràng trên hóa đơn, hãy gán giá trị null cho trường đó.

    Các trường thông tin cần trích xuất bao gồm:

    "ten_ngan_hang": Tên của ngân hàng phát hành hóa đơn, tên của đơn vị chấp nhận thanh toán (ví dụ: "MPOS", "MB", "HDBank", "VPBank"), hoặc tên của tổ chức tài chính trung gian nếu có. Ưu tiên tên ngân hàng nếu có, nếu không tìm thấy, tìm tên thương hiệu dịch vụ thanh toán nổi bật.

    "ten_don_vi_ban": Tên của đơn vị bán hàng hoặc cung cấp dịch vụ. Tìm kiếm các nhãn như "Tên đơn vị:", "Cửa hàng:", "Tên Đại lý:", hoặc tên thương hiệu chính của doanh nghiệp.

    "dia_chi_don_vi_ban": Địa chỉ đầy đủ của đơn vị bán hàng hoặc cung cấp dịch vụ. Tìm kiếm các nhãn như "Địa chỉ:", "Đ/C:", "ĐỊA CHỈ ĐẠI LÝ:", hoặc các dòng địa chỉ liên quan đến doanh nghiệp.

    "ngay_giao_dich": Ngày giao dịch diễn ra. Chuẩn hóa định dạng thành YYYY-MM-DD. Tìm kiếm các nhãn như "Ngày:", "NGÀY:", "DATE:", "Ngày giao dịch:".

    "gio_giao_dich": Giờ giao dịch diễn ra. Chuẩn hóa định dạng thành HH:MM:SS. Tìm kiếm các nhãn như "Giờ:", "GIỜ:", "TIME:", "Giờ giao dịch:".

    "tong_so_tien": Tổng số tiền cuối cùng của giao dịch. Giá trị này phải là một số (hoặc chuỗi số) và không chứa ký tự phân tách hàng nghìn (ví dụ: "10200000" thay vì "10.200.000").

    "don_vi_tien_te": Ký hiệu hoặc mã loại tiền tệ được sử dụng (ví dụ: "VND", "USD"). Tìm kiếm gần tổng số tiền.

    "loai_the": Loại thẻ được sử dụng nếu thanh toán bằng thẻ (ví dụ: "Mastercard", "Visa", "ATM", "NAPAS"). Tìm kiếm các nhãn như "Loại thẻ:", "Thẻ:", "Card Type:", hoặc tên logo thẻ. Nếu không có thông tin về thẻ, hãy để là null.

    "ma_giao_dich": Mã giao dịch duy nhất. Tìm kiếm các nhãn như "Mã GD:", "Số giao dịch:", "Transaction ID:", "TID:", "Mã tham chiếu:".

    "ma_don_vi_chap_nhan": Mã định danh của đơn vị chấp nhận thẻ. Tìm kiếm các nhãn như "Mã ĐV:", "Merchant ID:", "MID:", "Mã ĐVCNT:".

    "so_lo": Số lô giao dịch. Tìm kiếm các nhãn như "Số lô:", "Lô:", "Batch No:", "BATCH:", "Số lô:".

    "so_tham_chieu": Số tham chiếu bổ sung (nếu có). Tìm kiếm các nhãn như "Mã chuẩn chi:", "Mã tham chiếu:", "TRACE No/SỐ HÓA ĐƠN:".

    "loai_giao_dich": Loại giao dịch (ví dụ: "Thanh Toán", "KẾT TOÁN", "RÚT TIỀN"). Nếu không có, để null.

    Hãy đảm bảo rằng JSON trả về là một đối tượng hợp lệ chứa tất cả các trường trên.
    """
    result = analyzer.analyze_bill(r"C:\Users\Admin\Downloads\hdbank.jpg", invoice_extraction_prompt)
    print(result)