# Lotus Telegram Bridge Wiki

Chào mừng bạn đến với tài liệu kỹ thuật chính thức của **Lotus Telegram Bridge** — bộ Gateway và Reverse Proxy chuyển đổi giao thức 2 chiều giữa **Vietnam Lotus Chat Bot API** (`bot.lotuschat.vn`) và **Telegram Bot API**.

---

### 📚 Danh mục tài liệu

* **[[Home]]**: Trang chủ và tổng quan kiến trúc.
* **[[Lotus Chat API Quirks & Gotchas|Lotus-Chat-API-Quirks]]**: Chi tiết 7 dị tật server-side của Lotus Chat so với chuẩn Telegram Bot API.
* **[[Getting Started & Deployment|Getting-Started-&-Deployment]]**: Hướng dẫn triển khai Standalone Proxy qua Docker Compose và Python virtual environment.
* **[[Integration Guide|Integration-Guide]]**: Hướng dẫn cấu hình `base_url` cho python-telegram-bot, Telegraf, telebot, grammY, n8n, Dify và AI Agent.
* **[[Troubleshooting & FAQ|Troubleshooting-&-FAQ]]**: Tổng hợp lỗi thường gặp (400, 401, 500, tin nhắn tàng hình, CDN link hết hạn).

---

### 🚀 Tổng quan kiến trúc 2 chiều

```
                  ┌──────────────────────────────────────────────┐
                  │          Lotus Telegram Bridge               │
[Lotus Server] ──►│ Inbound: Port 8080/webhook (Normalize JSON)  │──► [Backend Bot App]
                  │                                              │    (PTB / Telegraf / AI)
[Lotus Server] ◄──│ Outbound: Port 8080/bot* (Rewrite API calls) │◄──
                  └──────────────────────────────────────────────┘
```

1. **Inbound Webhook Proxy**: Nhận webhook từ Lotus Chat (`/webhook`), chuẩn hóa cấu trúc JSON cho đúng chuẩn Telegram rồi chuyển tiếp tới bot backend.
2. **Outbound API Interceptor**: Đóng vai trò Telegram Bot API Server giả lập (`/bot<token>/<method>`). Bot backend chỉ cần trỏ `base_url` về bridge; bridge sẽ tự động format Markdown thành HTML, đổi tên field upload media thành `file`, và bypass lỗi 500 của server Lotus.
