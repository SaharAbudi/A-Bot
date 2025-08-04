import os
import asyncio
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

from agron_bot.core.executor import run_agron_and_capture_with_cancel_support
from agron_bot.logger import logger
from agron_bot.core.cancel_state import should_cancel, clear_cancel
from agron_bot.core.history import log_run
from agron_bot.core.session import set_last_id  # ✅ חדש

# Track if cancellation message was sent
in_progress_message_sent = {}

async def send_result_to_user(update, context, result: dict):
    user = update.effective_user
    chat_id = user.id

    try:
        # Send screenshot
        img_path = result.get("path")
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as img_file:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=img_file,
                    caption="🖼️ תוצאה בצילום מסך",
                )
            logger.info(f"📸 Screenshot sent to {user.full_name} (ID: {chat_id})")

        # Send PDF
        pdf_path = result.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            raise FileNotFoundError("❌ PDF result file not found.")

        with open(pdf_path, "rb") as pdf_file:
            await context.bot.send_document(
                chat_id=chat_id,
                document=InputFile(pdf_file),
                filename=os.path.basename(pdf_path),
                caption=f"📄 חיפוש הושלם ב־{result['duration']} שניות",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 חפש שוב", callback_data="repeat")],
                    [
                        InlineKeyboardButton("📜 היסטוריה", callback_data="history"),
                        InlineKeyboardButton("📈 סטטיסטיקות", callback_data="stats")
                    ]
                ])
            )
        logger.info(f"📤 Sent result PDF to {user.full_name} (ID: {chat_id})")

        # ✅ Delete files after sending
        try:
            if img_path and os.path.exists(img_path):
                os.remove(img_path)
                logger.info(f"🗑️ Deleted screenshot: {img_path}")
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
                logger.info(f"🗑️ Deleted PDF: {pdf_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete files after sending: {e}")

    except Exception as e:
        logger.exception("❌ Failed to send result to user")
        await context.bot.send_message(chat_id=chat_id, text=f"❗ שגיאה בשליחת תוצאה: {str(e)}")


async def worker(queue: asyncio.Queue):
    while True:
        update, context, id_number = await queue.get()
        user = update.effective_user
        user_id = user.id
        user_name = user.full_name
        user_info = f"{user_name} (ID: {user_id})"

        try:
            if should_cancel(user_id):
                logger.info(f"⛔ Skipping ID '{id_number}' from {user_info} – cancel requested before start.")
                await update.message.reply_text("❌ Your request was canceled before processing began.")
                log_run(user_id, id_number, None, status="cancelled")
                continue

            logger.info(f"🔄 Started processing ID '{id_number}' from {user_info}")
            await update.message.reply_text(f"🔍 Now processing your request for ID {id_number}...")

            loop = asyncio.get_running_loop()
            result, was_cancelled = await loop.run_in_executor(
                None, run_agron_and_capture_with_cancel_support, id_number, user_id, user_name
            )

            if was_cancelled:
                await update.message.reply_text("🛑 Cancellation in progress... Closing Agron.")
                logger.info(f"❌ Canceled during execution: ID '{id_number}' for {user_info}")

                # Delete files if canceled
                if result:
                    for path in [result.get("path"), result.get("pdf_path")]:
                        if path and os.path.exists(path):
                            os.remove(path)

                log_run(user_id, id_number, None, status="cancelled")

            elif result:
                await update.message.reply_text("📤 Uploading your result...")
                await send_result_to_user(update, context, result)

                minutes = int(result["duration"] // 60)
                seconds = int(result["duration"] % 60)
                duration_text = f"{minutes}m {seconds}s" if minutes else f"{seconds:.1f} seconds"

                logger.info(f"✅ Completed ID '{id_number}' for {user_info} in {result['duration']:.2f} sec")
                log_run(user_id, id_number, result["duration"], status="completed")

                # Save last ID for repeat search
                set_last_id(user_id, id_number)

        except Exception as e:
            logger.exception(f"❌ Error while processing ID '{id_number}' for {user_info}: {e}")
            await update.message.reply_text(f"❗ An error occurred:\n{str(e)}")
            log_run(user_id, id_number, None, status="error")

        finally:
            clear_cancel(user_id)
            in_progress_message_sent.pop(user_id, None)
            queue.task_done()
