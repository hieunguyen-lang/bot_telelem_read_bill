import base64
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
load_dotenv()  # Tự động tìm và load từ .env
class GPT4oImageProcessor:
    def __init__(self, prompt_id: str, version: int = 1):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY is missing. Check your .env file or environment variables.")

        self.client = OpenAI(api_key=api_key)
        self.prompt_id = prompt_id
        self.version = version

    def process_base64_image(self, base64_string: str, instruction: str = "Ảnh cần xử lý ở dưới"):
        """Gửi ảnh base64 và instruction vào prompt đã lưu"""
        #base64_string = base64.b64encode(img_file.read()).decode('utf-8')
        
        image_url = f"data:image/jpeg;base64,{base64_string}"
        # Kiểm tra kỹ
        print(">>> START <<<")
        print("Preview:", repr(image_url[:100]))
        print("Starts with:", image_url.startswith("data:image/jpeg;base64,"))
        print("Length:", len(image_url))
        print(">>> END <<<")
        print("Gửi ảnh vào gpt....")
        response = self.client.responses.create(
            prompt={
                "id": "pmpt_685c2e52caec8193a3e40f10de2c44430976694b2bec9c34",
                "version": "3"
            },
            input=[
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": "sao tôi gửi qua api ko thấy trả về\n{\n  \"ten_ngan_hang\": \"HDBank\",\n  \"ten_may_pos\": \"GAS NGUYEN LONG 1\",\n  \"loai_giao_dich\": \"Thanh Toán\",\n  \"ngay_giao_dich\": \"2025-06-24\",\n  \"gio_giao_dich\": \"16:51:17\",\n  \"tong_so_tien\": \"12690000\",\n  \"so_the\": \"5128 24** **** 0666\",\n  \"tid\": \"19500292\",\n  \"mid\": \"01950072140006\",\n  \"so_lo\": \"000021\",\n  \"so_hoa_don\": \"000022\",\n  \"so_tham_chieu\": null\n}"
                    }
                ]
                },
                {
                "id": "msg_685c3f0b9744819bac87b3873a4a3dfa0f9975dad2242f95",
                "role": "assistant",
                "content": [
                    {
                    "type": "output_text",
                    "text": "Bạn đã gửi đúng một đối tượng JSON chuẩn theo yêu cầu.\n\n**Nguyên nhân thường gặp khiến API không trả về dữ liệu:**\n\n1. **API có trả về thông báo lỗi hoặc log gì không?**\n   - Nếu API trả về status code 4xx, 5xx hoặc thông báo lỗi, bạn hãy kiểm tra nội dung log/trả về cụ thể.\n2. **API backend nhận shape dữ liệu không đúng hoặc reject các trường null.**\n   - Một số API khi field có giá trị `null` (ví dụ `\"so_tham_chieu\": null`) có thể tự động bỏ field hoặc trả lỗi nếu phía backend đang dùng schema nghiêm ngặt.\n   - Đảm bảo định dạng tên field hoàn toàn đúng, không có extra spaces, không viết hoa theo key.\n3. **Kiểm tra lại phương thức gọi API:**\n   - Đúng method (POST/PUT...)\n   - Header ứng dụng đúng kiểu nội dung (`Content-Type: application/json`).\n   - Body truyền chính xác JSON, không bị lỗi format, không có ký tự lạ, không BOM (Byte Order Mark).\n4. **Nếu backend dùng kiểm tra typescript/schema validator**  \n    - Có thể dừng lại khi gặp trường null hoặc định dạng ngày tháng không chuẩn.\n\n---\n\n**Kiểm tra đầu ra ví dụ bạn vừa cung cấp:**\n```json\n{\n  \"ten_ngan_hang\": \"HDBank\",\n  \"ten_may_pos\": \"GAS NGUYEN LONG 1\",\n  \"loai_giao_dich\": \"Thanh Toán\",\n  \"ngay_giao_dich\": \"2025-06-24\",\n  \"gio_giao_dich\": \"16:51:17\",\n  \"tong_so_tien\": \"12690000\",\n  \"so_the\": \"5128 24** **** 0666\",\n  \"tid\": \"19500292\",\n  \"mid\": \"01950072140006\",\n  \"so_lo\": \"000021\",\n  \"so_hoa_don\": \"000022\",\n  \"so_tham_chieu\": null\n}\n```\n→ JSON này **hoàn toàn hợp lệ** theo chuẩn.\n\n---\n\n## Cách xử lý/Troubleshoot đề xuất\n- Kiểm tra log từ phía API hoặc hỏi đội dev phụ trách backend để biết lý do tại sao không có response (có thể bị reject đầu vào?).\n- Thử gửi với `\"so_tham_chieu\": \"\"` thay vì `null` (nhiều hệ thống API không accept null).\n- Kiểm tra với JSON nhỏ hơn, lần lượt loại bỏ từng trường có khả năng null để xác định trường hợp nào bị lỗi.\n- Nếu bạn muốn example JSON luôn đầy đủ giá trị (kể cả các trường không rõ), sử dụng chuỗi rỗng `\"\"` thay vì `null` (hoặc hỏi dev backend field nào cần bắt buộc).\n\n---\n\nNếu muốn tôi giả lập luồng API (dành cho backend), có thể gửi request test với các giá trị khác nhau cho bạn.\n\n**Tóm lại:**  \n- JSON bạn gửi hoàn toàn chuẩn.  \n- Nếu API không trả về kết quả, hãy kiểm tra lại log backend về kiểm tra schema và thử thay giá trị `null` bằng `\"\"`.\n\nBạn cần tôi test với giá trị khác, hãy yêu cầu cụ thể nhé!"
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": "Response(id='resp_685c3e7c780c819aa910483db4dcdbe608e7e00b6a3c2629', created_at=1750875772.0, error=None, incomplete_details=None, instructions=[EasyInputMessage(content=[], role='system', type='message'), EasyInputMessage(content=[ResponseInputText(text='🎯 Bối cảnh:\\r\\n            Bạn là một trợ lý AI thông minh, chuyên phân loại và trích xuất dữ liệu từ ảnh hóa đơn tài chính tại Việt Nam.\\r', type='input_text')], role='user', type='message'), EasyInputMessage(content=[ResponseInputText(text='Tôi đã hiểu bối cảnh và vai trò của mình: Tôi là một trợ lý AI thông minh, chuyên giúp bạn phân loại và trích xuất dữ liệu (ví dụ: thông tin nhà cung cấp, mã số thuế, ngày, số hóa đơn, thành tiền, VAT,...) từ ảnh các loại hóa đơn tài chính tại Việt Nam (hóa đơn GTGT, hóa đơn bán lẻ, phiếu thu, phiếu chi...).\\nBạn có thể gửi cho tôi ảnh hóa đơn hoặc thông tin liên quan. Sau đó, tôi sẽ:\\nPhân loại hóa đơn: Xác định đó là hóa đơn GTGT, hóa đơn bán lẻ hay chứng từ khác.\\nTrích xuất dữ liệu chính theo yêu cầu, ví dụ:\\nTên đơn vị bán hàng\\nMã số thuế\\nĐịa chỉ\\nSố hóa đơn, ký hiệu hóa đơn\\nNgày hóa đơn\\nDanh sách hàng hóa/dịch vụ, số lượng, đơn giá\\nThành tiền chưa VAT, tiền thuế VAT, tổng thanh toán\\nThông tin người mua, người bán (nếu có)\\nHình thức thanh toán\\nĐịnh dạng đầu ra: Xuất dữ liệu rõ ràng, có thể ở dạng bảng, JSON hoặc theo mẫu bạn yêu c', type='input_text')], role='assistant', type='message'), EasyInputMessage(content=[ResponseInputText(text='Bạn hãy học nhận diện 4 loại bill Thanh toán của 4 loại trên Lưu ý quan trọng ảnh thứ 2 là bill dạng điện tử, là ảnh chụp màn hình, học ảnh này thật kỹ tại có thể nhầm với chụp màn hình chuyển khoản ngân hàng', type='input_text')], role='user', type='message'), EasyInputMessage(content=[ResponseInputText(text='Tôi đã tiếp nhận 4 ảnh bill thanh toán và nhận diện các đặc điểm phân biệt từng loại, đặc biệt chú ý kỹ tới ảnh thứ 2 (bill điện tử) để tránh nhầm lẫn với ảnh chuyển khoản ngân hàng thông thường. Sau đây là phân tích và rút ra tiêu chí nhận diện từng loại bill:\\n1. Bill giấy do máy POS in ra (HDBank, MB, VPBank)\\nĐặc điểm chung:\\nLà ảnh chụp giấy in POS ngoài đời thực, thường đi kèm thẻ ngân hàng.\\nCó các trường thông tin cố định:\\nTên đại lý/điểm giao dịch/cửa hàng\\nThông tin thiết bị POS, số hiệu hóa đơn, thời gian in\\nLoại thẻ (Visa/Master)\\nĐuôi số thẻ/mã bảo mật\\nTên chủ thẻ\\nSố tiền đã thanh toán\\nCác thông tin xác nhận/ghi chú tiếng Việt hoặc tiếng Anh như “tôi xác nhận hóa đơn thanh toán...”, “KHÔNG HOÀN TIỀN”\\nLogo, tên ngân hàng (HDBank, MB, VPBank) luôn nổi bật phía trên hóa đơn.\\n2. Bill điện tử - Ảnh chụp màn hình app thanh toán (ảnh số 2)\\nĐặc điểm nhận diện:\\nLà ảnh chụp màn hình từ ứng dụng điện thoại, giao diện app rõ ràng.\\nThông tin hiển thị theo cấu trúc phần mềm:\\nSố tiền với biểu tượng VNĐ, hiển thị to rõ\\nSố thẻ (ẩn phần giữa)\\nMã cấp phép, mã hóa đơn, tên khách/mã giao dịch\\nSố lô, mã giao dịch đầy đủ, ngày giờ giao dịch\\nGhi rõ loại thẻ (MASTER), TID, MID\\nCó dấu xác nhận đã thanh toán (icon check xanh)\\nCác nút chức năng phụ như “Gửi lại hóa đơn”, “Đã kết toán”\\nNổi bật: Đây không phải hóa đơn giấy, hiển thị trong app, thường sẽ có “dashboard” (giao diện phần mềm, không có nếp gấp giấy, bóng kính, không có chữ ký).\\nLưu ý: Nếu là chuyển khoản ngân hàng thì sẽ hiển thị tên ngân hàng, mã giao dịch ngân hàng, không có các trường “ứng dụng thẻ”, TID/MID, nút liên quan hóa đơn.\\n3. Bill thanh toán POS - MB Bank & VPBank (Ảnh 3 và 4)\\nĐặc điểm nhận diện:\\nGiống với ảnh 1, nhưng logo và nhận diện thương hiệu là \"MB\", \"VPBank\".\\nCó thể kèm ảnh thẻ thực tế đặt bên cạnh/pdf receipt in ra.\\nLuôn có các trường: số hóa đơn, ngày giao dịch, số thẻ, batch, tên chủ thẻ, amount, signature area.\\nDưới chân hóa đơn có dòng xác nhận (“tôi xác nhận..../I acknowledge...”).\\nĐặc biệt hóa đơn VPBank thường hiển thị thêm: MID/TID và mã xác thực, thông tin thêm (PAN, ARQC,...)\\nTóm tắt Tiêu chí nhận diện\\nLoại BillĐặc điểm nhận diện riêng biệtBill giấy in POSẢnh chụp hóa đơn giấy, logo NH nổi bật, nhiều trường thông tin chuyển khoản/thẻ, xác nhận ký tayBill điện tử chụp màn hình appẢnh chụp màn hình, nội dung dưới dạng app, có icon xác nhận, nút gửi hóa đơn, trường TID/MIDBill POS MB Bank/VPBankTương tự bill giấy, nhận diện logo MB/VPBank và cách trình bày đặc trưng, nhiều mã, xác nhận tiếng Anh\\nKinh nghiệm lưu ý đặc biệt với bill dạng điện tử (ảnh 2):\\nChỉ là ảnh chụp màn hình, dễ nhầm với sao kê chuyển khoản nhưng cấu trúc trường thông tin, layout app POS, icon xác nhận và các trường chuyên biệt như “ứng dụng thẻ”, TID, MID, Mã hóa đơn... là yếu tố khác biệt lớn.\\nChuyển khoản ngân hàng thường chỉ có mã giao dịch, tên ngân hàng, số tiền, người nhận/người gửi, không có trường hóa đơn TID/MID hay xác thực POS sale.', type='input_text')], role='assistant', type='message'), EasyInputMessage(content=[ResponseInputText(text='Đây là bill kết toán hãy học nhận diện thật kĩ để không bị nhầm với bill thanh toán', type='input_text')], role='user', type='message'), EasyInputMessage(content=[ResponseInputText(text='Tôi đã tiếp nhận các ảnh bill kết toán (settlement) và sẽ phân tích kỹ để giúp phân biệt với bill thanh toán (payment) nhằm tránh nhầm lẫn khi trích xuất dữ liệu hoặc phân loại tự động.\\nĐẶC ĐIỂM NHẬN DIỆN CHUYÊN BIỆT CỦA BILL KẾT TOÁN (SETTLEMENT)\\n1. Đặc trưng định dạng/nội dung\\nTiêu đề hoặc dòng chữ nổi bật: Thường có các từ khóa như \"TỔNG KẾT\", \"KẾT TOÁN\", \"SETTLEMENT\", \"TỔNG KẾT THÀNH CÔNG\", \"LÔ ĐÃ KẾT TOÁN\", \"Tổng giao dịch thanh toán\" hoặc \"Batch\".\\nMang tính chất thống kê, tổng hợp:\\nHiển thị nhiều giao dịch hoặc tổng số giao dịch đã kết toán trong một lần.\\nCó thể liệt kê tổng số lần thanh toán, tổng số tiền đã thanh toán trong ngày/kỳ/khoảng.\\nCó bảng/tổng cộng giao dịch theo từng loại thẻ/từng loạt POS.\\n2. Cấu trúc dữ liệu khác biệt\\nKhông có chi tiết khách hàng/thẻ cụ thể như bill thanh toán lẻ từng giao dịch (không có số thẻ, tên khách hàng, không có mục “chữ ký khách hàng”).\\nCó trường TID, MID, Số lô/Batch/Trace (Batch no/Số lô), thể hiện đây là phiếu tổng hợp cho một kỳ giao dịch của máy POS.\\nThường không có mục hàng hóa, dịch vụ cụ thể (số lượng hàng, đơn giá...), chỉ có tổng số giao dịch, tổng tiền.\\nNgày giờ kết toán và/hoặc số batch, số lô là trường dữ liệu quan trọng.\\n3. Một số nhận diện trên ảnh minh họa\\nBill kết toán HDBank/VPBank/MB:\\nRõ ràng tiêu đề “TỔNG KẾT”, “SETTLEMENT-KẾT TOÁN” hoặc “TỔNG KẾT THÀNH CÔNG”.\\nTên đại lý/cửa hàng nằm bên trên.\\nTrường số lô/số batch, tổng số giao dịch, tổng số tiền.\\nLuôn có thông tin TID/MID, máy chủ: VND.\\nCó mục \"TỔNG GIAO DỊCH THANH TOÁN: ...\", \"TỔNG SỐ TIỀN\", \"TỔNG SỐ LẦN\".\\nSo sánh với bill thanh toán\\nBill kết toánBill thanh toánTiêu đềTỔNG KẾT, KẾT TOÁN, SETTLEMENTTHANH TOÁN, PAYMENT, SALETrường đại diệnTổng số giao dịch, tổng số tiền, số lô, batchSố thẻ (cheo/cụ thể), tên KH, số tiền lẻNội dungLiệt kê tổng, bảng tổng hợp giao dịch/thẻNội dung giao dịch chi tiết theo khách/phiênChi tiết thẻKhông có hoặc rất tổng hợpCó số thẻ, tên chủ thẻ, loại thẻ, chữ kýGiao dịch mẫu2-3 dòng tổng hợp, có thể theo loại thẻ1 giao dịch chi tiết (số tiền, hàng hóa, VAT)\\nLưu ý Nhận diện so với các loại khác:\\nBill thanh toán luôn ghi rõ số thẻ, tên KH, số tiền lẻ từng giao dịch, chữ ký KH.\\nBill chuyển khoản ngân hàng (ảnh chụp màn hình app) thường không xuất hiện các cụm tổng hợp như \"batch\", \"tổng kết\", mà chỉ có \"giao dịch thành công\", số tiền, mã giao dịch, KH/người nhận.\\nQUY LUẬT/NHẬN DIỆN TỰ ĐỘNG\\nĐể không bị nhầm lẫn giữa bill kết toán và bill thanh toán, khi OCR nội dung:\\nNếu tiêu đề chứa “TỔNG KẾT”, “KẾT TOÁN”, “SETTLEMENT”, “TỔNG KẾT THÀNH CÔNG” => Xác định đó là bill kết toán\\nNếu có trường “Batch no”, “Số lô”, “Tổng giao dịch thanh toán”, “Tổng số giao dịch”, “MID”, “TID”, không có trường “Số thẻ”, “Chữ ký khách hàng” => bill kết toán\\nNếu liệt kê từng giao dịch riêng lẻ, có số thẻ, tên KH, chữ ký => bill thanh toán\\nTóm tắt nhận diện bill kết toán\\nNhận diện từ khóa: \"TỔNG KẾT\", \"KẾT TOÁN\", \"SETTLEMENT\", \"TỔNG KẾT THÀNH CÔNG\", \"Batch/Số lô\", “TID”, “MID”\\nCấu trúc: Tổng hợp, liệt kê số lượng và tổng số tiền nhiều giao dịch thanh toán/dòng; không có thông tin chi tiết thẻ/khách hàng.\\nNội dung: Tổng số lần, tổng số tiền, thời gian kết toán, không có hàng hóa cụ thể lẻ từng giao dịch.\\nKết luận: Hệ thống cần ưu tiên các quy tắc này để luôn phân biệt chuẩn xác bill kết toán và tránh nhầm với bill thanh toán hoặc các giao dịch cá nhân lẻ. Nếu có thắc mắc hoặc cần ví dụ data mẫu cho từng loại, bạn vui lòng yêu cầu thêm!', type='input_text')], role='assistant', type='message'), EasyInputMessage(content=[ResponseInputText(text='DỮ LIỆU CẦN TRÍCH XUẤT TỪ BILL THANH TOÁN\\n1. Thông tin đơn vị chấp nhận thanh toán (Cửa hàng/Đại lý)\\nTên đơn vị/cửa hàng/phòng giao dịch\\nMã số/địa chỉ cửa hàng (nếu có)\\nMID: Mã số thiết bị chấp nhận thẻ (Merchant ID)\\n2. Thông tin giao dịch\\nNgày giờ giao dịch\\nSố hóa đơn (Invoice/Receipt No hoặc Bill No)\\nBatch No (nếu có)\\nSTT giao dịch hoặc Trace No (Transaction Sequence No)\\n3. Thông tin thẻ\\nLoại thẻ (Visa, Mastercard, v.v.)\\nSố thẻ (dạng masked: **** **** **** 1234)\\nTên chủ thẻ (CARD HOLDER)\\nNgân hàng phát hành (Issuing Bank, nếu có)\\n4. Chi tiết thanh toán\\nSố tiền thanh toán (Amount): Ghi rõ số và đơn vị VNĐ\\nLoại giao dịch (Sale, Payment, …)\\n5. Thông tin xác nhận giao dịch\\nSignature/Chữ ký khách hàng (có/không)\\nGhi chú đặc biệt/Remark (NẾU có): ví dụ: “Đã thanh toán”, “Sale”, “KHÔNG HOÀN TIỀN”, “APPROVED”, “Success”, …\\nAuth Code (Mã xác thực giao dịch)\\n6. Thông tin về máy POS\\nTID: Terminal ID\\nSố hiệu máy POS\\n7. Ngôn ngữ & thông tin phụ\\nDạng hóa đơn (bản in/giao diện màn hình/app)\\nApp phiên bản (nếu là bill điện tử)', type='input_text')], role='assistant', type='message'), EasyInputMessage(content=[ResponseInputText(text='Chỉ trích xuất các trường sau đây ❗ Yêu cầu bắt buộc: 1. Chỉ trả về đối tượng JSON hợp lệ. 2. Không chứa văn bản thừa, markdown, giải thích hay ghi chú. 3. Tất cả các trường phải có giá trị. - Nếu một trường không tìm thấy trên hóa đơn hoặc không rõ ràng, gán giá trị là null. - Tất cả giá trị số tiền phải loại bỏ dấu phân cách hàng nghìn (chỉ dùng số, ví dụ: \"5020000\" thay vì \"5.020.000\"). 📤 Định dạng JSON đầu ra (bắt buộc): { \"ten_ngan_hang\": \"string\", \"ten_may_pos\": \"string\", \"loai_giao_dich\": \"string\", \"ngay_giao_dich\": \"YYYY-MM-DD\", \"gio_giao_dich\": \"HH:MM:SS\", \"tong_so_tien\": \"string\", \"so_the\": \"string\", \"tid\": \"string\", \"mid\": \"string\", \"so_lo\": \"string\", \"so_hoa_don\": \"string\", \"so_tham_chieu\": \"string\" }\\n            🔍 Hướng dẫn trích xuất từng trường:              - ten_ngan_hang:             - POS Giấy: Nhận diện từ logo/tên ngân hàng ở đầu hóa đơn.             - MPOS ảnh màn hình: Để \"MPOS\".              - ten_may_pos:             - POS Giấy: Dưới logo, hoặc dòng chứa \"TÊN ĐẠI LÝ:\", \"Cửa hàng:\".             - MPOS ảnh màn hình: Để \"MPOS\".              - loai_giao_dich:             - POS Giấy: \"THANH TOÁN\", \"SALE\",... → chuẩn hóa thành \"Thanh Toán\".             - MPOS ảnh màn hình: \"Thanh Toán\".              - ngay_giao_dich:             - POS Giấy: Dòng \"NGÀY/GIC\", \"NGÀY GIỜ\", \"Ngày:\" → chuẩn \"YYYY-MM-DD\".             - MPOS ảnh màn hình: Dòng \"Ngày giao dịch\".              - gio_giao_dich:             - POS Giấy: Cùng dòng với ngày.             - MPOS ảnh màn hình: Dòng \"Giờ giao dịch\", định dạng HH:MM:SS.              - tong_so_tien:             - POS Giấy: Từ dòng \"TỔNG TIỀN\", \"Tiền thực trả\". Bỏ \"đ\", \"VND\", dấu \".\".             - MPOS ảnh màn hình: Số in to nhất, đầu màn hình. Chuẩn hóa như trên.              - so_the:             - POS Giấy: Dòng có số thẻ dạng \"**** **** **** 1234\".             - MPOS ảnh màn hình: Dãy số che một phần, 4 số cuối.              - tid:             - POS Giấy: Dòng \"TID:\", hoặc phần sau trong dòng \"Máy/Tid:\".             - MPOS ảnh màn hình: Dòng \"Mã thiết bị\".              - mid:             - POS Giấy: Dòng \"MID:\", hoặc phần trước trong \"Máy/Tid:\".             - MPOS ảnh màn hình: Dòng \"Mã ĐVCNT\".              - so_lo:             - POS Giấy: Dòng \"SỐ LÔ:\", \"BATCH No:\".             - MPOS ảnh màn hình: Dòng \"Số lô\".              - so_hoa_don:             - POS Giấy: Dòng \"SỐ H.ĐƠN:\", \"TRACE No:\", \"Mã giao dịch:\".             - MPOS ảnh màn hình: Dòng \"Mã giao dịch\".              - so_tham_chieu:             - POS Giấy: Dòng \"SỐ TC:\", \"REF No:\", \"Số tham chiếu:\".             - MPOS ảnh màn hình: Dòng \"Mã tham chiếu\".', type='input_text')], role='user', type='message'), EasyInputMessage(content=[ResponseInputText(text='Đã hiểu hoàn toàn yêu cầu.\\nKhi bạn gửi ảnh bill tài chính, tôi sẽ:\\nChỉ trích xuất đúng các trường bạn liệt kê, trả về một đối tượng JSON hợp lệ, không kèm theo bất kỳ ghi chú hoặc văn bản nào khác.\\nNếu trường nào không thể xác định rõ, sẽ gán giá trị null.\\nMọi số tiền đều loại bỏ dấu chấm/dấu phẩy.\\nChuẩn hóa đúng định dạng ngày, giờ.\\nBạn có thể gửi ảnh hóa đơn/bill, tôi sẽ thực hiện đúng hướng dẫn này.', type='input_text')], role='assistant', type='message'), EasyInputMessage(content=[ResponseInputText(text='nếu là bill thanh toán thì mới trích xuất \\nnếu là bill thanh kết toán thì các trường trích xuất để null', type='input_text')], role='user', type='message'), EasyInputMessage(content=[ResponseInputText(text='Đã rõ. Tôi chỉ thực hiện trích xuất dữ liệu khi nhận diện đúng là bill thanh toán (không phải bill kết toán, không phải hóa đơn tổng, không phải chuyển khoản, không phải loại chứng từ khác).\\nNếu nhận diện được là bill thanh toán, tôi sẽ trả về đúng JSON như bạn định nghĩa; Nếu KHÔNG PHẢI bill thanh toán, tôi sẽ KHÔNG trả về bất kỳ kết quả JSON nào.\\nSẵn sàng nhận ảnh từ bạn.', type='input_text')], role='assistant', type='message'), EasyInputMessage(content=[], role='user', type='message')], metadata={}, model='gpt-4.1-2025-04-14', object='response', output=[ResponseOutputMessage(id='msg_685c3e7da514819a922ec6b7ec37acbb08e7e00b6a3c2629', content=[ResponseOutputText(annotations=[], text='Đây là ảnh xác nhận CHUYỂN KHOẢN NGÂN HÀNG, không phải bill thanh toán thẻ POS hoặc bill kết toán POS. Không trích xuất dữ liệu.', type='output_text', logprobs=None)], role='assistant', status='completed', type='message')], parallel_tool_calls=True, temperature=1.0, tool_choice='auto', tools=[], top_p=1.0, background=False, max_output_tokens=2048, previous_response_id=None, prompt=ResponsePrompt(id='pmpt_685c2e52caec8193a3e40f10de2c44430976694b2bec9c34', variables={}, version='2'), reasoning=Reasoning(effort=None, generate_summary=None, summary=None), service_tier='default', status='completed', text=ResponseTextConfig(format=ResponseFormatText(type='text')), truncation='disabled', usage=ResponseUsage(input_tokens=4869, input_tokens_details=InputTokensDetails(cached_tokens=4634), output_tokens=43, output_tokens_details=OutputTokensDetails(reasoning_tokens=0), total_tokens=4912), user=None, store=True)\napi trả về"
                    }
                ]
                },
                {
                "id": "msg_685c3f2e1888819bb951b25b6f844b740f9975dad2242f95",
                "role": "assistant",
                "content": [
                    {
                    "type": "output_text",
                    "text": "Cảm ơn bạn đã gửi log và chi tiết. Từ chuỗi bạn gửi, tôi thấy luồng hoạt động đúng như sau:\n\n- Nếu nhận diện được là **chuyển khoản ngân hàng** (không phải bill thanh toán POS, không phải bill kết toán), sẽ trả về:  \n  **\"Đây là ảnh xác nhận CHUYỂN KHOẢN NGÂN HÀNG, không phải bill thanh toán thẻ POS hoặc bill kết toán POS. Không trích xuất dữ liệu.\"**\n- Và **không trả về JSON**.\n\nĐiều này hoàn toàn ĐÚNG với quy tắc bạn đã đặt trước đó:\n> Nếu không phải bill thanh toán, không trích xuất, không trả về JSON.\n\n**Nghĩa là API/middleware hoặc AI đã hoạt động đúng quy tắc phân loại bạn định nghĩa.**\n\n---\n\n## Tóm tắt lại quy trình đúng:\n1. Nếu là bill thanh toán thẻ (POS) → Trích xuất JSON đúng mẫu bạn định nghĩa.\n2. Nếu là bill kết toán hoặc bất cứ loại khác (chuyển khoản, tổng kết, biên nhận không phải POS)  \n   → Không trả về JSON, hoặc trả về thông báo bạn thấy phía trên.\n\n---\n\n## Nếu Bạn Muốn ĐIỀU CHỈNH\n- Nếu đọc POST API bạn muốn DÙNG JSON rỗng với tất cả trường null như:  \n  ```json\n  {\n    \"ten_ngan_hang\": null,\n    \"ten_may_pos\": null,\n    \"loai_giao_dich\": null,\n    \"ngay_giao_dich\": null,\n    \"gio_giao_dich\": null,\n    \"tong_so_tien\": null,\n    \"so_the\": null,\n    \"tid\": null,\n    \"mid\": null,\n    \"so_lo\": null,\n    \"so_hoa_don\": null,\n    \"so_tham_chieu\": null\n  }\n  ```\n  **Kể cả nhận diện là bill kết toán, hay chuyển khoản...**  \n  → Hãy yêu cầu tôi/AI hoặc phía code backend luôn trả JSON với các trường null.\n\n- Nếu đúng ý bạn là:\n  > Loại chứng từ không thuộc \"bill thanh toán thẻ POS\" -> không trả về gì (hoặc thông báo ngắn, dạng plain text),  \n  … thì hệ thống hiện tại đã hoạt động đúng.\n\n---\n\n## Gợi ý kiểm tra (nếu bạn vẫn chưa nhận được JSON cho bảng POS)\n- Hãy thử gửi 1 bill đúng loại POS (thanh toán thẻ), kiểm tra có trả về JSON như bạn mô tả đầu.\n- Nếu vẫn không trả ra JSON, vui lòng kiểm tra lại phần nhận diện loại bill ở bước phân loại input ảnh/OCR.\n\n---\n\n**Kết luận:**  \nSystem hiện tại bạn mô tả hoạt động ĐÚNG với logic phân loại của bạn. Nếu muốn API LUÔN trả JSON đủ trường (dù null), hãy hướng dẫn rõ cho AI hoặc backend.\n\nBạn cần điều chỉnh chính sách trả về không?  \nNếu muốn, tôi có thể viết lại đáp án/logic rule cụ thể hơn theo đúng quy trình tích hợp của bạn."
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": "tôi muốn Nếu không phải bill thanh toán, không trích xuất, không trả về JSON. thì vẫn trả về json nhưng mà null hết mà"
                    }
                ]
                },
                {
                "id": "msg_685c3f79a888819b80177fa6d86741180f9975dad2242f95",
                "role": "assistant",
                "content": [
                    {
                    "type": "output_text",
                    "text": "Rất rõ!  \nBạn muốn:  \n**Nếu KHÔNG phải bill thanh toán** (ví dụ: bill kết toán, chuyển khoản, hóa đơn tổng hợp, các loại chứng từ khác)  \n→ VẪN phải trả về một object JSON đầy đủ các trường, nhưng tất cả các giá trị đều là `null`.\n\n---\n\n### Mẫu JSON đầu ra bắt buộc:\n```json\n{\n  \"ten_ngan_hang\": null,\n  \"ten_may_pos\": null,\n  \"loai_giao_dich\": null,\n  \"ngay_giao_dich\": null,\n  \"gio_giao_dich\": null,\n  \"tong_so_tien\": null,\n  \"so_the\": null,\n  \"tid\": null,\n  \"mid\": null,\n  \"so_lo\": null,\n  \"so_hoa_don\": null,\n  \"so_tham_chieu\": null\n}\n```\n\n---\n\n## Quy tắc xử lý mới:\n\n1. **Nếu ảnh là bill thanh toán POS đúng chuẩn**  \n → Trích xuất và trả về Object JSON đủ trường, đúng nội dung.\n\n2. **Nếu ảnh là bill kết toán, chuyển khoản ngân hàng, hay bất kỳ loại nào KHÔNG phải bill thanh toán POS**  \n → Trả về một Object JSON đầy đủ các trường, nhưng tất cả các giá trị đều là `null`.\n\n---\n\n## Kịch bản mẫu (minh họa):\n\n**Ví dụ 1: Bill thanh toán POS**\n```json\n{\n  \"ten_ngan_hang\": \"VPBank\",\n  \"ten_may_pos\": \"VINMART HA NOI\",\n  \"loai_giao_dich\": \"Thanh Toán\",\n  \"ngay_giao_dich\": \"2024-06-05\",\n  \"gio_giao_dich\": \"18:11:32\",\n  \"tong_so_tien\": \"987000\",\n  \"so_the\": \"4319 24** **** 6789\",\n  \"tid\": \"12345678\",\n  \"mid\": \"09876543212345\",\n  \"so_lo\": \"001024\",\n  \"so_hoa_don\": \"000998\",\n  \"so_tham_chieu\": null\n}\n```\n\n**Ví dụ 2: Bill kết toán/chuyển khoản…**\n```json\n{\n  \"ten_ngan_hang\": null,\n  \"ten_may_pos\": null,\n  \"loai_giao_dich\": null,\n  \"ngay_giao_dich\": null,\n  \"gio_giao_dich\": null,\n  \"tong_so_tien\": null,\n  \"so_the\": null,\n  \"tid\": null,\n  \"mid\": null,\n  \"so_lo\": null,\n  \"so_hoa_don\": null,\n  \"so_tham_chieu\": null\n}\n```\n\n---\n\n## Cam kết thực hiện:\n\nKể từ giờ, nếu bạn gửi ảnh hóa đơn thuộc các loại *không phải bill thanh toán* (ví dụ: bill kết toán, chuyển khoản…), tôi sẽ luôn trả về một object JSON đầy đủ trường, tất cả giá trị là `null`.\n\nNếu đồng ý định dạng này, vui lòng xác nhận lại! Bạn có thể test bằng cách gửi ảnh cụ thể cho tôi để kiểm tra kết quả."
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_image",
                    "image_url": "data:image/jpeg;base64,..."
                    }
                ]
                },
                {
                "id": "msg_685c3fd1f6f4819b9294e94a28e45d920f9975dad2242f95",
                "role": "assistant",
                "content": [
                    {
                    "type": "output_text",
                    "text": "```json\n{\n  \"ten_ngan_hang\": null,\n  \"ten_may_pos\": null,\n  \"loai_giao_dich\": null,\n  \"ngay_giao_dich\": null,\n  \"gio_giao_dich\": null,\n  \"tong_so_tien\": null,\n  \"so_the\": null,\n  \"tid\": null,\n  \"mid\": null,\n  \"so_lo\": null,\n  \"so_hoa_don\": null,\n  \"so_tham_chieu\": null\n}\n```"
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_image",
                    "image_url": "data:image/jpeg;base64,..."
                    }
                ]
                },
                {
                "id": "msg_685c407f4c60819b9e4ccb8796b82d5b0f9975dad2242f95",
                "role": "assistant",
                "content": [
                    {
                    "type": "output_text",
                    "text": "```json\n{\n  \"ten_ngan_hang\": \"VPBank\",\n  \"ten_may_pos\": \"HKD NGUYEN THI THUONG 41\",\n  \"loai_giao_dich\": \"Thanh Toán\",\n  \"ngay_giao_dich\": \"2025-06-21\",\n  \"gio_giao_dich\": \"13:43:44\",\n  \"tong_so_tien\": \"29990000\",\n  \"so_the\": \"5138 92** **** 2003\",\n  \"tid\": \"R3411406\",\n  \"mid\": \"341471002267952\",\n  \"so_lo\": \"000351\",\n  \"so_hoa_don\": \"000066\",\n  \"so_tham_chieu\": null\n}\n```"
                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": "hãy xử lí ảnh sau"
                    },
                    {
                    "type": "image_url",
                    "image_url": image_url
                    }
                ]
                },
                {
                "id": "msg_685c40a92934819ba5ce88786ae1e9a40f9975dad2242f95",
                "role": "assistant",
                "content": [
                    {
                    "type": "output_text",
                    "text": "```json\n{\n  \"ten_ngan_hang\": \"VPBank\",\n  \"ten_may_pos\": \"HKD NGUYEN THI THUONG 41\",\n  \"loai_giao_dich\": \"Thanh Toán\",\n  \"ngay_giao_dich\": \"2025-06-21\",\n  \"gio_giao_dich\": \"13:43:44\",\n  \"tong_so_tien\": \"29990000\",\n  \"so_the\": \"5138 92** **** 2003\",\n  \"tid\": \"R3411406\",\n  \"mid\": \"341471002267952\",\n  \"so_lo\": \"000351\",\n  \"so_hoa_don\": \"000066\",\n  \"so_tham_chieu\": null\n}\n```"
                    }
                ]
                }
            ],
            reasoning={},
            max_output_tokens=2048,
            store=True
            )
        

        print(response)
        return self._extract_text_response(response)

    

    @staticmethod
    def _extract_text_response(response):
        try:
            text = response.choices[0].message.content[0].text.strip()
            print(text)
            return json.loads(text)  # 🎯 Trả về dict nếu chuỗi là JSON hợp lệ
        except json.JSONDecodeError as e:
            return {"error": f"❌ JSON decode failed: {e}", "raw_text": text}
        except Exception as e:
            return {"error": f"❌ Unexpected error: {e}"}

