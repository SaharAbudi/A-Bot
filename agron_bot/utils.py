def is_valid_id(id_number: str) -> bool:
    return id_number.isdigit() and 8 <= len(id_number) <= 9
