import os
import time
import subprocess
import pyautogui
from dotenv import load_dotenv
from agron_bot.logger import logger, log_search_step, reset_search_log_counter
import pygetwindow as gw
from agron_bot.core.cancel_state import should_cancel
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import json

# Load license from environment
load_dotenv()
AGRON_LICENSE = os.getenv("AGRON_LICENSE", "7958423837")

# Delay between actions (seconds)
ACTION_DELAY = 1


def wait_for_window(title_substring: str, timeout: int = 20) -> gw.Win32Window | None:
    """Wait for a window containing specific title text."""
    for _ in range(timeout * 2):
        windows = gw.getWindowsWithTitle(title_substring)
        if windows:
            log_search_step(f"✅ Found window: {windows[0].title}")
            return windows[0]
        time.sleep(0.5)
    logger.warning(f"⏰ Timeout: No window found with title containing '{title_substring}'")
    return None


def add_watermark(image_path: str, id_number: str, user_name: str):
    """Add a watermark to the image."""
    try:
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        text = f"ID: {id_number} | User: {user_name} | Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        font = ImageFont.load_default()
        text_position = (10, image.height - 20)
        draw.text(text_position, text, fill="black", font=font)
        image.save(image_path)
        log_search_step("💧 Watermark added.")
    except Exception as e:
        logger.warning(f"⚠️ Failed to add watermark: {e}")


def save_as_pdf(image_path: str, pdf_path: str):
    """Save the image as a PDF."""
    try:
        image = Image.open(image_path).convert("RGB")
        image.save(pdf_path, "PDF")
        log_search_step(f"📄 Saved PDF to: {pdf_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to save PDF: {e}")


def log_query_entry(data: dict):
    """Log the search query details to a JSON file."""
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/queries.json"
    if os.path.exists(log_file):
        with open(log_file, "r+", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
            existing.append(data)
            f.seek(0)
            json.dump(existing, f, ensure_ascii=False, indent=2)
    else:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump([data], f, ensure_ascii=False, indent=2)


def run_agron_and_capture(id_number: str, user_name: str) -> dict:
    """Run Agron automation and capture the result."""
    reset_search_log_counter()
    log_search_step(f"▶️ Starting search for ID: {id_number}")

    if not (id_number.isdigit() and len(id_number) == 9):
        raise ValueError("❌ Invalid ID number. Must be 9 digits.")

    start_time = time.time()
    log_search_step("Launching Agron...")

    agr_path = r"C:\\Users\\USER\\Desktop\\אגרון\\אגרון"
    exe_path = os.path.join(agr_path, "ap2006.exe")

    try:
        subprocess.Popen(exe_path, cwd=agr_path)
        log_search_step("✅ Agron executable launched.")
    except Exception as e:
        logger.error(f"❌ Failed to launch Agron: {str(e)}")
        raise

    reg_window = wait_for_window("רישום", timeout=10)
    if not reg_window:
        raise RuntimeError("❌ Registration window not found.")
    pyautogui.write(AGRON_LICENSE, interval=0.1)
    time.sleep(ACTION_DELAY)
    pyautogui.press("enter")
    log_search_step("🔑 License entered.")
    time.sleep(ACTION_DELAY)

    main_window = wait_for_window("אגרון פלוס 2006", timeout=20)
    if not main_window:
        raise RuntimeError("❌ Agron main window did not appear.")
    try:
        main_window.activate()
        main_window.maximize()
        log_search_step("🪟 Focused on Agron window.")
    except Exception as e:
        logger.warning(f"⚠️ Could not focus window: {str(e)}")

    log_search_step("⏳ Waiting 15 seconds for Agron to fully load...")
    time.sleep(15)

    pyautogui.click(x=323, y=44)  # Filter
    log_search_step("🔍 Clicked filter button.")
    time.sleep(ACTION_DELAY)

    pyautogui.write(id_number, interval=0.05)
    log_search_step("⌨️ Entered ID number.")
    time.sleep(ACTION_DELAY)

    pyautogui.click(x=914, y=808)  # Search
    log_search_step("🔎 Clicked search button.")
    time.sleep(ACTION_DELAY)

    pyautogui.doubleClick(x=1229, y=470)  # Open result
    log_search_step("📂 Opened result.")
    time.sleep(ACTION_DELAY)

    folder = os.path.join("screenshots", datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"result_{id_number}.png")
    pdf_path = path.replace(".png", ".pdf")

    pyautogui.screenshot(region=(622, 207, 700, 473)).save(path)
    log_search_step(f"📸 Screenshot saved to: {path}")
    time.sleep(ACTION_DELAY)

    add_watermark(path, id_number, user_name)
    time.sleep(ACTION_DELAY)

    save_as_pdf(path, pdf_path)
    time.sleep(ACTION_DELAY)

    for i in range(3):
        pyautogui.hotkey("alt", "f4")
        log_search_step(f"❌ Closed window {i+1}/3")
        time.sleep(ACTION_DELAY)

    duration = time.time() - start_time
    log_search_step(f"⏱️ Execution completed in {duration:.2f} seconds")

    log_query_entry({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_name": user_name,
        "id_number": id_number,
        "duration_sec": round(duration, 2),
        "status": "ok"
    })

    return {
        "status": "ok",
        "path": path,
        "pdf_path": pdf_path,
        "duration": round(duration, 2)
    }


def run_agron_and_capture_with_cancel_support(id_number: str, user_id: int, user_name: str) -> tuple[dict | None, bool]:
    """Run Agron with cancel support."""
    if should_cancel(user_id):
        pyautogui.hotkey("alt", "f4")
        return None, True

    result = run_agron_and_capture(id_number, user_name)

    if should_cancel(user_id):
        pyautogui.hotkey("alt", "f4")
        if os.path.exists(result["path"]):
            os.remove(result["path"])
        if os.path.exists(result["pdf_path"]):
            os.remove(result["pdf_path"])
        return None, True

    return result, False
