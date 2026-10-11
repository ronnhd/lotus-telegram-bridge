# Vietnam Lotus Chat Bot API: Comprehensive Quirks & Architecture Gotchas

This document details the undocumented deviations, non-standard schemas, and server-side quirks in the **Vietnam Lotus Chat Bot API** (`bot.lotuschat.vn`) compared to the official **Telegram Bot API**.

These findings are verified through real-world reverse engineering, testing over 113 production payloads, and cross-referencing with the official Lotus Chat Bot developer documentation.

---

## 1. Intentional Schema Flaw: `reply_to_message` as an Integer

### Standard Telegram Specification
In standard Telegram Bot API, `reply_to_message` is an optional `Message` object representing the message being replied to:
```json
{
  "message_id": 42,
  "reply_to_message": {
    "message_id": 10,
    "from": { "id": 12345, "is_bot": false, "first_name": "Alice" },
    "chat": { "id": -100123456, "type": "supergroup" },
    "text": "Original message"
  }
}
```

### Lotus Chat Behavior
Lotus Chat deliberately defines `reply_to_message` in its core schema as an integer:
> `reply_to_message | integer | ID of the message this is replying to`

```json
{
  "message_id": 42,
  "reply_to_message": 10
}
```

### Impact & Solution
Strict Telegram SDKs (such as `python-telegram-bot` v20+ or `grammY`) expect an object and crash during deserialization with `AttributeError: 'int' object has no attribute 'copy'` or `ValidationError`.
* **Bridge Solution**: Detects if `reply_to_message` is an integer, wrapping it into a valid `Message` stub:
  ```python
  if isinstance(reply_to, int):
      msg["reply_to_message"] = {
          "message_id": reply_to,
          "date": msg.get("date", 0),
          "chat": chat or {},
      }
  ```

---

## 2. Universal Media Upload Enforcement: The `file` Key

### Standard Telegram Specification
Telegram Bot API specifies distinct multipart field names matching each media type:
* `sendPhoto` -> multipart form key `photo`
* `sendAudio` -> multipart form key `audio`
* `sendVoice` -> multipart form key `voice`
* `sendDocument` -> multipart form key `document`
* `sendVideo` -> multipart form key `video`
* `sendAnimation` -> multipart form key `animation`

### Lotus Chat Behavior
Lotus Chat rejects all standard multipart field names with an error:
```json
{"ok": false, "description": "photo id not found"}
```
Across every media method (`sendPhoto`, `sendAudio`, `sendVoice`, `sendDocument`, `sendAnimation`, `sendVideo`), Lotus strictly enforces the parameter name **`file`** for binary uploads, remote URLs, and file ID resending.

*Note: In the official Lotus documentation, copy-paste artifacts repeatedly paste `// -- Gửi lại ảnh` (Resend photo) into documentation curl examples for audio, voice, documents, and animations.*

### Impact & Solution
* **Bridge Solution**: Intercepts all outbound multipart and urlencoded requests, automatically renaming `photo`, `audio`, `voice`, `document`, `video`, and `animation` form fields to `file`.

---

## 3. Parameter Renaming in `sendMediaGroup`

### Standard Telegram Specification
Telegram Bot API accepts media albums via `sendMediaGroup` with the parameter `media`:
```bash
curl -F 'chat_id=123' -F 'media=[{"type":"photo","media":"attach://f1"}]' -F 'f1=@img.jpg' ...
```

### Lotus Chat Behavior
Lotus Chat renamed the required parameter from `media` to **`media_group`**:
> `media_group | array of Media | yes | một mảng JSON chứa các đối tượng Media`

When standard libraries submit `media`, the server responds with HTTP 500 or `media_group is missing`. Furthermore, multipart attachments require strict 1:1 filename matching with `attach://` URIs.

### Impact & Solution
* **Bridge Solution**: Rewrites outbound `media` parameters to `media_group` in JSON and form data.

---

## 4. Broken `getFile` & Proprietary `link_cdn` / `getChatMessages`

### Standard Telegram Specification
Bots retrieve files by calling `getFile(file_id=...)`, which returns a `file_path` on Telegram's file CDN (`https://api.telegram.org/file/bot<token>/<file_path>`).

### Lotus Chat Behavior
1. **`getFile` is broken**: Any call to `getFile` on Lotus Chat consistently returns:
   ```json
   {"ok": false, "error_code": 400, "description": "File ID invalid"}
   ```
2. **Custom `link_cdn` in Payloads**: Inbound photo/video/document objects include a custom signed CDN URL field named `link_cdn`:
   ```json
   {
     "file_id": "8107734069970034730",
     "width": 1280,
     "height": 720,
     "link_cdn": "https://chat-cdn.lotus.vn/lotuschat-prod/...jpg?e=1791800000&s=..."
   }
   ```
   *Note: In official docs, Lotus describes this field verbatim as: `URL to CDN-hosted photo (custom field in your system)`.*
3. **CDN URL Expiration**: The signed `link_cdn` expires after ~72 hours (`?e=<epoch>`).
4. **Proprietary `getChatMessages` Method**: Lotus implements a non-Telegram method `getChatMessages` (`message_ids=[...]`, `chat_id=...`) to retrieve message history and acquire freshly re-signed CDN links.

