from collections import defaultdict

# in-memory session store (resets on restart)
sessions = defaultdict(dict)

def update_session(user_id, key, value):
    sessions[user_id][key] = value

def get_session(user_id):
    return sessions.get(user_id, {})

def clear_session(user_id):
    sessions.pop(user_id, None)
