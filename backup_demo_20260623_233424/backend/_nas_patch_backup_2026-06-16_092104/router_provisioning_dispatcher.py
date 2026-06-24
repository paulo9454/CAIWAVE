from utils.router_normalizer import normalize_router
from services.provisioning_tracker import log_provisioning
from services.mikrotik_builder import build_mikrotik_script
import datetime
import asyncio


def dispatch_router_provisioning(router: dict, mode: str = "script"):
    router = normalize_router(router)
    """
    Router Provisioning Dispatcher (Phase 1)

    Modes:
    - script: returns MikroTik RSC script
    - file: saves script to /tmp
    """

    script = build_mikrotik_script(router)

    # safe async logging fallback (FIXED)
    try:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(log_provisioning(router, script))
        except RuntimeError:
            # no running loop (fallback to thread)
            import threading

            threading.Thread(
                target=lambda: asyncio.run(log_provisioning(router, script)),
                daemon=True
            ).start()

    except Exception as e:
        print("Provisioning log failed:", e)

    router_name = router.get("name", "unknown")
    timestamp = datetime.datetime.utcnow().isoformat()

    print(f"[{timestamp}] Router={router_name} Mode={mode}")

    if mode == "script":
        return {
            "status": "success",
            "router": router_name,
            "script": script
        }

    if mode == "file":
        filename = f"/tmp/{router_name}_mikrotik.rsc"
        with open(filename, "w") as f:
            f.write(script)

        return {
            "status": "saved",
            "router": router_name,
            "file": filename,
            "script": script
        }

    return {
        "status": "error",
        "message": f"Unknown mode: {mode}"
    }
