from fpdf import FPDF
from fpdf.enums import XPos, YPos

class PDFQuote(FPDF):
    def header(self):
        self.set_font("Arial", "", 12)
        self.cell(
            0,
            10,
            "BÁO GIÁ PHÁT TRIỂN BOT TELEGRAM & WEBSITE QUẢN LÝ HÓA ĐƠN (DÙNG LLM GPT)",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="C"
        )
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.cell(0, 10, f"Trang {self.page_no()}", align="C")

pdf = PDFQuote()
pdf.add_font('Arial', '', 'C:/Windows/Fonts/arial.ttf', uni=True)  # add font trước add_page
pdf.set_auto_page_break(auto=True, margin=15)

pdf.add_page()
pdf.set_font("Arial", "", 11)

pdf.multi_cell(0, 8, "Người báo giá: Freelancer Nguyễn Khắc Hiếu\nNgày báo giá: 02/07/2025")
pdf.ln(5)

pdf.cell(0, 8, "1. BOT TELEGRAM – 6.000.000 VNĐ", ln=True)
bot_text = """• Nhận ảnh từ group Telegram (ảnh đơn hoặc nhóm)
• Chuẩn hóa caption, kiểm tra đủ trường (khách, sdt, loại giao dịch, phí,…)
• Chuyển ảnh sang base64, gửi lên LLM (OpenAI/Gemini) kèm prompt để trích xuất thông tin JSON
• Xử lý kết quả JSON: loại trùng, kiểm tra thiếu trường → cảnh báo
• Tính phí dịch vụ và phản hồi người gửi
• Ghi dữ liệu vào MySQL + Google Sheet
• Ghi trạng thái xử lý vào Redis (chống trùng)
• Lệnh /hoahong tính hoa hồng cho user
• Gửi báo cáo định kỳ: khách đáo/rút ngày mai
• Tra cứu hóa đơn theo tên khách, số hóa đơn, MID, TID…
• Backup DB + script khởi tạo
⏱️ Thời gian: 5–6 ngày làm việc"""
pdf.multi_cell(0, 8, bot_text)
pdf.ln(3)

pdf.cell(0, 8, "2. WEBSITE DASHBOARD PHÂN QUYỀN – 5.000.000 VNĐ", ln=True)
web_text = """• Giao diện quản trị hóa đơn (React/Next.js + TailwindCSS)
• Kết nối MySQL, hiển thị dữ liệu dạng bảng
• Phân quyền đăng nhập: admin / nhân viên / kế toán
• Bộ lọc nâng cao: ngày, khách, ngân hàng, loại giao dịch...
• Tìm kiếm nhanh, xuất dữ liệu ra Excel
• Backend API: FastAPI hoặc ExpressJS, bảo mật JWT
• Giao diện dễ dùng, hỗ trợ mobile
⏱️ Thời gian: 5–7 ngày làm việc"""
pdf.multi_cell(0, 8, web_text)
pdf.ln(3)

pdf.cell(0, 8, "TỔNG CHI PHÍ TOÀN DỰ ÁN: 11.000.000 VNĐ", ln=True)
pdf.ln(3)

pdf.cell(0, 8, "Lưu ý khi dùng LLM GPT:", ln=True)
note_text = """✅ Độ chính xác cao hơn OCR, nhận diện được mẫu đa dạng
✅ Chi phí mỗi lần gọi API: khoảng 0.001–0.03 USD / ảnh (tự đăng ký API key OpenAI/Gemini)
✅ Có thể tối ưu prompt để giảm số token tiêu thụ"""
pdf.multi_cell(0, 8, note_text)
pdf.ln(3)


# Xuất PDF
pdf.output("Bao_gia_Bot_Telegram_Web_HoaDon_LLM_GPT.pdf")
