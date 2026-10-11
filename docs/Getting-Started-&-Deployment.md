# Getting Started & Deployment

This guide walks you through deploying **Lotus Telegram Bridge** as a standalone container or local service to bridge your Telegram bot with Vietnam Lotus Chat.

---

## 1. System Requirements

* **Docker & Docker Compose** (recommended) OR **Python 3.10+**.
* An HTTPS public endpoint or reverse proxy (e.g. Cloudflare Tunnel, Nginx SSL, Caddy, ngrok) so Vietnam Lotus Chat servers can deliver inbound webhooks to your machine.

---

## 2. Docker Compose Deployment (Recommended)

### Step 1: Clone the repository
```bash
git clone https://github.com/ronnhd/lotus-telegram-bridge.git
cd lotus-telegram-bridge
```

### Step 2: Configure environment variables
Copy the template configuration:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
# Bridge listening port
PORT=8080
HOST=0.0.0.0

# Upstream Lotus API base URL
LOTUS_API_BASE=https://bot.lotuschat.vn

# Forwarding target for normalized inbound webhooks
# If your bot backend runs in the same Docker network: http://bot-service:8443/webhook
# If your bot backend runs on host machine: http://host.docker.internal:8443/webhook
TARGET_BOT_WEBHOOK_URL=http://host.docker.internal:8443/webhook

# Secret token to protect the webhook endpoint (optional)
WEBHOOK_SECRET=your_secret_token_here

# Optional: Comma-separated list of allowed user IDs for private chats (DM Allowlist)
# Prevents unauthorized users from triggering private bot interactions
# Leave empty to allow all incoming users
ALLOWED_USERS=123456,789012

# Logging level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

### Step 3: Start the service
```bash
docker-compose up -d
```
Verify status:
```bash
docker-compose logs -f
curl http://localhost:8080/health
# Returns: {"status": "ok", "service": "lotus-telegram-bridge"}
```

---

## 3. Standalone Python Deployment

```bash
git clone https://github.com/ronnhd/lotus-telegram-bridge.git
cd lotus-telegram-bridge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run Uvicorn server
uvicorn lotus_bridge.server:app --host 0.0.0.0 --port 8080
```

---

## 4. Registering Webhooks with Vietnam Lotus Chat

Vietnam Lotus Chat does **not** support Telegram's standard `/bot<token>/setWebhook` endpoint. Instead, webhooks must be registered using their custom endpoint `/set_bot_webhook`:

```bash
curl -X POST "https://bot.lotuschat.vn/set_bot_webhook" \
     -H "Authorization: Bearer <YOUR_ADMIN_JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 123456,
       "bot_id": 123456789,
       "webhook": "https://bot.yourdomain.com/webhook",
       "secret": "your_secret_token_here"
     }'
```

*Note: Once registered, Lotus server will deliver incoming updates to your HTTPS URL. Inbound requests will deliver the secret in the `Secret:` header, which Lotus Telegram Bridge validates and normalizes.*
