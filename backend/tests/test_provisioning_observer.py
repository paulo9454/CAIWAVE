from backend.services.provisioning_observer import ProvisioningObserver
from backend.services.provisioning_repository import ProvisioningRepository


def test_duplicate_success_is_idempotent(monkeypatch):
    saved = []
    monkeypatch.setattr(
        ProvisioningRepository,
        "save_sync",
        lambda record: saved.append(record),
    )
    observer = ProvisioningObserver()
    run = observer.start("router-1")

    observer.success("router-1", script="script", run=run)
    first_finished_at = run.finished_at
    first_logs = list(run.logs)

    observer.success("router-1", script="script-again", run=run)

    assert run.status == "active"
    assert run.finished_at == first_finished_at
    assert run.logs == first_logs
    assert len(saved) == 1


def test_failure_after_success_cannot_change_terminal_run(monkeypatch):
    saved = []
    monkeypatch.setattr(
        ProvisioningRepository,
        "save_sync",
        lambda record: saved.append(record),
    )
    observer = ProvisioningObserver()
    run = observer.start("router-1")

    observer.success("router-1", script="script", run=run)
    first_logs = list(run.logs)

    observer.fail("router-1", "late failure", run=run)

    assert run.status == "active"
    assert run.error is None
    assert run.logs == first_logs
    assert len(saved) == 1
    assert saved[0]["status"] == "success"


def test_success_after_failure_cannot_change_terminal_run(monkeypatch):
    saved = []
    monkeypatch.setattr(
        ProvisioningRepository,
        "save_sync",
        lambda record: saved.append(record),
    )
    observer = ProvisioningObserver()
    run = observer.start("router-1")

    observer.fail("router-1", "initial failure", run=run)
    first_finished_at = run.finished_at
    first_logs = list(run.logs)

    observer.success("router-1", script="late script", run=run)

    assert run.status == "failed"
    assert run.error == "initial failure"
    assert run.finished_at == first_finished_at
    assert run.logs == first_logs
    assert len(saved) == 1
    assert saved[0]["status"] == "failed"


def test_stale_callback_cannot_finish_newer_run(monkeypatch):
    saved = []
    monkeypatch.setattr(
        ProvisioningRepository,
        "save_sync",
        lambda record: saved.append(record),
    )
    observer = ProvisioningObserver()
    old_run = observer.start("router-1")
    new_run = observer.start("router-1")

    observer.fail("router-1", "late error from old run", run=old_run)

    assert observer.runs["router-1"] is new_run
    assert new_run.status == "pending"
    assert new_run.error is None
    assert saved == []

    observer.success("router-1", script="new script", run=new_run)

    assert new_run.status == "active"
    assert len(saved) == 1
    assert saved[0]["status"] == "success"


def test_script_generation_does_not_mark_router_provisioned(monkeypatch):
    from backend.services import router_provisioning_dispatcher as dispatcher

    observer = ProvisioningObserver()
    monkeypatch.setattr(dispatcher, "observer", observer)
    monkeypatch.setattr(
        dispatcher,
        "normalize_router",
        lambda router: router,
    )
    monkeypatch.setattr(
        dispatcher,
        "build_mikrotik_script",
        lambda router: "/system identity print",
    )

    result = dispatcher.dispatch_router_provisioning(
        {"nas_identifier": "router-script-test", "name": "test-router"},
        mode="script",
    )

    run = observer.runs["router-script-test"]
    assert result["status"] == "success"
    assert result["script"] == "/system identity print"
    assert run.status == "pending"
    assert run.finished_at is None


def test_concurrent_success_and_failure_save_only_one_terminal_result(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    saved = []
    barrier = Barrier(3)

    monkeypatch.setattr(
        ProvisioningRepository,
        "save_sync",
        lambda record: saved.append(record),
    )

    observer = ProvisioningObserver()
    run = observer.start("router-concurrent")

    def report_success():
        barrier.wait()
        observer.success("router-concurrent", script="script", run=run)

    def report_failure():
        barrier.wait()
        observer.fail("router-concurrent", "late error", run=run)

    with ThreadPoolExecutor(max_workers=2) as executor:
        success_future = executor.submit(report_success)
        failure_future = executor.submit(report_failure)
        barrier.wait()
        success_future.result()
        failure_future.result()

    assert len(saved) == 1
    assert saved[0]["status"] in {"success", "failed"}

    if saved[0]["status"] == "success":
        assert run.status == "active"
        assert run.error is None
    else:
        assert run.status == "failed"
        assert run.error == "late error"


def test_failed_persistence_restores_run_and_allows_retry(monkeypatch):
    saved = []
    attempts = {"count": 0}

    def save_with_one_failure(record):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary database failure")
        saved.append(record)

    monkeypatch.setattr(
        ProvisioningRepository,
        "save_sync",
        save_with_one_failure,
    )

    observer = ProvisioningObserver()
    run = observer.start("router-retry")
    original_logs = list(run.logs)

    import pytest

    with pytest.raises(RuntimeError, match="temporary database failure"):
        observer.success("router-retry", script="script", run=run)

    assert run.status == "pending"
    assert run.finished_at is None
    assert run.error is None
    assert run.logs == original_logs
    assert saved == []

    observer.success("router-retry", script="script", run=run)

    assert run.status == "active"
    assert len(saved) == 1
    assert saved[0]["status"] == "success"


def test_file_saved_but_status_persistence_fails(monkeypatch, tmp_path):
    from pathlib import Path

    from backend.services import router_provisioning_dispatcher as dispatcher

    observer = ProvisioningObserver()
    monkeypatch.setattr(dispatcher, "observer", observer)
    monkeypatch.setattr(dispatcher, "normalize_router", lambda router: router)
    monkeypatch.setattr(
        dispatcher, "build_mikrotik_script", lambda router: "/system identity print"
    )

    real_open = open

    def temporary_open(path, *args, **kwargs):
        if str(path).startswith("/tmp/") and str(path).endswith("_mikrotik.rsc"):
            path = tmp_path / Path(path).name
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", temporary_open)

    def fail_persistence(record):
        raise RuntimeError("simulated persistence failure")

    monkeypatch.setattr(ProvisioningRepository, "save_sync", fail_persistence)

    result = dispatcher.dispatch_router_provisioning(
        {"nas_identifier": "diagnostic-router", "name": "diagnostic-router"},
        mode="file",
    )

    run = observer.runs["diagnostic-router"]
    output_file = tmp_path / "diagnostic-router_mikrotik.rsc"

    assert result["status"] == "saved"
    assert "status could not be recorded" in result["warning"]
    assert output_file.exists()
    assert output_file.read_text() == "/system identity print"
    assert run.status == "pending"
    assert run.finished_at is None
