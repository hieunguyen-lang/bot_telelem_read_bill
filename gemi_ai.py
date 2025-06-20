import base64
from PIL import Image
import io
import google.generativeai as genai
import json
import os
import re
class GeminiBillAnalyzer:
    def __init__(self, api_key=''):
        genai.configure(api_key=api_key)

    @staticmethod
    def image_to_base64(image_path):
        """
        Chuyển đổi hình ảnh từ đường dẫn file sang chuỗi Base64.
        """
        try:
            with Image.open(image_path) as img:
                # Chuyển đổi sang RGB nếu hình ảnh có chế độ khác (ví dụ: RGBA) để tránh lỗi với một số API
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG') # Hoặc 'PNG' tùy thuộc vào định dạng mong muốn
                encoded_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                return encoded_img
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file hình ảnh tại {image_path}")
            return None
        except Exception as e:
            print(f"Lỗi khi chuyển đổi hình ảnh sang Base64: {e}")
            return None

    def analyze_bill(self, base64_str):
        if not base64_str:
            print("Không thể chuyển đổi hình ảnh.")
            return None
        try:
            model = genai.GenerativeModel('gemini-1.5-flash') # Sử dụng model vision cho input hình ảnh
            invoice_extraction_prompt = """
                Bạn là một chuyên gia phân tích hóa đơn tài chính. Hãy phân tích hình ảnh hóa đơn được cung cấp và trích xuất các thông tin sau vào định dạng JSON. Nếu một trường thông tin không xuất hiện hoặc không thể xác định rõ ràng trên hóa đơn, hãy gán giá trị null cho trường đó.
                **QUAN TRỌNG:** Tên các trường (keys) trong đối tượng JSON phải chính xác như được liệt kê dưới đây. Nếu một trường thông tin không xuất hiện hoặc không thể xác định rõ ràng trên hóa đơn, hãy gán giá trị `null` cho trường đó.
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
            # Tạo nội dung cho request, bao gồm hình ảnh và văn bản
            contents = [
                {
                    "parts": [
                        {
                            "mime_type": "image/jpeg", # Hoặc "image/png" tùy thuộc vào định dạng bạn đã lưu
                            "data": base64_str
                        },
                        {
                            "text": invoice_extraction_prompt
                        }
                    ]
                }
            ]

            print("Đang gửi yêu cầu đến Gemini API...")
            response = model.generate_content(contents)
            print(response.text)
           

            # Áp dụng regex TRÊN BIẾN NÀY (raw_llm_response_text)
            
            # Cố gắng phân tích phản hồi thành JSON
            try:
                #json_data = json.loads(json_match.group(1))
                json_match = re.search(r'```json\s*(\{.*?\})\s*```|(\{.*\})', response.text, re.DOTALL)
                if json_match:
                    raw_json = json_match.group(1) or json_match.group(2)
                    try:
                        parsed = json.loads(raw_json)
                        print("✅ Phân tích JSON thành công:", parsed)
                        return parsed
                    except json.JSONDecodeError as e:
                        print("❌ Không thể decode JSON:", e)
                        return None
                else:
                    print("⚠️ Không tìm thấy JSON trong phản hồi.")
                    return None
                
            except json.JSONDecodeError:
                print("Lỗi: Phản hồi từ LLM không phải là JSON hợp lệ.")
                return {"raw_text_response": response.text, "error": "Invalid JSON from LLM"}

        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")
            return None

# Ví dụ sử dụng:
# analyzer = GeminiBillAnalyzer(api_key="YOUR_API_KEY")
# image_file = r"C:\Users\Admin\Documents\tool\bottele_check_bill\hdbank.jpg"
# prompt = """
# Phân tích thông tin từ hóa đơn này và trích xuất các thông tin sau vào định dạng JSON:
# - "bank_name": Tên ngân hàng
# - "merchant_name": Tên đơn vị chấp nhận thẻ
# - "merchant_address": Địa chỉ đơn vị chấp nhận thẻ
# - "transaction_date": Ngày giao dịch (định dạng YYYY-MM-DD)
# - "transaction_time": Giờ giao dịch (định dạng HH:MM:SS)
# - "total_amount": Tổng số tiền
# - "currency": Loại tiền tệ (ví dụ: VND)
# - "card_type": Loại thẻ (ví dụ: Mastercard)
# - "transaction_id": ID giao dịch (TID)
# - "merchant_id": ID đơn vị chấp nhận thẻ (MID)
# - "batch_number": Số lô (Lô)
# - "ivn": Số IVN (Internal Voucher Number)
# Nếu một thông tin không có, hãy để giá trị là null.
# """
# result = analyzer.analyze_bill(image_file, prompt)
# print(result)

