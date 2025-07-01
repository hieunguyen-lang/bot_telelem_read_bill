
from io import BytesIO
from PIL import Image
import base64
def process_telegram_photo_to_base64(message_photo, max_width=800, quality=70) -> str:
    file = message_photo.get_file()
    bio = BytesIO()
    file.download(out=bio)
    bio.seek(0)

    image = Image.open(bio)

    if image.mode != "L":
        image = image.convert("L")

    if image.width > max_width:
        ratio = max_width / float(image.width)
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

    #image.save("resized_image.jpg", format="JPEG", quality=quality)

    resized_bio = BytesIO()
    image.save(resized_bio, format="JPEG", quality=quality)
    resized_bio.seek(0)

    return base64.b64encode(resized_bio.getvalue()).decode("utf-8")