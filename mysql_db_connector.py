import mysql.connector
from mysql.connector import Error

class MySQLConnector:
    def __init__(self, host="localhost", user="root", password="", database="test_db", port=3306):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port
        }
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ Kết nối MySQL thành công.")
        except Error as e:
            print("❌ Lỗi kết nối MySQL:", e)
            self.connection = None
            self.cursor = None

    def ensure_connection(self):
        if self.connection is None or not self.connection.is_connected():
            print("🔁 Reconnecting to MySQL...")
            self.connect()

    def execute(self, query, params=None):
        self.ensure_connection()
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Error as e:
            print("❌ Lỗi khi thực thi:", e)
            return None

    def fetchone(self, query, params=None):
        self.ensure_connection()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Error as e:
            print("❌ Lỗi fetchone:", e)
            return None

    def fetchall(self, query, params=None):
        self.ensure_connection()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Error as e:
            print("❌ Lỗi fetchall:", e)
            return []

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("✅ Đã đóng kết nối MySQL.")
        self.cursor = None
        self.connection = None
