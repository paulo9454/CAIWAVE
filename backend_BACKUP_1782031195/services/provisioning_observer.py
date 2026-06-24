from backend.models.provisioning_run import ProvisioningRun
from backend.models.provisioning_record import ProvisioningRecord
from backend.services.provisioning_repository import ProvisioningRepository


class ProvisioningObserver:
    def __init__(self):
        self.runs = {}

    def start(self, router_id: str) -> ProvisioningRun:
        run = ProvisioningRun(router_id)
        run.log("Provisioning started")
        self.runs[router_id] = run
        return run

    async def success(self, router_id: str, script: str = ""):
        run = self.runs.get(router_id)
        if run:
            run.log("Provisioning successful")
            run.mark_success()

            await ProvisioningRepository.save(
                ProvisioningRecord(
                    router_id=router_id,
                    status="success",
                    script=script,
                    logs=run.logs,
                )
            )

    async def fail(self, router_id: str, error: str):
        run = self.runs.get(router_id)
        if run:
            run.log(f"Provisioning failed: {error}")
            run.mark_failed(error)

            await ProvisioningRepository.save(
                ProvisioningRecord(
                    router_id=router_id,
                    status="failed",
                    logs=run.logs,
                    error=error,
                )
            )


observer = ProvisioningObserver()
