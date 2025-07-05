from redis_connect import RedisDuplicateChecker
redis=RedisDuplicateChecker()

redis.remove_invoice("__000865_19500293_14:50:57_37201000_HDBank")
redis.remove_invoice("_000110_000080_19500293_15:23:45_49275000_HDBank")
redis.remove_invoice("_000109_000080_19500293_15:22:55_49975000_HDBank")