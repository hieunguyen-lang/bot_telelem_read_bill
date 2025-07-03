from redis_connect import RedisDuplicateChecker
redis=RedisDuplicateChecker()

redis.remove_invoice("_000111_000086_19500292_13:03:15_40816000_HDBank")
redis.remove_invoice("_000110_000080_19500293_15:23:45_49275000_HDBank")
redis.remove_invoice("_000109_000080_19500293_15:22:55_49975000_HDBank")