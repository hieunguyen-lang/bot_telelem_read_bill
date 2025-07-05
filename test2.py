from PIL import Image
import os

def make_grid(image_paths, output_path, rows, cols):
    images = [Image.open(p).convert("RGB") for p in image_paths]
    w, h = images[0].size  # lấy kích thước gốc
    grid = Image.new('RGB', (cols*w, rows*h), (255,255,255))

    for i, img in enumerate(images):
        grid.paste(img, (w*(i%cols), h*(i//cols)))

    grid.save(output_path, quality=95)

# ===============================
# Đường dẫn ảnh gốc
ket_toan_images = [
    "dataset\\ketoan_hd.jpg",
    "dataset\\ketoan_mb.jpg",
    "dataset\\kettoan_vp.jpg",
]

thanh_toan_images = [
    "dataset\\thanhtoan_hdbank.jpg",
    "dataset\\thanhtoan_Mbbank.jpg",
    "dataset\\thanhtoan_vp.jpg",
    "dataset\\MPOS.jpg",
]

# Gộp và lưu
make_grid(ket_toan_images, "bills_ket_toan.jpg", rows=2, cols=2)
make_grid(thanh_toan_images, "bills_thanh_toan.jpg", rows=2, cols=2)
