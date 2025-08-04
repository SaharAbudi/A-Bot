import json
import os

HISTORY_PATH = os.path.join("logs", "history.json")

if not os.path.exists(HISTORY_PATH):
    print("❌ logs/history.json not found.")
    exit()

with open(HISTORY_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

migrated = 0

for user_id, records in data.items():
    for record in records:
        # שינוי שם שדה
        if "duration" in record and "duration_sec" not in record:
            record["duration_sec"] = record.pop("duration")
            migrated += 1
        # הוספת סטטוס ברירת מחדל
        if "status" not in record:
            record["status"] = "completed"
            migrated += 1

with open(HISTORY_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Migration complete. {migrated} changes made.")
