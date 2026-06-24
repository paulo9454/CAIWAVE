from backend.utils.router_normalizer import normalize_router
from backend.services.mikrotik_builder import build_mikrotik_script
from backend.services.provisioning_observer import observer
import datetime
import asyncio


def dispatch_router_provisioning(router: dict, mode: str = "script"):

    router_id = router.get("nas_identifier", "unknown")
    run = observer.start(router_id)

    try:
        router = normalize_router(router)

        script = build_mikrotik_script(router)
        run.log("Script generated")

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(lambda: None)
        except RuntimeError:
            pass

        run.log("Provisioning dispatched")

        router_name = router.get("name", "unknown")

        if mode == "script":
            observer.success(router_id, script=script)
            return {
                "status": "success",
                "router": router_name,
                "script": script
            }

        if mode == "file":
            filename = f"/tmp/{router_name}_mikrotik.rsc"
            with open(filename, "w") as f:
                f.write(script)

            observer.success(router_id, script=script)

            return {
                "status": "saved",
                "router": router_name,
                "file": filename,
                "script": script
            }

        raise ValueError(f"Unknown mode: {mode}")

    except Exception as e:
        observer.fail(router_id, str(e))

        return {
            "status": "error",
            "message": str(e)
        }
