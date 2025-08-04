import json
import os
from datetime import datetime
from threading import Lock

HISTORY_FILE = "logs/history.json"
history_lock = Lock()

def log_run(user_id: int, id_number: str, duration: float | None, status: str):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "id_number": id_number,
        "duration_sec": duration,
        "status": status
    }

    with history_lock:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        uid_str = str(user_id)
        data.setdefault(uid_str, []).append(entry)

        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def get_user_history(user_id: int, limit=5) -> list:
    with history_lock:
        if not os.path.exists(HISTORY_FILE):
            return []

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get(str(user_id), [])[-limit:]

def get_user_stats(user_id: int) -> dict:
    with history_lock:
        if not os.path.exists(HISTORY_FILE):
            return {}

        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data.get(str(user_id), [])
        if not records:
            return {}

        total_runs = len(records)

        completed = [
            r for r in records
            if r.get("status") == "completed" and r.get("duration_sec") is not None
        ]

        total_cancelled = sum(
            1 for r in records if r.get("status") == "cancelled"
        )

        avg_runtime = round(
            sum(r["duration_sec"] for r in completed),
            2
        ) / len(completed) if completed else 0

        return {
            "total_runs": total_runs,
            "avg_runtime": avg_runtime,
            "total_cancelled": total_cancelled
        }