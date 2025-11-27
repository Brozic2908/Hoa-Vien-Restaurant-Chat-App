# Dùng python 3.8 bản nhẹ (slim)
FROM python:3.8-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (để cài torch/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài thư viện Python
# (Làm bước này trước để tận dụng Cache của Docker, build nhanh hơn)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Thiết lập biến môi trường để Model lưu vào thư mục /app/models
ENV HF_HOME=/app/models

# Lệnh chạy mặc định
CMD ["python", "src/main.py"]