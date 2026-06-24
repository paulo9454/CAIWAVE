import json
import datetime
import os

AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "/app/logs/audit.log")


def _write_log(entry: dict):
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def audit_log(
        event_type: str,
        message: str,
        meta: dict = None,
        level: str = "INFO",
        trace_id: str = None,
        service: str = None,
        action: str = None,
        status: str = "success",
        ):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_type": event_type,
        "level": level,
        "message": message,
        "meta": meta or {},
        "trace_id": trace_id,
        "service": service,
        "action": action,
        "status": status,
    }
    _write_log(entry)
    print(f"[AUDIT:{level}] {event_type} - {message}")
