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
        self.model = genai.GenerativeModel('gemini-2.0-flash') # Sử dụng model vision cho input hình ảnh

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
            
            invoice_extraction_prompt = """
            Bạn là một chuyên gia phân tích hóa đơn tài chính. Hãy phân tích hình ảnh hóa đơn được cung cấp và trích xuất các thông tin sau vào định dạng JSON. Nếu một trường không xuất hiện hoặc không thể xác định rõ ràng từ hóa đơn, hãy gán giá trị null cho trường đó
            ❗ **Lưu ý quan trọng:**
                - Nếu đây là hóa đơn chuyển tiền ngân hàng cá nhân (ví dụ như từ app ngân hàng Sacombank, Techcombank, VPBank,... mà chỉ chứa nội dung như “Giao dịch thành công”, “Chuyển khoản thành công”, “Người nhận”, “Mã giao dịch”, “Số tiền”, mà không có thông tin máy POS, MID/TID, mã số hóa đơn, số lô,…), thì đây **không phải là hóa đơn thanh toán POS**, hãy **trả về: `null`.
                - Chỉ xử lý và trích xuất nếu hóa đơn là loại **"THANH TOÁN"** POS thực sự.
                - Nếu hóa đơn là loại: **"BÁO CÁO CHI TIẾT"**, **"BÁO CÁO KẾT TOÁN"**, **"KẾT TOÁN THÀNH CÔNG"**, **"TỔNG KẾT"**, v.v... thì **không trích xuất gì cả, hãy trả về: `null`**.

            Nếu hóa đơn là loại "THANH TOÁN" POS hợp lệ, hãy trích xuất các trường sau vào 1 đối tượng JSON:
            **YÊU CẦU QUAN TRỌNG:**
            - Tên các trường (keys) trong đối tượng JSON phải **chính xác** như liệt kê bên dưới.
            - Nếu một trường không tìm thấy trên hóa đơn hoặc không rõ ràng, gán giá trị là `null`.
            - Tất cả giá trị số tiền phải loại bỏ dấu phân cách hàng nghìn (chỉ dùng số, ví dụ: `"5020000"` thay vì `"5.020.000"`).
            **Các trường cần trích xuất:**
            1. "ten_ngan_hang":  
            Tên ngân hàng phát hành hóa đơn, hoặc tên đơn vị chấp nhận thanh toán (ví dụ: "HDBank", "MB", "VPBank", "MPOS",...). Ưu tiên tên ngân hàng, nếu không có thì lấy tên thương hiệu thanh toán nổi bật.
            2. "ngay_giao_dich":  
            Ngày giao dịch, chuẩn hóa định dạng thành "YYYY-MM-DD". Tìm kiếm nhãn như: "Ngày:", "NGÀY:", "DATE:", "Ngày giao dịch:".
            3. "gio_giao_dich":  
            Giờ giao dịch, chuẩn hóa định dạng thành "HH:MM:SS". Tìm kiếm nhãn như: "Giờ:", "GIỜ:", "TIME:", "Giờ giao dịch:".
            4. "tong_so_tien":  
            Tổng số tiền giao dịch. Trả về giá trị dạng số, không có dấu phân cách hàng nghìn (ví dụ: "1250000").
            5. "tid":  
            Mã thiết bị POS. Tìm nhãn như: "TID:", "Terminal ID:", "Mã thiết bị:", "Mã POS:".  
            **Lưu ý**: Nếu hóa đơn có dòng "MID/TIT: xxx/yyy", thì phần `yyy` (sau dấu `/`) là giá trị `tid`.
            6. "mid":  
            Mã đơn vị chấp nhận thẻ. Tìm nhãn như: "MID:", "Merchant ID:", "Mã ĐVCNT:", "Mã đơn vị:".  
            **Lưu ý**: Nếu hóa đơn có dòng "MID/TIT: xxx/yyy", thì phần `xxx` (trước dấu `/`) là giá trị `mid`.
            7. "so_lo":  
            Số lô giao dịch. Tìm nhãn như: "Batch:", "BATCH:", "Số lô:", "Lô:".
            8. "so_tham_chieu":  
            Số tham chiếu. Tìm nhãn như: "Số tham chiếu:", "REF:", "TRACE No:", "SỐ HÓA ĐƠN:", "REFERENCE:".
            9. "so_hoa_don":  
            Số hóa đơn hoặc mã giao dịch cụ thể. Tìm nhãn như: "Số hóa đơn:", "SỐ HÓA ĐƠN:", ". H.ĐƠN:", "Số giao dịch:", "Transaction ID:", "Receipt No:", "Hóa đơn số:", kể cả khi viết hoa toàn bộ,Hãy cố gắng nhận dạng cả những trường hợp `SỐ HÓA ĐƠN` viết hoa, có thể nằm ở dòng giữa hoặc cuối hóa đơn".
            10. "loai_giao_dich":  
            Loại giao dịch, ví dụ: "Thanh Toán", "Rút Tiền", "Hoàn Tiền", "Kết Toán",... Nếu không có, để null.
            11. "ten_may_pos":  
            Tên máy POS hoặc tên điểm giao dịch in trên hóa đơn, ví dụ: "XIXI GAMING 2", "GAS NGUYEN LONG 1",... Nếu không thấy, để null.
            12. "so_the":  
            Số thẻ được sử dụng để thanh toán, bao gồm cả phần bị ẩn. Tìm kiếm các chuỗi dạng như: `"4413 57** **** 8787"`, `"5138 **** **** 0890"` hoặc tương tự. Nếu không thấy, để null.
            **YÊU CẦU ĐẦU RA:**
            - Trả về đúng 1 đối tượng JSON chứa đầy đủ 12 trường trên.
            - Không thêm giải thích hoặc văn bản nào khác ngoài đối tượng JSON.
            - Đảm bảo JSON hợp lệ.
            Ví dụ đầu ra:
            {
            "ten_ngan_hang": "HDBank",
            "ngay_giao_dich": "2025-06-19",
            "gio_giao_dich": "13:06:25",
            "tong_so_tien": "50200000",
            "tid": "54235423454",
            "mid": "234234234",
            "so_lo": "000820",
            "so_tham_chieu": "517019445360",
            "so_hoa_don": "000456",
            "loai_giao_dich": "Thanh Toán",
            "ten_may_pos": "XIXI GAMING 2",
            "so_the": "4413 57** **** 8787"
            }
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
            response = self.model.generate_content(contents)
            #print(response.text)
           

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

