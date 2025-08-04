import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 🛠 נתיב תיקיית הקובץ (agron_bot)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(BASE_DIR)
sys.path.append(SCRIPT_DIR)

# טעינת משתני סביבה
env_path = os.path.join(SCRIPT_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print(f"⚠️ .env file not found at {env_path}")

print("TELEGRAM_TOKEN:", os.getenv("TELEGRAM_TOKEN"))
print("DEVELOPER_ID:", os.getenv("DEVELOPER_ID"))

# ייבוא הלוגר
from agron_bot.logger import logger, enable_telegram_logging

# 🔒 קובץ נעילה
LOCK_FILE = os.path.join(BASE_DIR, "bot.lock")
if os.path.exists(LOCK_FILE):
    logger.error("⛔ Bot is already running. Access denied.")
    print("⛔ Bot is already running. Access denied.")
    sys.exit(1)
with open(LOCK_FILE, "w") as f:
    f.write("locked")

# מחיקת קובץ נעילה ביציאה
import atexit
def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
atexit.register(remove_lock_file)

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

# ✅ ייבוא פנימי
from agron_bot.handlers.handlers import handle_message
from agron_bot.worker import worker
from agron_bot.handlers.commands import (
    start_command,
    status_command,
    cancel_command,
    history_command,
    stats_command,
    errors_command,
)
from agron_bot.handlers.callbacks import handle_callback
from agron_bot.core.state import queue

DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "5962330651"))

async def set_bot_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "📖 How to use the bot"),
        BotCommand("status", "📊 Your queue status"),
        BotCommand("cancel", "❌ Cancel active request"),
        BotCommand("history", "📜 Last 5 completed searches"),
        BotCommand("stats", "📈 Your personal usage stats"),
        BotCommand("errors", "🧾 Latest error log (for developers only)"),
    ])

async def startup(app):
    # חיבור הלוגר לטלגרם
    if os.getenv("TELEGRAM_TOKEN") and os.getenv("DEVELOPER_ID"):
        loop = asyncio.get_running_loop()
        enable_telegram_logging(app.bot, loop, int(os.getenv("DEVELOPER_ID")))
        logger.info("📡 Telegram log handler enabled.")
    else:
        logger.warning("⚠️ Telegram log handler not active – missing TELEGRAM_TOKEN or DEVELOPER_ID in .env")

    app.create_task(worker(queue))
    await set_bot_commands(app)
    logger.info(f"🚀 Bot started at {datetime.now().isoformat()}")
    if os.getenv("DEBUG") == "1":
        logger.info("🧪 DEBUG mode is active")

async def notify_developer(bot, error):
    try:
        await bot.send_message(DEVELOPER_ID, f"❗️Critical error occurred:\n{str(error)}")
    except Exception as e:
        logger.error(f"❌ Failed to notify developer: {str(e)}")

def main():
    try:
        app = (
            ApplicationBuilder()
            .token(os.getenv("TELEGRAM_TOKEN"))
            .post_init(startup)
            .build()
        )

        # פקודות
        app.add_handler(CommandHandler("start", start_command()))
        app.add_handler(CommandHandler("status", status_command(queue)))
        app.add_handler(CommandHandler("cancel", cancel_command(queue)))
        app.add_handler(CommandHandler("history", history_command()))
        app.add_handler(CommandHandler("stats", stats_command()))
        app.add_handler(CommandHandler("errors", errors_command()))

        # כפתורי אינליין
        app.add_handler(CallbackQueryHandler(handle_callback))

        # הודעות רגילות
        async def guarded_handle_message(update, context):
            if queue.qsize() > 10:
                msg = "🛑 High load at the moment. Try again in a few minutes."
                await update.message.reply_text(msg)
                logger.warning(f"User {update.effective_user.id} got load warning.")
                return
            await handle_message(queue)(update, context)

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guarded_handle_message))

        logger.info("🤖 Agron Bot is running...")
        print("🤖 Agron Bot is running...")

        app.run_polling()

    except Exception as e:
        logger.exception("❌ Unexpected error occurred in main()")
        try:
            asyncio.run(notify_developer(app.bot, e))
        except:
            pass
        raise e

if __name__ == "__main__":
    main()
