# Base image với Python
FROM python:3.10-slim

# Đặt thư mục làm việc
WORKDIR /app

# Copy toàn bộ mã nguồn vào container
COPY . /app

# Cài đặt thư viện
RUN pip install --upgrade pip && pip install -r requirements.txt

# Lệnh mặc định khi container start
CMD ["python", "core.py"]
