from data_connect.redis_connect import RedisDuplicateChecker
redis=RedisDuplicateChecker()

redis.remove_invoice("_20250705162075053188_000023_i1656671_16:20:25_44460000_MPOS")
redis.remove_invoice("_000110_000080_19500293_15:23:45_49275000_HDBank")
redis.remove_invoice("_000109_000080_19500293_15:22:55_49975000_HDBank")