from telegram import Update
from telegram.ext import ContextTypes
from agron_bot.utils import is_valid_id
from agron_bot.logger import logger

AVG_PROCESSING_SECONDS = 15  # ⏳ Estimated time per ID in seconds

def handle_message(queue):
    async def _handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        id_number = update.message.text.strip()
        user = update.effective_user
        user_info = f"{user.full_name} (ID: {user.id})"

        if not is_valid_id(id_number):
            await update.message.reply_text("❌ Please send a valid 8 or 9-digit ID number.")
            logger.warning(f"❌ Invalid ID received from {user_info}: '{id_number}'")
            return

        queue_position = queue.qsize() + 1
        await queue.put((update, context, id_number))

        estimated_wait = queue_position * AVG_PROCESSING_SECONDS
        minutes = estimated_wait // 60
        seconds = estimated_wait % 60
        wait_str = f"{minutes} min {seconds} sec" if minutes else f"{seconds} seconds"

        await update.message.reply_text(
            f"📥 Your request has been added to the queue.\n"
            f"You are currently **#{queue_position}** in line.\n"
            f"⏳ Estimated wait time: ~{wait_str}."
        )

        logger.info(
            f"📥 ID '{id_number}' added to queue by {user_info} "
            f"(position #{queue_position}, est. wait {wait_str})"
        )

    return _handler
