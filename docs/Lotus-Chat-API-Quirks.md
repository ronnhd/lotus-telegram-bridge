# Lotus Chat API Quirks & Gotchas

Tài liệu này tổng hợp toàn bộ các điểm sai lệch, dị tật ngầm và hành vi phi chuẩn của server Lotus Chat Bot (`bot.lotuschat.vn`) so với Telegram Bot API chính thức, được đúc kết từ quá trình reverse-engineer và kiểm chứng thực tế qua hơn 113 payload.

---

## 1. Private Chat ID Deviation

### Vấn đề
Khi người dùng nhắn tin trực tiếp (1-on-1 DM) cho bot, payload webhook của Lotus trả về trường `message.chat.id` là một chuỗi số ID hội thoại nội bộ gồm 16 chữ số (ví dụ: `3363019539071413`).
Nếu bot framework lấy ID này để gọi `sendMessage`, server Lotus vẫn trả về HTTP 200 OK nhưng ứng dụng Lotus Chat phía người dùng **hoàn toàn không hiển thị tin nhắn**.

### Cách Bridge xử lý
Trong hàm `normalize_inbound_update`:
```python
if chat.get("type") == "private" and sender_id is not None:
    chat["id"] = sender_id
```
Bridge tự động ghi đè `chat.id` bằng `from.id` (User ID thực của người gửi) trước khi chuyển tiếp webhook cho bot backend.

---

## 2. Thiếu trường `is_bot` trong User Object

### Vấn đề
Telegram Bot API quy định object `User` bắt buộc phải có trường `is_bot: bool`. Lotus server hoàn toàn bỏ qua trường này và gửi kèm `profile_photos: null`.
Các thư viện bot có cơ chế validate schema chặt chẽ (như `python-telegram-bot` v20+) sẽ crash ngay lập tức:
```text
TypeError: User.__init__() missing 1 required positional argument: 'is_bot'
```

### Cách Bridge xử lý
Bridge kiểm tra và tự động inject `is_bot: False` vào mọi object `from`:
```python
if "is_bot" not in sender:
    sender["is_bot"] = False
```

---

## 3. `reply_to_message` là số nguyên trần (Bare Integer)

### Vấn đề
Khi người dùng reply một tin nhắn, Telegram gửi object `reply_to_message` là một object `Message` đầy đủ. Lotus server lại gửi `reply_to_message: <message_id_int>`. Điều này làm parser của các SDK bot bị crash `AttributeError: 'int' object has no attribute '...'`.

### Cách Bridge xử lý
Bridge tự động bọc số nguyên này thành một object `Message` hợp lệ:
```python
if isinstance(reply_to, int):
    msg["reply_to_message"] = {
        "message_id": reply_to,
        "date": msg.get("date", 0),
        "chat": chat or {},
    }
```

---

## 4. Bắt buộc tên field upload Media là `file`

### Vấn đề
Telegram Bot API sử dụng các multipart key riêng biệt tùy theo loại media:
* `sendPhoto` -> key `photo`
* `sendDocument` -> key `document`
* `sendVoice` -> key `voice`
* `sendVideo` -> key `video`

Lotus server từ chối tất cả các tên trên và báo lỗi: `photo id not found`. Lotus **chỉ chấp nhận duy nhất một tên field là `file`** cho mọi loại file và cả khi gửi lại `file_id`.

### Cách Bridge xử lý
Ở chiều Outbound, Bridge chặn request multipart/form-data và tự động rename các key media sang `file`.

---

## 5. Không hỗ trợ `MarkdownV2`, chỉ render HTML

### Vấn đề
* Gửi `parse_mode=MarkdownV2`: Lotus hiển thị nguyên xi các dấu escape `\` ra màn hình chat (ví dụ `1\.` hiển thị là `1\.`).
* Lotus server chỉ hỗ trợ một tập con HTML: `<b>`, `<i>`, `<code>`, `<pre>`, và `<a href="...">`.
* Các thẻ `<s>` (gạch ngang) hay `<blockquote>` (quote) bị client Lotus bỏ qua hoặc hạ cấp về plain text.

### Cách Bridge xử lý
Bridge tích hợp sẵn bộ chuyển đổi `markdown_to_lotus_html`:
1. Gỡ bỏ các ký tự escape MarkdownV2.
2. Bảo vệ các khối code (``` và `) bằng placeholder.
3. Escape ký tự HTML an toàn.
4. Chuyển đổi cú pháp markdown (`**bold**`, `*italic*`, `[link](url)`) sang thẻ HTML tương ứng.
5. Ép `parse_mode = "HTML"`.

---

## 6. Lỗi 500 Server-side tại `sendMediaGroup`

### Vấn đề
Endpoint `sendMediaGroup` của Lotus bị lỗi backend server-side. Dù gửi theo định dạng nào (JSON string, multipart array, attach://...) server đều trả về HTTP 500 hoặc `media_group is missing`.

### Cách Bridge xử lý
Bridge khuyến nghị không dùng `sendMediaGroup` mà gửi tách lẻ từng file qua `sendPhoto` / `sendDocument`.

---

## 7. Endpoint `getFile` luôn trả về `File ID invalid`

### Vấn đề
Lotus Chat không hỗ trợ luồng `getFile` chuẩn của Telegram. Mọi request `getFile?file_id=...` đều nhận về lỗi `File ID invalid`.

### Cách Bridge xử lý
File media trong Lotus được phân phối qua CDN có chữ ký tạm thời (`link_cdn`), đính kèm trực tiếp trong payload update khi user gửi file.
Bridge lưu một bộ nhớ đệm `MediaRegistry` (mapping `file_id -> link_cdn`). Khi bot gọi `getFile`, Bridge tự động trả về response Telegram giả lập với đường dẫn `file_path` trỏ tới CDN URL đã lưu:
```json
{
  "ok": true,
  "result": {
    "file_id": "123456",
    "file_path": "https://chat-cdn.lotus.vn/lotuschat-prod/..."
  }
}
```

---

## 8. Tin nhắn nhóm bị tàng hình nếu thiếu `reply_to_message_id`

### Vấn đề
Khi bot gửi tin nhắn vào Group Chat (`chat_id < 0`), nếu request không có trường `reply_to_message_id`, server vẫn nhận nhưng ứng dụng Lotus client của các thành viên trong nhóm sẽ **không hiển thị tin nhắn**.

### Cách Bridge xử lý
Luôn đảm bảo outbound request vào group có chứa `reply_to_message_id` trích dẫn tin nhắn của người hỏi hoặc tin nhắn neo của nhóm.
