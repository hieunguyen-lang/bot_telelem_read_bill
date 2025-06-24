#!/bin/bash

# ==============================
# Thông tin MySQL
DB_CONTAINER="mysql_bill"
MYSQL_PASSWORD="root"  # ⚠️ Đổi nếu cần
BACKUP_DIR="./backups"
BACKUP_NAME="mysql_backup_$(date +%F_%H-%M-%S).sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# ==============================
# Thông tin Redis
REDIS_CONTAINER="redis_bill"
REDIS_BACKUP_NAME="redis_backup_$(date +%F_%H-%M-%S).rdb"
REDIS_BACKUP_PATH="${BACKUP_DIR}/${REDIS_BACKUP_NAME}"
REDIS_DUMP_PATH="/data/dump.rdb"  # Default dump path trong redis:alpine

# ==============================
# Tạo thư mục backup nếu chưa có
mkdir -p "${BACKUP_DIR}"

# ==============================
# Backup MySQL
echo "📦 Dumping MySQL database..."
docker exec ${DB_CONTAINER} /usr/bin/mysqldump -u root --password=${MYSQL_PASSWORD} bill_data > "${BACKUP_PATH}"
echo "✅ MySQL DB đã được backup tại: ${BACKUP_PATH}"

# ==============================
# Backup Redis
echo "📦 Saving Redis dump file..."
docker exec ${REDIS_CONTAINER} redis-cli SAVE

echo "📥 Copying Redis dump file..."
docker cp ${REDIS_CONTAINER}:${REDIS_DUMP_PATH} "${REDIS_BACKUP_PATH}"
echo "✅ Redis DB đã được backup tại: ${REDIS_BACKUP_PATH}"

# ==============================
# Xóa backup cũ hơn 7 ngày (nếu muốn)
find "${BACKUP_DIR}" -type f -mtime +7 -delete
