# Troubleshooting & FAQ

Tổng hợp các vấn đề và lỗi phổ biến nhất khi tích hợp bot trên Vietnam Lotus Chat.

---

### 1. Bot gửi tin nhắn vào nhóm nhưng không ai nhìn thấy?
* **Nguyên nhân**: Lotus Chat yêu cầu tin nhắn bot trong nhóm bắt buộc phải có `reply_to_message_id`. Nếu gửi tin nhắn trần (không reply), server Lotus vẫn trả về 200 nhưng client của người dùng sẽ bỏ qua và không render.
* **Cách khắc phục**: Luôn truyền `reply_to_message_id` vào request `sendMessage`.

---

### 2. Người dùng chat riêng (DM) với bot nhưng bot trả lời không thấy?
* **Nguyên nhân**: Lotus Chat gửi `chat.id` private là ID hội thoại nội bộ (16 số), nếu bot gửi lại ID này thì client không nhận.
* **Cách khắc phục**: Đảm bảo inbound webhook đi qua Bridge. Bridge đã tự động ghi đè `chat.id = from.id` cho mọi tin nhắn private.

---

### 3. Lỗi `TypeError: User.__init__() missing is_bot` khi chạy PTB?
* **Nguyên nhân**: Object `from` của Lotus thiếu trường `is_bot: bool`.
* **Cách khắc phục**: Cho webhook đi qua Bridge để tự động chèn `is_bot: false`.

---

### 4. Lỗi `photo id not found` khi gửi ảnh hoặc file?
* **Nguyên nhân**: SDK Telegram gửi multipart với key là `photo`, `document`, hoặc `voice`. Lotus chỉ nhận duy nhất key mang tên `file`.
* **Cách khắc phục**: Cấu hình bot trỏ `base_url` về Bridge. Bridge sẽ tự động đổi tên key sang `file` trước khi forward lên Lotus.

---

### 5. Ký tự MarkdownV2 hiển thị dấu gạch chéo ngược (`\`) lộn xộn?
* **Nguyên nhân**: Lotus Chat không hỗ trợ cú pháp `MarkdownV2`, chỉ hỗ trợ các thẻ HTML cơ bản (`<b>`, `<i>`, `<code>`, `<pre>`).
* **Cách khắc phục**: Bridge đã có bộ converter tự động biên dịch Markdown sang thẻ HTML và gán `parse_mode=HTML`.

---

### 6. Không tải được file người dùng gửi qua `getFile`?
* **Nguyên nhân**: Endpoint `getFile` của Lotus luôn trả về lỗi `File ID invalid`.
* **Cách khắc phục**: Bridge tự động lấy link CDN có chữ ký (`link_cdn`) từ payload update người dùng gửi và giả lập response của `getFile`.
