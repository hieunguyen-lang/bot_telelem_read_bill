# redis_duplicate_checker.py

import redis
import os
import dotenv
from dotenv import load_dotenv
load_dotenv() 
class RedisDuplicateChecker:
    def __init__(self, host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0, key_prefix='processed_invoices',momo_key_prefix='momo_invoices',doiung_key_prefix='doi_ung_invoices'
):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.key = key_prefix
        self.momo_key = momo_key_prefix
        self.doiung_key = doiung_key_prefix
    def is_duplicate(self, invoice_id):
        """
        Kiểm tra xem hóa đơn đã xử lý chưa.
        """
        return self.client.sismember(self.key, invoice_id)

    def mark_processed(self, invoice_id):
        """
        Đánh dấu hóa đơn đã xử lý.
        """
        self.client.sadd(self.key, invoice_id)

    def remove_invoice(self, invoice_id):
        """
        Xóa một invoice_id khỏi danh sách đã xử lý.
        """
        self.client.srem(self.key, invoice_id)

    # ==================== KEY PHỤ ====================
    def is_duplicate_momo(self, invoice_id):
        """Kiểm tra trùng trên key phụ."""
        return self.client.sismember(self.momo_key, invoice_id)

    def mark_processed_momo(self, invoice_id):
        """Đánh dấu đã xử lý trên key phụ."""
        self.client.sadd(self.momo_key, invoice_id)

    def remove_invoice_momo(self, invoice_id):
        """Xóa khỏi key phụ."""
        self.client.srem(self.momo_key, invoice_id)

    # ==================== KEY PHỤ ====================
    def is_duplicate_doiung(self, invoice_id):
        """Kiểm tra trùng trên key phụ."""
        return self.client.sismember(self.doiung_key, invoice_id)

    def mark_processed_doiung(self, invoice_id):
        """Đánh dấu đã xử lý trên key phụ."""
        self.client.sadd(self.doiung_key, invoice_id)

    def remove_invoice_doiung(self, invoice_id):
        """Xóa khỏi key phụ."""
        self.client.srem(self.doiung_key, invoice_id)