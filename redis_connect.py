# redis_duplicate_checker.py

import redis
import os
import dotenv
from dotenv import load_dotenv
load_dotenv() 
class RedisDuplicateChecker:
    def __init__(self, host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0, key_prefix='processed_invoices'):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.key = key_prefix

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
