# cancel_state.py
from collections import defaultdict
import threading

cancel_flags = defaultdict(threading.Event)
in_progress_flags = defaultdict(threading.Event)

def mark_cancel(user_id: int):
    cancel_flags[user_id].set()

def should_cancel(user_id: int) -> bool:
    return cancel_flags[user_id].is_set()

def clear_cancel(user_id: int):
    cancel_flags[user_id].clear()
    in_progress_flags[user_id].clear()

def mark_in_progress(user_id: int):
    in_progress_flags[user_id].set()
