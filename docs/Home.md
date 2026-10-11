# Lotus Telegram Bridge Wiki

Welcome to the technical documentation for **Lotus Telegram Bridge** — a lightweight, bidirectional reverse proxy and protocol gateway translating between [Vietnam Lotus Chat Bot API](https://lotuschat.vn/) (`bot.lotuschat.vn`) and standard [Telegram Bot API](https://core.telegram.org/bots/api) specifications.

---

### 📚 Documentation Index

* **[[Home]]**: Overview, architecture, and core capabilities.
* **[[API Quirks & Architecture Gotchas|Lotus-Chat-API-Quirks]]**: In-depth analysis of 10 server-side protocol bugs, schema incompatibilities, and documentation errors in Lotus Chat Bot.
* **[[Getting Started & Deployment|Getting-Started-&-Deployment]]**: Production deployment guides via Docker Compose and standalone Python services.
* **[[Integration Guide|Integration-Guide]]**: Plug-and-play guides for python-telegram-bot, Telegraf (Node.js), telebot, grammY, n8n, Dify, and AI agent frameworks.
* **[[Troubleshooting & FAQ|Troubleshooting-&-FAQ]]**: Diagnosing silent drops, error 400/500/502, expired CDN links, and invisible group messages.

---

### 🚀 Bidirectional Gateway Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          Lotus Telegram Bridge               │
[Lotus Server] ──►│ Inbound: Port 8080/webhook (Normalize JSON)  │──► [Backend Bot App]
                  │                                              │    (PTB / Telegraf / AI)
[Lotus Server] ◄──│ Outbound: Port 8080/bot* (Rewrite API calls) │◄──
                  └──────────────────────────────────────────────┘
```

#### 1. Inbound Webhook Proxy
Lotus Chat webhooks violate several strict Telegram schema requirements:
* Rewrites 16-digit private conversation IDs to recipient `user.id`.
* Injects missing `is_bot: false` flags into `User` objects.
* Wraps bare-integer `reply_to_message` IDs into valid Telegram `Message` objects.
* Extracts and registers signed temporary CDN URLs (`link_cdn`) for downstream file fetching.
* Normalizes non-standard `Secret:` headers to `X-Telegram-Bot-Api-Secret-Token`.

#### 2. Outbound API Interceptor
Standard Telegram SDKs point their `base_url` to `http://localhost:8080`:
* Intercepts media uploads (`sendPhoto`, `sendDocument`, `sendVoice`, etc.) and forces the form field key to `file`.
* Rewrites `sendMediaGroup` parameter `media` to Lotus's non-standard `media_group`.
* Emulates Telegram's broken `getFile` endpoint by serving cached CDN links.
* Translates Markdown/MarkdownV2 into safe HTML tags (`<b>`, `<i>`, `<code>`, `<pre>`, `<a>`), automatically forcing `parse_mode="HTML"`.
