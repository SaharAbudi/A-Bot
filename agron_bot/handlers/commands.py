import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from agron_bot.logger import logger
from agron_bot.core.cancel_state import mark_cancel
from agron_bot.core.history import get_user_stats, get_user_history
from agron_bot.handlers.messages import (
    START_MESSAGE,
    NO_QUEUE_MESSAGE,
    QUEUE_STATUS_MESSAGE,
    CANCELLED_FROM_QUEUE_MESSAGE,
    CANCEL_MARKED_MESSAGE,
    NO_HISTORY_MESSAGE,
    HISTORY_HEADER,
    HISTORY_LINE,
    NO_STATS_MESSAGE,
    STATS_TEMPLATE,
)

AVG_PROCESSING_SECONDS = 15
ERROR_LOG_PATH = os.path.join("logs", "error.log")


def build_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Status", callback_data="status")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
        [InlineKeyboardButton("📜 History", callback_data="history")],
        [InlineKeyboardButton("📈 Stats", callback_data="stats")],
        [InlineKeyboardButton("🧾 Errors", callback_data="errors")]
    ])


def start_command():
    async def _command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_info = f"{user.full_name} (ID: {user.id})"

        message = update.message or (update.callback_query and update.callback_query.message)
        if update.callback_query:
            await update.callback_query.answer()

        await message.reply_markdown(START_MESSAGE, reply_markup=build_menu())
        logger.info(f"👋 /start used by {user_info}")

    return _command


def status_command(queue):
    async def _command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        user_info = f"{user.full_name} (ID: {user.id})"

        message = update.message or (update.callback_query and update.callback_query.message)
        if update.callback_query:
            await update.callback_query.answer()

        queue_items = list(queue._queue)
        total_in_queue = len(queue_items)
        user_position = None

        for i, (queued_update, _, _) in enumerate(queue_items):
            if queued_update.effective_user.id == user_id:
                user_position = i + 1
                break

        if user_position:
            estimated_wait = user_position * AVG_PROCESSING_SECONDS
            minutes = estimated_wait // 60
            seconds = estimated_wait % 60
            wait_str = f"{minutes} min {seconds} sec" if minutes else f"{seconds} seconds"
            msg = QUEUE_STATUS_MESSAGE.format(total=total_in_queue, position=user_position, wait=wait_str)
            await message.reply_text(msg, reply_markup=build_menu())
            logger.info(f"📊 /status: {user_info} is #{user_position} in queue ({wait_str})")
        else:
            await message.reply_text(NO_QUEUE_MESSAGE, reply_markup=build_menu())
            logger.info(f"📊 /status: {user_info} is not in the queue.")

    return _command


def cancel_command(queue):
    async def _command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        user_info = f"{user.full_name} (ID: {user.id})"

        message = update.message or (update.callback_query and update.callback_query.message)
        if update.callback_query:
            await update.callback_query.answer()

        mark_cancel(user_id)

        queue_items = list(queue._queue)
        index_to_remove = None

        for i, (queued_update, _, _) in enumerate(queue_items):
            if queued_update.effective_user.id == user_id:
                index_to_remove = i
                break

        if index_to_remove is not None:
            del queue._queue[index_to_remove]
            await message.reply_text(CANCELLED_FROM_QUEUE_MESSAGE, reply_markup=build_menu())
            logger.info(f"🗑️ /cancel: Removed request from {user_info} (was position #{index_to_remove + 1})")
        else:
            await message.reply_text(CANCEL_MARKED_MESSAGE, reply_markup=build_menu())
            logger.info(f"🛑 /cancel: {user_info} marked for cancellation (not found in queue).")

    return _command


def history_command():
    async def _command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        user_info = f"{user.full_name} (ID: {user.id})"

        message = update.message or (update.callback_query and update.callback_query.message)
        if update.callback_query:
            await update.callback_query.answer()

        try:
            history = get_user_history(user_id)
            completed = [h for h in history if h.get("status") == "completed"]
            last_5 = completed[-5:]

            if not last_5:
                await message.reply_text(NO_HISTORY_MESSAGE, reply_markup=build_menu())
                return

            lines = [HISTORY_HEADER]
            for item in last_5:
                timestamp_str = item.get("timestamp", "")
                try:
                    if "T" in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    else:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    formatted = timestamp.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    formatted = timestamp_str

                duration = item.get("duration_sec", 0.0)
                id_number = item.get("id_number", "unknown")
                lines.append(HISTORY_LINE.format(id_number=id_number, duration=duration, timestamp=formatted))

            await message.reply_markdown("\n".join(lines), reply_markup=build_menu())

        except Exception as e:
            logger.exception("❌ Failed to retrieve history:")
            await message.reply_text(f"❗ Failed to load history: {str(e)}", reply_markup=build_menu())

    return _command


def stats_command():
    async def _command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        user_info = f"{user.full_name} (ID: {user.id})"

        message = update.message or (update.callback_query and update.callback_query.message)
        if update.callback_query:
            await update.callback_query.answer()

        stats = get_user_stats(user_id)

        if not stats:
            await message.reply_text(NO_STATS_MESSAGE, reply_markup=build_menu())
            return

        msg = STATS_TEMPLATE.format(
            total=stats["total_runs"],
            avg=stats["avg_runtime"],
            cancelled=stats["total_cancelled"]
        )
        await message.reply_markdown(msg, reply_markup=build_menu())
        logger.info(f"📈 /stats used by {user_info}: {stats}")

    return _command


def errors_command():
    async def _command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_info = f"{user.full_name} (ID: {user.id})"

        message = update.message or (update.callback_query and update.callback_query.message)
        if update.callback_query:
            await update.callback_query.answer()

        if not os.path.exists(ERROR_LOG_PATH):
            await message.reply_text("📭 No error log file found.", reply_markup=build_menu())
            return

        if os.path.getsize(ERROR_LOG_PATH) == 0:
            await message.reply_text("📂 The error log file exists but is empty.", reply_markup=build_menu())
            return

        try:
            with open(ERROR_LOG_PATH, "rb") as log_file:
                await message.reply_document(document=log_file, filename="error.log", reply_markup=build_menu())
            logger.info(f"📤 Sent error log to {user_info}")
        except Exception as e:
            logger.exception("❌ Failed to send error log:")
            await message.reply_text(f"❗ Failed to send error log:\n{str(e)}", reply_markup=build_menu())

    return _command