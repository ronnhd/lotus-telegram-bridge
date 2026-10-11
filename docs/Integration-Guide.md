# Integration Guide

A complete guide for configuring popular Telegram Bot libraries and AI Agent platforms to work seamlessly with **Lotus Telegram Bridge**.

**Key Principle**: You do **not** need to modify any of your bot's core business logic or message handlers. You only need to redirect the **API Base URL** to the Lotus Telegram Bridge (`http://localhost:8080/bot` or `http://localhost:8080`).

---

## 1. python-telegram-bot (v20+)

Configure the `base_url` parameter using `ApplicationBuilder`:

```python
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lotus Telegram Bridge automatically converts Markdown to safe Lotus HTML
    await update.message.reply_text("Hello from Lotus Chat via Lotus Telegram Bridge!")

app = (
    ApplicationBuilder()
    .token("YOUR_LOTUS_BOT_TOKEN")
    .base_url("http://localhost:8080/bot")  # Point to the Bridge
    .build()
)

app.add_handler(CommandHandler("start", start))

# Run webhook receiving normalized updates from the Bridge
app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    webhook_url="http://localhost:8080/webhook",
)
```

---

## 2. Telegraf (Node.js)

Configure the `telegram.apiRoot` option:

```javascript
const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.LOTUS_BOT_TOKEN, {
  telegram: {
    apiRoot: 'http://localhost:8080', // Point to the Bridge
  },
});

bot.start((ctx) => ctx.reply('Hello from Vietnam Lotus Chat!'));

bot.on('text', (ctx) => {
  ctx.reply(`Echo: ${ctx.message.text}`);
});

bot.launch();
```

---

## 3. pyTelegramBotAPI (telebot)

Override `apihelper.API_URL`:

```python
import telebot
from telebot import apihelper

# Point base API URL to the Bridge
apihelper.API_URL = "http://localhost:8080/bot{0}/{1}"

bot = telebot.TeleBot("YOUR_LOTUS_BOT_TOKEN")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hello from telebot running on Lotus Chat!")

bot.infinity_polling()
```

---

## 4. grammY (TypeScript / Node.js)

Configure `client.apiRoot`:

```typescript
import { Bot } from "grammy";

const bot = new Bot("YOUR_LOTUS_BOT_TOKEN", {
  client: {
    apiRoot: "http://localhost:8080", // Point to the Bridge
  },
});

bot.command("start", (ctx) => ctx.reply("Hello from grammY on Lotus Chat!"));
bot.start();
```

---

## 5. Dify / n8n / AI Agent Platforms

For no-code agent platforms, workflow automation engines, and custom agents:
1. In your **Telegram Bot** node or credential settings:
2. Enter the Bot Token assigned by Vietnam Lotus Chat.
3. In the **Custom API Endpoint** or **Base URL** field, specify the Bridge endpoint:
   `http://lotus-bridge:8080/bot`
