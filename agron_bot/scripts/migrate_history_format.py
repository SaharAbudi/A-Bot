import json
from collections import defaultdict

OLD_PATH = "logs/history.json"
NEW_PATH = "logs/history.json"  # אפשר לשנות אם רוצים לגבות קודם

with open(OLD_PATH, "r", encoding="utf-8") as f:
    old_data = json.load(f)

if not isinstance(old_data, list):
    print("✅ Already in new format.")
    exit()

converted = defaultdict(list)
for record in old_data:
    user_id = str(record.get("user_id"))
    if user_id:
        # הסר user_id מתוך כל רשומה – עכשיו זה ברמת המפתח
        clean = {k: v for k, v in record.items() if k != "user_id"}
        converted[user_id].append(clean)

with open(NEW_PATH, "w", encoding="utf-8") as f:
    json.dump(converted, f, indent=2, ensure_ascii=False)

print("✅ Converted history.json to new format.")
