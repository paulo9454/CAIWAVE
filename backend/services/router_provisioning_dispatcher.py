from backend.utils.router_normalizer import normalize_router
from backend.services.mikrotik_builder import build_mikrotik_script
from backend.services.provisioning_observer import observer
import asyncio


def dispatch_router_provisioning(router: dict, mode: str = "script"):

    router_id = router.get("nas_identifier", "unknown")
    run = observer.start(router_id)

    try:
        router = normalize_router(router)

        script = build_mikrotik_script(router)
        if not isinstance(script, str):
            raise TypeError("Provisioning engine must return string script")
        if not isinstance(script, str):
            raise TypeError("build_mikrotik_script must return str")
        if hasattr(script, "__await__"):
            raise RuntimeError("build_mikrotik_script must be sync")
        run.log("Script generated")

        run.log("Provisioning dispatched")

        router_name = router.get("name", "unknown")

        if mode == "script":
            return {
                "status": "success",
                "router": router_name,
                "script": str(script)
            }

        if mode == "file":
            filename = f"/tmp/{router_name}_mikrotik.rsc"
            with open(filename, "w") as f:
                f.write(script)

            getattr(observer, "success", lambda *a, **k: None)(router_id, script=script)

            return {
                "status": "saved",
                "router": router_name,
                "file": filename,
                "script": str(script)
            }

        raise ValueError(f"Unknown mode: {mode}")

    except Exception as e:
        getattr(observer, "fail", lambda *a, **k: None)(router_id, str(e))

        return {
            "status": "error",
            "message": str(e)
        }
