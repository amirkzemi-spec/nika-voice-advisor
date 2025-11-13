from collections import defaultdict

sessions = defaultdict(dict)

def get_session(user_id):
    return sessions[user_id]

def update_session(user_id, key, value):
    sessions[user_id][key] = value

def clear_session(user_id):
    sessions.pop(user_id, None)
