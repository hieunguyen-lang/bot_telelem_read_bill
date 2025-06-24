import os
import json
import re
from google import genai
from google.genai import types
from google.auth import default
from google.auth.credentials import Credentials


class GeminiBillAnalyzer:
    def __init__(self):
        # Lấy thông tin xác thực mặc định từ môi trường (ADC - Application Default Credentials)
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        self.client = genai.Client(
            vertexai=True,
            project="e-caldron-463814-p7",
            location="global",
            credentials=credentials  
        )
        self.model = "gemini-2.5-flash"

    def analyze_bill(self, base64_str):
        if not base64_str:
            print("Không thể chuyển đổi hình ảnh.")
            return None
        try:
            invoice_extraction_prompt = """
                🧠 Prompt AI Toàn Diện Trích Xuất Dữ Liệu Giao Dịch POS & MPOS

                🎯 Bối cảnh:
                Bạn là một trợ lý AI thông minh, chuyên trích xuất dữ liệu từ:

                - Hóa đơn máy POS của ngân hàng HDBank, MB Bank, VPBank (in giấy).
                - Ảnh màn hình "Chi tiết giao dịch" từ ứng dụng thanh toán MPOS tại Việt Nam.

                🎯 Nhiệm vụ:
                Phân tích hình ảnh được cung cấp và trích xuất thông tin vào định dạng JSON duy nhất bên dưới.

                ❗ Yêu cầu bắt buộc:
                1. Chỉ trả về đối tượng JSON hợp lệ.
                2. Không chứa văn bản thừa, markdown, giải thích hay ghi chú.
                3. Tất cả các trường phải có giá trị.
                - Nếu không xác định được → trả về chuỗi rỗng "" (không được dùng null).

                📤 Định dạng JSON đầu ra (bắt buộc):
                {
                "ten_ngan_hang": "string",
                "ten_may_pos": "string",
                "loai_giao_dich": "string",
                "ngay_giao_dich": "YYYY-MM-DD",
                "gio_giao_dich": "HH:MM:SS",
                "tong_so_tien": "string",
                "so_the": "string",
                "tid": "string",
                "mid": "string",
                "so_lo": "string",
                "so_hoa_don": "string",
                "so_tham_chieu": "string"
                }

                🔍 Hướng dẫn trích xuất từng trường:

                - ten_ngan_hang:
                - POS Giấy: Nhận diện từ logo/tên ngân hàng ở đầu hóa đơn.
                - MPOS: Nếu không có, trả về "".

                - ten_may_pos:
                - POS Giấy: Dưới logo, hoặc dòng chứa "TÊN ĐẠI LÝ:", "Cửa hàng:".
                - MPOS: Để "MPOS".

                - loai_giao_dich:
                - POS Giấy: "THANH TOÁN", "SALE",... → chuẩn hóa thành "Thanh Toán".
                - MPOS: "Thanh Toán".

                - ngay_giao_dich:
                - POS Giấy: Dòng "NGÀY/GIC", "NGÀY GIỜ", "Ngày:" → chuẩn "YYYY-MM-DD".
                - MPOS: Dòng "Ngày giao dịch".

                - gio_giao_dich:
                - POS Giấy: Cùng dòng với ngày.
                - MPOS: Dòng "Giờ giao dịch", định dạng HH:MM:SS.

                - tong_so_tien:
                - POS Giấy: Từ dòng "TỔNG TIỀN", "Tiền thực trả". Bỏ "đ", "VND", dấu ".".
                - MPOS: Số in to nhất, đầu màn hình. Chuẩn hóa như trên.

                - so_the:
                - POS Giấy: Dòng có số thẻ dạng "**** **** **** 1234".
                - MPOS: Dãy số che một phần, 4 số cuối.

                - tid:
                - POS Giấy: Dòng "TID:", hoặc phần sau trong dòng "Máy/Tid:".
                - MPOS: Dòng "Mã thiết bị".

                - mid:
                - POS Giấy: Dòng "MID:", hoặc phần trước trong "Máy/Tid:".
                - MPOS: Dòng "Mã ĐVCNT".

                - so_lo:
                - POS Giấy: Dòng "SỐ LÔ:", "BATCH No:".
                - MPOS: Dòng "Số lô".

                - so_hoa_don:
                - POS Giấy: Dòng "SỐ H.ĐƠN:", "TRACE No:", "Mã giao dịch:".
                - MPOS: Dòng "Mã giao dịch".

                - so_tham_chieu:
                - POS Giấy: Dòng "SỐ TC:", "REF No:", "Số tham chiếu:".
                - MPOS: Dòng "Mã tham chiếu".
            """

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/jpeg",
                                data=base64_str
                            )
                        ),
                        types.Part(text=invoice_extraction_prompt)
                    ]
                )
            ]

            config = types.GenerateContentConfig(
                temperature=1,
                top_p=1,
                seed=0,
                max_output_tokens=4096,
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
                ],
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
            )

            print("Đang gửi yêu cầu đến Gemini API...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )

            response_text = response.text if hasattr(response, 'text') else str(response)
            print(response_text)

            try:
                json_match = re.search(r'```json\s*(\{.*?\})\s*```|(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    raw_json = json_match.group(1) or json_match.group(2)
                    try:
                        parsed = json.loads(raw_json)
                        print("✅ Phân tích JSON thành công:", parsed)
                        return parsed
                    except json.JSONDecodeError as e:
                        print("❌ Không thể decode JSON:", e)
                else:
                    print("⚠️ Không tìm thấy JSON trong phản hồi.")
            except json.JSONDecodeError:
                print("Lỗi: Phản hồi từ LLM không phải là JSON hợp lệ.")

        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")

        return {
            "ten_ngan_hang": None,
            "ngay_giao_dich": None,
            "gio_giao_dich": None,
            "tong_so_tien": None,
            "tid": None,
            "mid": None,
            "so_lo": None,
            "so_tham_chieu": None,
            "so_hoa_don": None,
            "loai_giao_dich": None,
            "ten_may_pos": None,
            "so_the": None
        }
