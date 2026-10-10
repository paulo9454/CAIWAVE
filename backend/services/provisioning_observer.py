import asyncio

from backend.models.provisioning_run import ProvisioningRun
from backend.services.provisioning_repository import ProvisioningRepository


class ProvisioningObserver:
    TERMINAL_STATUSES = {"active", "failed"}

    def __init__(self):
        self.runs = {}
        self._lock = asyncio.Lock()

    async def start(self, router_id: str):
        async with self._lock:
            run = ProvisioningRun(router_id)
            run.log("Provisioning started")
            self.runs[router_id] = run
            return run

    def _get_current_run(self, router_id: str, run=None):
        current = self.runs.get(router_id)
        candidate = run if run is not None else current

        if candidate is None or candidate is not current:
            return None

        if candidate.status in self.TERMINAL_STATUSES:
            return None

        return candidate

    async def _finish(
        self,
        router_id: str,
        status: str,
        run=None,
        script: str = "",
        error: str = "",
    ):
        async with self._lock:
            current_run = self._get_current_run(router_id, run)
            if current_run is None:
                return

            previous_status = current_run.status
            previous_finished_at = current_run.finished_at
            previous_error = current_run.error
            previous_logs = list(current_run.logs)

            if status == "active":
                current_run.log("Provisioning successful")
                current_run.mark_success()
                record = {
                    "router_id": router_id,
                    "status": "success",
                    "script": script,
                    "logs": list(current_run.logs),
                }
            else:
                current_run.log(f"Provisioning failed: {error}")
                current_run.mark_failed(error)
                record = {
                    "router_id": router_id,
                    "status": "failed",
                    "error": error,
                    "logs": list(current_run.logs),
                }

            try:
                await ProvisioningRepository.save(record)
            except Exception:
                current_run.status = previous_status
                current_run.finished_at = previous_finished_at
                current_run.error = previous_error
                current_run.logs[:] = previous_logs
                raise

    async def success(self, router_id: str, script: str = "", run=None):
        await self._finish(router_id, "active", run=run, script=script)

    async def fail(self, router_id: str, error: str, run=None):
        await self._finish(router_id, "failed", run=run, error=error)


observer = ProvisioningObserver()
