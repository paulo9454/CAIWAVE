def create_session(user_id, package):
    return {
        "session_id": "demo-session-xyz",
        "status": "active",
        "bandwidth": "10Mbps",
        "expires_in": 3600
    }

def check_session(session_id):
    return {
        "active": True,
        "remaining_time": 2400
    }
