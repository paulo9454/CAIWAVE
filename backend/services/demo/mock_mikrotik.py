def get_router_status():
    return {
        "status": "online",
        "active_users": 12,
        "cpu": "12%",
        "memory": "45%",
        "mode": "demo"
    }

def create_session(user):
    return {
        "session_id": "demo-session-001",
        "status": "active",
        "ip": "10.10.10.5"
    }
