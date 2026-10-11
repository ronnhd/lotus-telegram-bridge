# Lotus Telegram Bridge (Unofficial)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

A lightweight, bidirectional protocol bridge and API gateway that translates between [Vietnam Lotus Chat Bot API](https://lotuschat.vn/) (`bot.lotuschat.vn`) and standard Telegram Bot API specifications.

It allows developers to run bots built on any Telegram bot framework (**python-telegram-bot**, **Telegraf**, **telebot**, **grammY**, or AI agent platforms like **Hermes**, **Dify**, **n8n**) on Vietnam Lotus Chat without rewriting business logic.

---

## Disclaimer
> **Notice**: This is an independent, community-driven open-source project and is **not** officially affiliated with, endorsed by, or maintained by VCCorp or Vietnam Lotus Chat. Use at your own discretion.

---

## Why This Bridge Exists: The Lotus API Quirks

Vietnam Lotus Chat exposes endpoints modeled after the Telegram Bot API (`sendMessage`, `sendPhoto`, `getUpdates`, webhooks, etc.). However, behind the scenes, Lotus Chat server implements several undocumented, non-standard behaviors that crash standard Telegram SDKs:

| Feature / Behavior | Standard Telegram Bot API | Vietnam Lotus Chat Deviation | How This Bridge Solves It |
|---|---|---|---|
| **Private Chat ID** | `chat.id` equals `from.id` in direct chats. | Sets `chat.id` to an internal 16-digit conversation ID. Replying to that ID returns 200 but messages never render on the user client. | Rewrites inbound private `chat.id` to `from.id` automatically. |
| **User Object** | Required `is_bot: boolean` flag in `from`. | `is_bot` is completely omitted, causing strict schemas (e.g. PTB) to crash (`TypeError`). | Injects `is_bot: false` into all user objects. |
| **Quoted Messages** | `reply_to_message` is a full `Message` object. | Sends `reply_to_message` as a bare integer `message_id`. | Wraps the bare integer into a standard `Message` stub. |
| **Media Uploads** | Named multipart keys: `photo`, `document`, `voice`, etc. | Server strictly requires multipart field name `file` for all media. Named fields return `photo id not found`. | Rewrites outbound multipart and form keys to `file`. |
| **Text Formatting** | Supports `MarkdownV2`, `Markdown`, `HTML`. | Displays `MarkdownV2` backslash escapes literally (`1\.` -> `1\.`). Only renders standard HTML tags (`<b>`, `<i>`, `<code>`, `<pre>`, `<a>`). | Automatically converts Markdown/MarkdownV2 into valid Lotus HTML entities and sets `parse_mode="HTML"`. |
| **`getFile` Endpoint** | Downloads media via `getFile` path. | Server returns `File ID invalid` for all file IDs. | Caches signed CDN URLs (`link_cdn`) from inbound payloads and emulates `getFile` responses. |
| **Group Chat Replies** | Bots can send unthreaded messages into groups. | Messages in groups are invisible unless they contain a `reply_to_message_id`. | Preserves and normalizes reply threading. |

---

## Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          Lotus Telegram Bridge               │
[Lotus Server] ──►│ Inbound: Port 8080/webhook (Normalize JSON)  │──► [Your Bot Backend]
                  │                                              │    (PTB / Telegraf / AI Agent)
[Lotus Server] ◄──│ Outbound: Port 8080/bot* (Rewrite API calls) │◄──
                  └──────────────────────────────────────────────┘
```

1. **Inbound Webhook Proxy**: Normalizes incoming updates from Lotus Chat before passing them to your bot backend.
2. **Outbound API Interceptor**: Emulates the standard Telegram Bot API server. Your bot simply configures its `base_url` to point to the bridge.

---

## Quickstart

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/ronnhd/lotus-telegram-bridge.git
   cd lotus-telegram-bridge
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```ini
   PORT=8080
   LOTUS_API_BASE=https://bot.lotuschat.vn
   TARGET_BOT_WEBHOOK_URL=http://host.docker.internal:8443/webhook
   WEBHOOK_SECRET=your_secret_token
   ALLOWED_USERS=
   ```

3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

---

### Option 2: Run with Python

```bash
git clone https://github.com/ronnhd/lotus-telegram-bridge.git
cd lotus-telegram-bridge

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
uvicorn lotus_bridge.server:app --host 0.0.0.0 --port 8080
```

---

## Connecting Your Bot Framework

### 1. python-telegram-bot (v20+)
Set the `base_url` parameter on `ApplicationBuilder`:

```python
from telegram.ext import ApplicationBuilder

app = (
    ApplicationBuilder()
    .token("YOUR_LOTUS_BOT_TOKEN")
    .base_url("http://localhost:8080/bot")
    .build()
)

app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    webhook_url="http://localhost:8080/webhook",
)
```

### 2. Telegraf (Node.js)
```javascript
const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.LOTUS_BOT_TOKEN, {
  telegram: {
    apiRoot: 'http://localhost:8080',
  },
});

bot.start((ctx) => ctx.reply('Hello from Lotus Chat!'));
bot.launch();
```

---

## Running Tests

Run the test suite to verify payload normalization and HTML markdown conversion:

```bash
python3 -m unittest discover -s tests
```

---

## License

This project is open-source under the [MIT License](LICENSE).