### Impact & Solution
* **Bridge Solution**: 
  - Maintains an in-memory `MediaRegistry` mapping `file_id -> link_cdn` captured during inbound webhook deliveries.
  - Intercepts outbound `getFile` calls and emulates standard Telegram responses:
    ```json
    {
      "ok": true,
      "result": {
        "file_id": "8107734069970034730",
        "file_unique_id": "8107734069970034730",
        "file_path": "https://chat-cdn.lotus.vn/lotuschat-prod/...jpg?e=..."
      }
    }
    ```

---

## 5. Inbound User Schema Omission: Missing `is_bot`

### Standard Telegram Specification
Every `User` object sent by Telegram contains a mandatory boolean:
```json
{
  "id": 123456,
  "is_bot": false,
  "first_name": "Ron"
}
```

### Lotus Chat Behavior
Lotus Chat completely omits `is_bot` from user objects while appending unexpected fields like `profile_photos: null`:
```json
{
  "id": 123456,
  "first_name": "Ron",
  "username": "ronnhd",
  "profile_photos": null
}
```

### Impact & Solution
Strict Pydantic or dataclass models in modern SDKs raise `TypeError: User.__init__() missing 1 required positional argument: 'is_bot'`.
* **Bridge Solution**: Injects `is_bot: false` into all inbound `from`, `forward_from`, and `new_chat_members` user objects.

---

## 6. Private Chat ID vs Internal Conversation ID (`peer_id`)

### Standard Telegram Specification
In Telegram, a user's `chat.id` in a private direct message is identical to their `user.id`.

### Lotus Chat Behavior
Lotus distinguishes between the user ID and an internal 16-digit conversation ID:
* Webhook updates deliver `chat.id` as the conversation ID (e.g., `3363019539071413`).
* Calling `sendMessage(chat_id=3363019539071413)` succeeds with HTTP 200, but **the message never appears in the user's chat window**.
* Official docs reveal an optional internal parameter: `peer_id | integer | Used internally for authorization in private mode (optional)`.

### Impact & Solution
* **Bridge Solution**: For any update where `chat.type == "private"`, the bridge rewrites `chat.id = from.id`. Calling `sendMessage` with the recipient's user ID renders correctly in the Lotus desktop and mobile apps.

---

## 7. Silent Group Message Drops without `reply_to_message_id`

### Standard Telegram Specification
Bots can send freestanding messages into groups without quoting any existing message.

### Lotus Chat Behavior
If a bot calls `sendMessage` to a group (`chat_id < 0`) without specifying `reply_to_message_id`:
* The Lotus API returns HTTP 200 OK.
* **The message is completely invisible in the group chat client.**
* All group messages must carry a valid `reply_to_message_id` to trigger client-side rendering.

### Impact & Solution
* **Bridge Solution**: Group bot implementations must thread their messages or maintain a known anchor message ID for the group.

---

## 8. Non-standard Administrative Webhook Endpoints

### Standard Telegram Specification
Telegram sets webhooks via:
```bash
POST https://api.telegram.org/bot<token>/setWebhook?url=...&secret_token=...
```

### Lotus Chat Behavior
Lotus provides custom REST routes separate from the bot token namespace:
* `POST /set_bot_webhook`: Requires JWT Bearer token and JSON payload:
  ```json
  {
    "user_id": 123456,
    "bot_id": 123456789,
    "webhook": "https://your-domain.com/webhook",
    "secret": "your_secret_token"
  }
  ```
* `POST /get_bot_webhook_info`
* `POST /delete_bot_webhook`

Furthermore, incoming webhook requests deliver the secret token via an HTTP header named `Secret:` rather than `X-Telegram-Bot-Api-Secret-Token`.

### Impact & Solution
* **Bridge Solution**: Accepts incoming webhooks carrying either `Secret:` or `X-Telegram-Bot-Api-Secret-Token`, validates the secret, and forwards the update with the standard Telegram header.

---

## 9. Text Formatting: No `MarkdownV2`, Strict HTML Subset

### Standard Telegram Specification
Telegram supports `MarkdownV2`, `Markdown`, and `HTML`.

### Lotus Chat Behavior
1. **MarkdownV2 backslashes rendered literally**: Escapes like `1\.` or `\$` render as literal backslashes on screen.
2. **Supported HTML tags**: Only `<b>`, `<i>`, `<code>`, `<pre>`, and `<a href="...">` are reliably parsed.
3. **Ignored/Degraded tags**: `<s>` (strikethrough) maps to an unknown entity, and `<blockquote>` is ignored, degrading to plain text.

### Impact & Solution
* **Bridge Solution**: Built-in AST-like regex tokenizer converts Markdown to safe HTML tags and automatically forces `parse_mode = "HTML"`.

---

## 10. Documentation Anomalies

The official Lotus Chat Bot documentation contains several notable errors:
* **Invalid JSON syntax in examples**:
  ```json
  // From official sendMessage documentation:
  {
    'chat_id=-123456789',
    'text=Hello world'
  }
  ```
* **Plain HTTP curl snippets**: All provided examples target `http://bot.lotuschat.vn` without TLS encryption.
* **Leaked internal developer annotations**: Fields like `link_cdn` annotate `(custom field in your system)`.
* **E-Commerce schema residues**: Message objects contain non-Telegram fields like `product`, `product_order`, and `data_button: []byte`.
