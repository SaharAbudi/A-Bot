from telegram import Update
from telegram.ext import ContextTypes
from agron_bot.logger import logger
from agron_bot.handlers.commands import (
    status_command,
    cancel_command,
    history_command,
    stats_command,
    errors_command,
)
from agron_bot.core.state import queue


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user
    user_info = f"{user.full_name} (ID: {user.id})"

    try:
        if data == "status":
            logger.info(f"🖱️ Button clicked: status by {user_info}")
            await status_command(queue)(update, context)  # ✅ תיקון כאן

        elif data == "cancel":
            logger.info(f"🖱️ Button clicked: cancel by {user_info}")
            await cancel_command(queue)(update, context)  # ✅ תיקון כאן

        elif data == "history":
            logger.info(f"🖱️ Button clicked: history by {user_info}")
            await history_command()(update, context)

        elif data == "stats":
            logger.info(f"🖱️ Button clicked: stats by {user_info}")
            await stats_command()(update, context)

        elif data == "errors":
            logger.info(f"🖱️ Button clicked: errors by {user_info}")
            await errors_command()(update, context)

        else:
            await query.edit_message_text("❓ Unknown action.")
            logger.warning(f"❗ Unknown callback data '{data}' by {user_info}")

    except Exception as e:
        logger.exception("❌ Exception during callback execution:")
        await query.edit_message_text(f"❗ An error occurred:\n{str(e)}")
