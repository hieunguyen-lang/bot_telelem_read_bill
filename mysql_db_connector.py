import aiomysql
import asyncio

class AsyncMySQLConnector:
    def __init__(self, host="localhost", user="root", password="", database="test_db", port=3306):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "db": database,
            "port": port,
            "autocommit": True
        }
        self.pool = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await aiomysql.create_pool(**self.config)
                print("✅ Kết nối MySQL (async) thành công.")
            except Exception as e:
                print("❌ Lỗi kết nối MySQL:", e)

    async def execute(self, query, params=None):
        await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, params)
                    await conn.commit()
                    return cur.rowcount
                except Exception as e:
                    print("❌ Lỗi khi thực thi:", e)
                    return None

    async def fetchone(self, query, params=None):
        await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.execute(query, params)
                    return await cur.fetchone()
                except Exception as e:
                    print("❌ Lỗi fetchone:", e)
                    return None

    async def fetchall(self, query, params=None):
        await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.execute(query, params)
                    return await cur.fetchall()
                except Exception as e:
                    print("❌ Lỗi fetchall:", e)
                    return []

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            print("✅ Đã đóng kết nối MySQL.")
