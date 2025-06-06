# Sử dụng một base image Python tương thích
FROM python:3.9-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Cài đặt các phụ thuộc hệ thống cần thiết (ví dụ: ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    # Thêm các gói hệ thống khác nếu Wav2Lip yêu cầu
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt các phụ thuộc cho server FastAPI
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ ứng dụng Wav2Lip vào trong image
COPY Wav2Lip/ ./Wav2Lip/

# Cài đặt các phụ thuộc riêng của Wav2Lip
# (Điều chỉnh nếu cần, ví dụ thêm --pre cho numba)
RUN pip install --no-cache-dir -r requirements.txt

# Copy file server main.py
COPY main.py .

# ---- THÊM DÒNG LỆNH TẠO THƯ MỤC results ----
# Script inference.py sẽ lưu kết quả vào đây
RUN mkdir -p /app/result

# Mở cổng 8000 để truy cập từ bên ngoài
EXPOSE 8000

# Lệnh để chạy ứng dụng khi container khởi động
# Khuyến nghị dùng 1 worker do tác vụ nặng, tránh tranh chấp tài nguyên
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]