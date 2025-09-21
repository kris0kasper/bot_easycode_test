import json
import os

STORAGE_FILE = "birthdays.json"

def load_data():
    if not os.path.exists(STORAGE_FILE):
        return {}
    try:
        with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}

def save_data(data):
    with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_birthdays(user_id):
    data = load_data()
    user_key = str(user_id)
    return data.get(user_key, {})

def add_birthday(user_id, name, date_str):
    data = load_data()
    user_key = str(user_id)
    if user_key not in data:
        data[user_key] = {}
    data[user_key][name] = date_str
    save_data(data)

def delete_birthday(user_id, name):
    data = load_data()
    user_key = str(user_id)
    if user_key in data and name in data[user_key]:
        del data[user_key][name]
        save_data(data)
        return True
    return False