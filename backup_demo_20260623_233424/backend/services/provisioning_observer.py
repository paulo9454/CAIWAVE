from models.provisioning_run import ProvisioningRun
from services.provisioning_repository import ProvisioningRepository


class ProvisioningObserver:
    def __init__(self):
        self.runs = {}

    def start(self, router_id: str):
        run = ProvisioningRun(router_id)
        run.log("Provisioning started")
        self.runs[router_id] = run
        return run

    def success(self, router_id: str, script: str = ""):
        run = self.runs.get(router_id)
        if not run:
            return

        run.log("Provisioning successful")
        run.mark_success()

        ProvisioningRepository.save_sync({
            "router_id": router_id,
            "status": "success",
            "script": script,
            "logs": run.logs,
        })

    def fail(self, router_id: str, error: str):
        run = self.runs.get(router_id)
        if not run:
            return

        run.log(f"Provisioning failed: {error}")
        run.mark_failed(error)

        ProvisioningRepository.save_sync({
            "router_id": router_id,
            "status": "failed",
            "error": error,
            "logs": run.logs,
        })


observer = ProvisioningObserver()
