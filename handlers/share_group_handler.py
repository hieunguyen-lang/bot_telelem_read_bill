from telegram.ext import MessageHandler, Filters
from core.momo_core import handle_photo_momo
from core.core import handle_photo
import os
from dotenv import load_dotenv
load_dotenv()  # Tự động tìm và load từ .env

# ID của các group
GROUP_DAO_ID = os.getenv("GROUP_DAO_ID")  # ID của group DAO
GROUP_RUT_ID = os.getenv("GROUP_RUT_ID")  # ID của group Rút tiền
GROUP_MOMO_ID = os.getenv("GROUP_MOMO_ID") 
def share_handler(dp):
    """
    Đăng ký 1 handler duy nhất cho ảnh, tự chia group trong callback.
    """
    dp.add_handler(
        MessageHandler(
            Filters.photo,
            lambda update, context: handle_by_group(update, context)
        )
    )

def handle_by_group(update, context):
    chat_id = update.effective_chat.id

    if str(chat_id)  in [str(GROUP_DAO_ID), str(GROUP_RUT_ID)]:
        handle_photo(update, context)
    elif str(chat_id)  in [ str(GROUP_MOMO_ID)]:
        handle_photo_momo(update, context)
    else:
        chat_id = update.effective_chat.id
        
        print(f"Ảnh gửi từ group  (ID: {chat_id})")
        update.message.reply_text("❌ Group này không được phép xử lý:", chat_id)