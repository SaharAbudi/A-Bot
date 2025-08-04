# session.py

_user_last_id = {}

def set_last_id(user_id: int, id_number: str):
    _user_last_id[user_id] = id_number

def get_last_id(user_id: int) -> str | None:
    return _user_last_id.get(user_id)
