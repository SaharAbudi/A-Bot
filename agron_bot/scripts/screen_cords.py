import pyautogui
import time

print("הזז את העכבר למיקום הכפתור 'סינון...' בתוך 5 שניות...")
time.sleep(5)

last_coords = None

try:
    while True:
        x, y = pyautogui.position()
        last_coords = (x, y)
        print(f"מיקום נוכחי: X={x}, Y={y}", end="\r")
        time.sleep(0.1)
except KeyboardInterrupt:
    if last_coords:
        x, y = last_coords
        print(f"\n📍 המיקום האחרון שנרשם: X={x}, Y={y}")
        print(f"להדבקה בקוד: pyautogui.click(x={x}, y={y})")
    else:
        print("\n❌ לא נרשמו קואורדינטות.")
