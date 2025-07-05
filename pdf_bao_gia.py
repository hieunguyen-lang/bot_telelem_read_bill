from fpdf import FPDF

class PDFQuote(FPDF):
    def header(self):
        
        self.set_font("DejaVu", "B", 12)
        self.cell(
            0, 10,
            "BÁO GIÁ PHÁT TRIỂN BOT TELEGRAM & WEBSITE QUẢN LÝ HÓA ĐƠN (DÙNG LLM GPT)",
            ln=True, align="C"
        )
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, f"Trang {self.page_no()}", align="C")


pdf = PDFQuote()
# Thêm font DejaVu Unicode
pdf.add_font("DejaVu", "", "C:/Users/Admin/Documents/tool/bot_tele_/bot_telelem_read_bill/dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf", uni=True)
pdf.add_font("DejaVu", "B", "C:/Users/Admin/Documents/tool/bot_tele_/bot_telelem_read_bill/dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Bold.ttf", uni=True)
pdf.add_font("DejaVu", "I", "C:/Users/Admin/Documents/tool/bot_tele_/bot_telelem_read_bill/dejavu-fonts-ttf-2.37/ttf/DejaVuSans-Oblique.ttf", uni=True)
pdf.set_font("DejaVu", "", 11)
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)



pdf.multi_cell(0, 8, "Người báo giá: Freelancer Nguyễn Khắc Hiếu\nNgày báo giá: 02/07/2025")
pdf.ln(5)

# Bot Telegram
pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "1. BOT TELEGRAM – 6.000.000 VNĐ", ln=True)
pdf.set_font("DejaVu", "", 11)
bot_text = """• Nhận ảnh từ group Telegram (ảnh đơn hoặc nhóm)
• Chuẩn hóa caption, kiểm tra đủ trường (khách, sdt, loại giao dịch, phí,…)
• Chuyển ảnh sang base64, gửi lên LLM (OpenAI/Gemini) kèm prompt để trích xuất thông tin JSON
• Xử lý kết quả JSON: loại trùng, kiểm tra thiếu trường → cảnh báo
• Tính phí dịch vụ và phản hồi người gửi
• Ghi dữ liệu vào MySQL + Google Sheet
• Ghi trạng thái xử lý vào Redis (chống trùng)
• Lệnh /hoahong tính hoa hồng cho từng user
• Gửi báo cáo định kỳ: danh sách khách đến hạn kết toán ngày mai
• Tra cứu hóa đơn theo tên khách, số hóa đơn, MID, TID…
• Backup DB + script khởi tạo
⏱️ Thời gian: 5–6 ngày làm việc"""
pdf.multi_cell(0, 8, bot_text)
pdf.ln(3)

# Website
pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "2. WEBSITE DASHBOARD PHÂN QUYỀN & BÁO CÁO – 7.000.000 VNĐ", ln=True)
pdf.set_font("DejaVu", "", 11)
web_text = """• Giao diện quản trị hóa đơn (React/Next.js + TailwindCSS)
• Kết nối MySQL, hiển thị dữ liệu dạng bảng
• Phân quyền đăng nhập: admin / nhân viên / kế toán
• Bộ lọc nâng cao: ngày, khách, ngân hàng, loại giao dịch...
• Tìm kiếm nhanh, xuất dữ liệu ra Excel
• Báo cáo hoa hồng: thống kê hoa hồng từng nhân viên theo tháng/quý/năm, biểu đồ trực quan
• Lịch hóa đơn: theo dõi các hóa đơn đến hạn kết toán dưới dạng calendar view
• Backend API: FastAPI hoặc ExpressJS, bảo mật JWT
• Giao diện dễ dùng, hỗ trợ mobile
⏱️ Thời gian: 7–8 ngày làm việc"""
pdf.multi_cell(0, 8, web_text)
pdf.ln(3)

pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "TỔNG CHI PHÍ TOÀN DỰ ÁN: 13.000.000 VNĐ", ln=True)
pdf.ln(3)

# Lưu ý
pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "Lưu ý khi dùng LLM GPT:", ln=True)
pdf.set_font("DejaVu", "", 11)
note_text = """✅ Độ chính xác cao hơn OCR, nhận diện được mẫu đa dạng
✅ Chi phí mỗi lần gọi API: khoảng 0.002–0.03 USD / ảnh (tự đăng ký API key OpenAI/Gemini)
✅ Có thể tối ưu prompt để giảm số token tiêu thụ"""
pdf.multi_cell(0, 8, note_text)
pdf.ln(3)

# Tùy chọn
pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "TÙY CHỌN MỞ RỘNG:", ln=True)
pdf.set_font("DejaVu", "", 11)
addons_text = """• Hybrid OCR + LLM fallback: +1.000.000 VNĐ
• Dashboard biểu đồ thống kê nâng cao: +2.000.000 VNĐ
• Tách group nhiều team riêng: +1.000.000 VNĐ
• Tích hợp Docker & CI/CD: +1.000.000 VNĐ"""
pdf.multi_cell(0, 8, addons_text)
pdf.ln(3)

# Thời gian
pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "THỜI GIAN TRIỂN KHAI:", ln=True)
pdf.set_font("DejaVu", "", 11)
time_text = """→ Bot Telegram: ~5–6 ngày
→ Website dashboard: ~7–8 ngày
→ Tổng dự án: ~12–14 ngày làm việc"""
pdf.multi_cell(0, 8, time_text)

# Xuất PDF
pdf_path = "Bao_gia_Bot_Telegram_Web_HoaDon_LLM_GPT.pdf"
pdf.output(pdf_path)
print(f"✅ Đã tạo PDF báo giá: {pdf_path}")
