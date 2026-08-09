import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@nighmal"
SUCCESS_CHANCE = 40


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id,
        )
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def make_try(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = "Удачно!" if random.randint(1, 100) <= SUCCESS_CHANCE else "Неудачно..."
    if update.callback_query:
        await update.callback_query.message.edit_text(result)
    else:
        await update.message.reply_text(result)


async def try_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    if not await is_subscribed(user.id, context):
        keyboard = [
            [InlineKeyboardButton(
                "Подписаться на канал",
                url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
            )],
            [InlineKeyboardButton(
                "Проверить подписку",
                callback_data="check_subscription"
            )],
        ]
        await update.message.reply_text(
            "Чтобы использовать /try, сначала подпишись на канал.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    await make_try(update, context)


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_subscribed(query.from_user.id, context):
        await query.answer("Ты ещё не подписан на канал.", show_alert=True)
        return

    await query.message.edit_text("Подписка подтверждена.\n\nЗапускаем попытку...")
    await make_try(query, context)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не установлен.")

    threading.Thread(target=start_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("try", try_command))
    app.add_handler(
        CallbackQueryHandler(
            check_subscription,
            pattern="^check_subscription$"
        )
    )

    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
