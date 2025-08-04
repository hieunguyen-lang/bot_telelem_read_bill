from telegram.ext import MessageHandler, Filters
from core.momo_core import handle_photo_momo
from core.core import handle_photo
from core.doi_ung import handle_photo_doiung
from core.doi_ung_the import handle_photo_doi_ung_the
import os
from dotenv import load_dotenv
load_dotenv()  # Tự động tìm và load từ .env

# ID của các group
GROUP_DAO_ID = os.getenv("GROUP_DAO_ID")  # ID của group DAO
GROUP_RUT_ID = os.getenv("GROUP_RUT_ID")  # ID của group Rút tiền
GROUP_MOMO_ID = os.getenv("GROUP_MOMO_ID") 
GROUP_DOI_UNG = os.getenv("GROUP_DOI_UNG") 
GROUP_DOI_UNG_THE_ID = os.getenv("GROUP_DOI_UNG_THE_ID") 
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

    elif str(chat_id)  in [ str(GROUP_DOI_UNG)]:
        handle_photo_doiung(update, context)
    elif str(chat_id)  in [ str(GROUP_DOI_UNG_THE_ID)]:
        handle_photo_doi_ung_the(update, context)
    else:
        chat_id = update.effective_chat.id
        
        print(f"Ảnh gửi từ group  (ID: {chat_id})")
        update.message.reply_text("❌ Group này không được phép xử lý")