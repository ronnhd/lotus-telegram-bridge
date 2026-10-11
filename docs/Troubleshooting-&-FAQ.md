# Troubleshooting & FAQ

Frequently encountered errors, unexpected behaviors, and edge cases when building or bridging bots on Vietnam Lotus Chat.

---

### 1. Bot sends messages to a group chat, but nobody sees them (Invisible Group Messages)
* **Root Cause**: Vietnam Lotus Chat requires all bot messages in group chats (`chat_id < 0`) to have a valid `reply_to_message_id`. If a bot sends a freestanding message into a group without quoting an existing message, the Lotus server responds with `{"ok": true}`, but **the Lotus desktop and mobile clients silently drop the message without rendering**.
* **Fix**: Ensure your bot always includes `reply_to_message_id` when sending messages into group chats.

---

### 2. Users direct message (DM) the bot, but the bot's replies never appear
* **Root Cause**: In 1-on-1 direct messages, Lotus Chat delivers incoming webhooks with `chat.id` set to an internal 16-digit conversation ID (e.g., `3363019539071413`). Replying to that ID returns HTTP 200, but the recipient client never receives the message.
* **Fix**: Lotus Telegram Bridge automatically intercepts inbound private webhooks and rewrites `chat.id = from.id` (the actual user ID), ensuring replies land in the user's active DM window.

---

### 3. Strict Telegram SDKs crash with `TypeError: User.__init__() missing is_bot`
* **Root Cause**: The official Telegram specification marks `is_bot: boolean` as mandatory on all `User` objects. Vietnam Lotus Chat omits this field entirely from its incoming webhook payloads (while including unexpected fields like `profile_photos: null`).
* **Fix**: Lotus Telegram Bridge injects `is_bot: false` into all user objects before forwarding the webhook payload to your bot backend.

---

### 4. Bot crashes with `AttributeError: 'int' object has no attribute '...'` on replies
* **Root Cause**: In Telegram, `reply_to_message` is a full `Message` object. Lotus Chat intentionally designed `reply_to_message` as a bare integer message ID (`reply_to_message: <int>`). Deserializers expecting an object crash immediately.
* **Fix**: Lotus Telegram Bridge detects integer `reply_to_message` values and wraps them into a valid `Message` stub (`{"message_id": <int>, "date": ..., "chat": ...}`).

---

### 5. Media uploads fail with `{"ok": false, "description": "photo id not found"}`
* **Root Cause**: Standard Telegram Bot API expects distinct multipart field names: `photo` for `sendPhoto`, `document` for `sendDocument`, `voice` for `sendVoice`, etc. Lotus Chat rejects these names and strictly requires the parameter name **`file`** across all media endpoints.
* **Fix**: Lotus Telegram Bridge intercepts outbound requests and automatically renames `photo`, `document`, `voice`, `audio`, `video`, and `animation` form fields to `file`.

---

### 6. MarkdownV2 displays messy literal backslashes (`\.`, `\!`)
* **Root Cause**: Lotus Chat does not implement Telegram's `MarkdownV2` grammar parser. Any escaped character (e.g., `1\.`, `\$`) renders literally on screen. Lotus Chat only natively renders a subset of standard HTML tags (`<b>`, `<i>`, `<code>`, `<pre>`, `<a href="...">`).
* **Fix**: Lotus Telegram Bridge converts Markdown formatting into compliant HTML tags and forces `parse_mode = "HTML"`.

---

### 7. Calls to `getFile` return `{"error_code": 400, "description": "File ID invalid"}`
* **Root Cause**: Lotus Chat does not support standard `getFile` file resolution. Media files are hosted on a temporary signed CDN (`link_cdn` parameter embedded in incoming message payloads), valid for ~72 hours.
* **Fix**: Lotus Telegram Bridge captures signed CDN links from inbound webhooks in an in-memory `MediaRegistry` and emulates standard `getFile` responses with the active CDN path.

---

### 8. `sendMediaGroup` returns HTTP 500 or `media_group is missing`
* **Root Cause**: Telegram Bot API uses `media` as the parameter name for album lists. Lotus Chat renamed this parameter to `media_group`. Furthermore, multipart album uploads suffer from server-side instability.
* **Fix**: Lotus Telegram Bridge rewrites `media` to `media_group` or unpacks media groups into serialized individual message sends.

---

### 9. Webhook registration fails when calling `/bot<token>/setWebhook`
* **Root Cause**: Lotus Chat does not expose webhook registration under the standard `/bot<token>/setWebhook` route. Webhook management is handled via custom administrative REST endpoints requiring JWT authorization (`POST /set_bot_webhook`).
* **Fix**: Use the `/set_bot_webhook` API detailed in the [Getting Started & Deployment Guide](Getting-Started-&-Deployment).
