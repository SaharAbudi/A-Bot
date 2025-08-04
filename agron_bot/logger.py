import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# === טעינת משתני סביבה ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# === תיקיית לוגים ===
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

daily_log_file = os.path.join(LOG_DIR, f"agron-{datetime.now().strftime('%Y-%m-%d')}.log")
error_log_file = os.path.join(LOG_DIR, "error.log")

# === מונה לוגים עבור חיפושים בלבד ===
search_log_counter = 0

def reset_search_log_counter():
    """איפוס מונה הלוגים של החיפוש (לקרוא בתחילת כל חיפוש חדש)"""
    global search_log_counter
    search_log_counter = 0

def log_search_step(message: str):
    """כתיבת לוג עם מונה ספציפי לחיפוש"""
    global search_log_counter
    search_log_counter += 1
    logger.info(f"[LOG {search_log_counter}] {message}")

# === פורמט לוגים רגיל (ללא מונה) ===
default_format = logging.Formatter("[%(levelname)s] %(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# === Handlers רגילים ===
file_handler = logging.FileHandler(daily_log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(default_format)

error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(default_format)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(default_format)

# === Handler לטלגרם ===
class TelegramLogHandler(logging.Handler):
    def __init__(self, bot, loop, chat_id):
        super().__init__()
        self.bot = bot
        self.loop = loop
        self.chat_id = chat_id

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.loop.create_task(self.bot.send_message(chat_id=self.chat_id, text=log_entry))
        except Exception as e:
            print(f"[Logger-Telegram] Failed to send log: {e}")

# === הפעלת שליחת לוגים לטלגרם ===
def enable_telegram_logging(bot, loop, chat_id: int):
    telegram_handler = TelegramLogHandler(bot, loop, chat_id)
    telegram_handler.setLevel(logging.INFO)
    telegram_handler.setFormatter(default_format)
    logger.addHandler(telegram_handler)
    logger.info("📡 Telegram log handler is active.")

# === logger ראשי ===
logger = logging.getLogger("AgronBot")
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)
