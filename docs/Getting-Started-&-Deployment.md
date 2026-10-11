# Getting Started & Deployment

Hướng dẫn chi tiết cách triển khai **Lotus Telegram Bridge** lên server/máy cá nhân để làm cầu nối cho bot.

---

## 1. Yêu cầu hệ thống

* **Docker & Docker Compose** (khuyên dùng) HOẶC **Python 3.10+**.
* Một domain hoặc reverse proxy HTTPS (Cloudflare Tunnel, Nginx, Caddy, ngrok) để Lotus Chat server có thể gọi webhook về máy của bạn.

---

## 2. Triển khai bằng Docker Compose (Khuyên dùng)

### Bước 1: Clone repository
```bash
git clone https://github.com/ronnhd/lotus-telegram-bridge.git
cd lotus-telegram-bridge
```

### Bước 2: Cấu hình biến môi trường
Sao chép file mẫu:
```bash
cp .env.example .env
```
Chỉnh sửa file `.env`:
```ini
# Port chạy Bridge
PORT=8080
HOST=0.0.0.0

# Upstream Lotus API
LOTUS_API_BASE=https://bot.lotuschat.vn

# URL Webhook của Bot Backend (nơi nhận update)
# Nếu bot chạy cùng mạng Docker: http://bot-service:8443/webhook
# Nếu bot chạy trên máy host: http://host.docker.internal:8443/webhook
TARGET_BOT_WEBHOOK_URL=http://host.docker.internal:8443/webhook

# Secret token bảo vệ webhook (tùy chọn)
WEBHOOK_SECRET=your_secret_token_here

# Allowlist User ID cho chat riêng tư (ngăn người lạ spam DM bot)
# Để trống nếu muốn cho phép tất cả mọi người
ALLOWED_USERS=123456,789012

# Mức log: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### Bước 3: Khởi chạy container
```bash
docker-compose up -d
```
Kiểm tra trạng thái:
```bash
docker-compose logs -f
curl http://localhost:8080/health
# Trả về: {"status": "ok", "service": "lotus-telegram-bridge"}
```

---

## 3. Triển khai trực tiếp với Python

```bash
git clone https://github.com/ronnhd/lotus-telegram-bridge.git
cd lotus-telegram-bridge

# Tạo virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình môi trường
cp .env.example .env
# Chỉnh sửa file .env

# Chạy server Uvicorn
uvicorn lotus_bridge.server:app --host 0.0.0.0 --port 8080
```

---

## 4. Thiết lập Webhook trên Lotus Chat

Để Lotus server chuyển tin nhắn về Bridge:
1. Mở cổng công khai HTTPS trỏ về port `8080/webhook` của Bridge (qua Cloudflare Tunnel hoặc Nginx SSL).
   Ví dụ domain của bạn là: `https://bot.yourdomain.com`
2. Gọi API đăng ký webhook của Lotus:
```bash
curl -X POST "https://bot.lotuschat.vn/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://bot.yourdomain.com/webhook",
       "secret_token": "your_secret_token_here"
     }'
```
