#!/bin/bash

# Định danh container và thông tin
DB_CONTAINER="mysql_bill"
BACKUP_DIR="./backups"
BACKUP_NAME="backup_$(date +%F).sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Tạo thư mục backup nếu chưa có
mkdir -p "${BACKUP_DIR}"

# Dump DB từ container MySQL
docker exec ${DB_CONTAINER} /usr/bin/mysqldump -u root --password=${MYSQL_ROOT_PASSWORD} bill_data > "${BACKUP_PATH}"

# Ghi log ra console
echo "✅ DB đã được backup tại: ${BACKUP_PATH}"
