def radius_authenticate(username, password):
    return {
        "status": "Access-Accept",
        "session_time": 3600,
        "rate_limit": "10M/10M",
        "mode": "demo"
    }

def radius_accounting(*args, **kwargs):
    return {"status": "ok", "demo": True}
