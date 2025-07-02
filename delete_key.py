from redis_connect import RedisDuplicateChecker
redis=RedisDuplicateChecker()

redis.remove_invoice("_000322_000053_i1656669_10:42:00_10110000_VISA")