import os
from PIL import Image
from io import BytesIO
import base64
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class GPTBill_Analyzer:
    def __init__(self):
        # Lấy thông tin xác thực mặc định từ môi trường (ADC - Application Default Credentials)
        self.client = OpenAI(api_key=os.getenv("GPT_KEY"))

    def analyze_bill_gpt(self, base64_string):
        print("---------------GỬI ẢNH TỚI GPT API--------------")
        if not base64_string:
            print("Chuỗi ảnh không hợp lệ.")
            return None
        data_url = f"data:image/jpeg;base64,{base64_string}"
        try:
            response = self.client.responses.create(
                prompt={
                    "id": "pmpt_685c2e52caec8193a3e40f10de2c44430976694b2bec9c34",
                    "version": "10"
                },
                input=[
                    
                    {
                    "role": "user",
                    "content": [
                        {
                        "type": "input_text",
                        "text": "hãy trích xuất thông tin ảnh sau\n"
                        },
                        {
                        "type": "input_image",
                        "image_url": data_url
                        }
                    ]
                    },
                    {
                    "id": "msg_685c9ebe692c819999895dbf24a401920ca2074a920ef22e",
                    "role": "assistant",
                    "content": [
                        {
                        "type": "output_text",
                        "text": "{\n  \"ten_ngan_hang\": null,\n  \"ten_may_pos\": null,\n  \"loai_giao_dich\": null,\n  \"ngay_giao_dich\": null,\n  \"gio_giao_dich\": null,\n  \"tong_so_tien\": null,\n  \"so_the\": null,\n  \"tid\": null,\n  \"mid\": null,\n  \"so_lo\": null,\n  \"so_hoa_don\": null,\n  \"so_tham_chieu\": null\n}"
                        }
                    ]
                    }
                ],
                reasoning={},
                max_output_tokens=2048,
                store=True
            )
        
        # Lấy chuỗi JSON đã được "escape" từ GPT
            escaped_json_str = response.output[0].content[0].text

            # Parse thành dict
            bill_data = json.loads(escaped_json_str)
            print(bill_data)
            return bill_data
        except Exception as e:
            print(e)
            return None
    
        

# opent = GPTBill_Analyzer()
# image_url = image_to_base64_data_url(r"C:\Users\hieunk\Documents\hieunk-project\bot_telelem_read_bill\photo_2025-06-26_08-29-51.jpg")
# res = opent.analyze_bill_gpt(image_url)
# #print(json.dumps(res))