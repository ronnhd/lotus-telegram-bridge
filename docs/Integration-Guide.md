# Integration Guide

Hướng dẫn cấu hình các thư viện và framework Telegram Bot phổ biến để hoạt động với **Lotus Telegram Bridge**.

Nguyên tắc chung: Bạn không cần sửa đổi bất kỳ logic code nào của bot, chỉ cần đổi **Base URL** trỏ về Bridge (`http://localhost:8080/bot` hoặc `http://localhost:8080`).

---

## 1. python-telegram-bot (v20+)

Cấu hình tham số `base_url` trong `ApplicationBuilder`:

```python
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào từ Lotus Chat qua Bridge!")

app = (
    ApplicationBuilder()
    .token("YOUR_LOTUS_BOT_TOKEN")
    .base_url("http://localhost:8080/bot")  # Trỏ về Bridge
    .build()
)

app.add_handler(CommandHandler("start", start))

# Chạy webhook nhận update từ Bridge
app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    webhook_url="http://localhost:8080/webhook",
)
```

---

## 2. Telegraf (Node.js)

Cấu hình option `telegram.apiRoot`:

```javascript
const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.LOTUS_BOT_TOKEN, {
  telegram: {
    apiRoot: 'http://localhost:8080', // Trỏ về Bridge
  },
});

bot.start((ctx) => ctx.reply('Xin chào từ Lotus Chat!'));

bot.on('text', (ctx) => {
  ctx.reply(`Bạn vừa nhắn: ${ctx.message.text}`);
});

bot.launch();
```

---

## 3. pyTelegramBotAPI (telebot)

Sử dụng `apihelper.API_URL`:

```python
import telebot
from telebot import apihelper

# Trỏ API URL về Bridge
apihelper.API_URL = "http://localhost:8080/bot{0}/{1}"

bot = telebot.TeleBot("YOUR_LOTUS_BOT_TOKEN")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Xin chào từ telebot trên Lotus Chat!")

bot.infinity_polling()
```

---

## 4. grammY (TypeScript / Node.js)

Cấu hình `client.apiRoot`:

```typescript
import { Bot } from "grammy";

const bot = new Bot("YOUR_LOTUS_BOT_TOKEN", {
  client: {
    apiRoot: "http://localhost:8080", // Trỏ về Bridge
  },
});

bot.command("start", (ctx) => ctx.reply("Xin chào từ grammY!"));
bot.start();
```

---

## 5. Dify / n8n / AI Agent Platforms

Với các nền tảng no-code hoặc AI Workflow:
1. Trong cấu hình Telegram Bot node / credential:
2. Nhập Bot Token cấp bởi Lotus Chat.
3. Trong phần **Custom API Endpoint** / **Base URL**, điền URL của Bridge:
   `http://lotus-bridge:8080/bot`
