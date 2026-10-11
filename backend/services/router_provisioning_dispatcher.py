from backend.utils.router_normalizer import normalize_router
from backend.services.mikrotik_builder import build_mikrotik_script
from backend.services.provisioning_observer import observer


async def dispatch_router_provisioning(router: dict, mode: str = "script"):
    router_id = router.get("nas_identifier", "unknown")
    run = await observer.start(router_id)

    try:
        router = normalize_router(router)
        script = build_mikrotik_script(router)

        if not isinstance(script, str):
            raise TypeError("Provisioning engine must return string script")
        if hasattr(script, "__await__"):
            raise RuntimeError("build_mikrotik_script must be sync")

        run.log("Script generated")
        run.log("Provisioning dispatched")
        router_name = router.get("name", "unknown")

        if mode == "script":
            return {
                "status": "success",
                "router": router_name,
                "script": str(script),
            }

        if mode == "file":
            filename = f"/tmp/{router_name}_mikrotik.rsc"
            with open(filename, "w") as output_file:
                output_file.write(script)

            try:
                await observer.success(router_id, script=script, run=run)
            except Exception as persistence_error:
                # The file exists; keep the run retryable if its status
                # could not be persisted. Do not misreport it as a failure.
                return {
                    "status": "saved",
                    "router": router_name,
                    "file": filename,
                    "script": str(script),
                    "warning": (
                        "Script saved, but provisioning status could not be "
                        f"recorded: {persistence_error}"
                    ),
                }

            return {
                "status": "saved",
                "router": router_name,
                "file": filename,
                "script": str(script),
            }

        raise ValueError(f"Unknown mode: {mode}")

    except Exception as error:
        try:
            await observer.fail(router_id, str(error), run=run)
        except Exception:
            # Preserve the original dispatcher error if failure recording
            # also encounters a persistence error.
            pass

        return {
            "status": "error",
            "message": str(error),
        }
