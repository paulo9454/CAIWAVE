import logging

from backend.models.provisioning_run import ProvisioningRun
from backend.services.provisioning_tracker import log_provisioning


logger = logging.getLogger(__name__)


class ProvisioningObserver:
    def __init__(self):
        self.runs = {}

    def start(self, router_id: str):
        run = ProvisioningRun(router_id)
        run.log("Provisioning started")
        self.runs[router_id] = run
        return run

    async def success(
        self,
        router_id: str,
        script: str = "",
        router: dict | None = None,
    ):
        run = self.runs.get(router_id)

        if not run:
            return

        run.log("Provisioning successful")
        run.mark_success()

        router_data = router or {
            "id": router_id,
            "nas_identifier": router_id,
        }

        try:
            await log_provisioning(
                router=router_data,
                script=script,
                status="success",
            )
        except Exception:
            logger.exception(
                "Provisioning persistence failed for %s",
                router_data.get("nas_identifier", router_id),
            )

    async def fail(
        self,
        router_id: str,
        error: str,
        router: dict | None = None,
    ):
        run = self.runs.get(router_id)

        if not run:
            return

        run.log(f"Provisioning failed: {error}")
        run.mark_failed(error)

        router_data = router or {
            "id": router_id,
            "nas_identifier": router_id,
        }

        try:
            await log_provisioning(
                router=router_data,
                script="",
                status="failed",
            )
        except Exception:
            logger.exception(
                "Provisioning failure persistence failed for %s",
                router_data.get("nas_identifier", router_id),
            )


observer = ProvisioningObserver()
