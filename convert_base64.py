import base64
import mimetypes

def convert_image_to_base64_file(image_path, output_path=None):
    """
    Chuyển ảnh sang định dạng data:image/...;base64,... và ghi ra file.

    :param image_path: Đường dẫn ảnh (PNG, JPG, JPEG, ...)
    :param output_path: Đường dẫn file output (.txt hoặc .base64). Nếu không có thì tự tạo.
    :return: Chuỗi base64 (dạng data URL)
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        raise ValueError("Không xác định được định dạng MIME của ảnh.")

    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode("utf-8")
        base64_data_url = f"data:{mime_type};base64,{encoded}"

    # Nếu chưa có output_path thì tạo cùng tên ảnh + .txt
    if output_path is None:
        output_path = image_path.rsplit('.', 1)[0] + ".base64.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(base64_data_url)

    print(f"✅ Đã ghi base64 vào file: {output_path}")
    return base64_data_url

# In ra hoặc dùng để gửi trong API OpenAI
convert_image_to_base64_file('bill_ketoan.jpeg')
