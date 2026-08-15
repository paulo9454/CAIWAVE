from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])

    async def find_one(self, query, projection=None, sort=None):
        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                result = dict(document)
                result.pop("_id", None)
                return result

        return None


async def fake_role_checker():
    return {
        "id": "owner-1",
        "role": server.UserRole.HOTSPOT_OWNER.value,
    }


def create_diagnostics_client(fake_db, monkeypatch):
    monkeypatch.setattr(server, "db", fake_db)

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    diagnostics_path = (
        "/api/mikrotik-onboard/routers/{router_id}/diagnostics"
    )

    for route in app.routes:
        if getattr(route, "path", None) == diagnostics_path:
            if not route.dependant.dependencies:
                raise AssertionError(
                    "Diagnostics route has no role dependency"
                )

            dependency = route.dependant.dependencies[0].call

            app.dependency_overrides[dependency] = (
                fake_role_checker
            )
            break
    else:
        raise AssertionError(
            "Diagnostics route was not registered"
        )

    return TestClient(app)


def test_diagnostics_surfaces_discovery(monkeypatch):
    router = {
        "id": "router-1",
        "nas_identifier": "CAIWAVE-TEST",
        "hotspot_id": "hotspot-1",
        "owner_id": "owner-1",
        "status": "online",
        "health_status": "healthy",
        "connection_confirmed": True,
        "discovery": {
            "received_at": "2026-08-15T15:00:00+00:00",
            "snapshot": {
                "router_id": "router-1",
                "board_name": "hAP-test",
                "routeros_version": "7.18",
                "architecture": "arm",
            },
            "capabilities": {
                "supports_wireless": True,
                "wireless_interfaces": ["wlan1"],
                "interface_count": 3,
            },
        },
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        router_diagnostics=FakeCollection(),
        radius_auth_logs=FakeCollection(),
        sessions=FakeCollection(),
    )

    with create_diagnostics_client(
        fake_db,
        monkeypatch,
    ) as client:
        response = client.get(
            "/api/mikrotik-onboard/routers/"
            "router-1/diagnostics"
        )

    assert response.status_code == 200

    body = response.json()

    assert body["router"]["discovery_received"] is True
    assert (
        body["router"]["discovery_received_at"]
        == "2026-08-15T15:00:00+00:00"
    )
    assert body["router"]["wireless_detected"] is True
    assert (
        body["discovery"]["snapshot"]["board_name"]
        == "hAP-test"
    )
    assert (
        body["discovery"]["capabilities"]["wireless_interfaces"]
        == ["wlan1"]
    )


def test_diagnostics_without_discovery_returns_empty_discovery_state(
    monkeypatch,
):
    router = {
        "id": "router-2",
        "nas_identifier": "CAIWAVE-NODISCOVERY",
        "hotspot_id": "hotspot-2",
        "owner_id": "owner-1",
        "status": "online",
        "health_status": "healthy",
        "connection_confirmed": True,
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        router_diagnostics=FakeCollection(),
        radius_auth_logs=FakeCollection(),
        sessions=FakeCollection(),
    )

    with create_diagnostics_client(
        fake_db,
        monkeypatch,
    ) as client:
        response = client.get(
            "/api/mikrotik-onboard/routers/"
            "router-2/diagnostics"
        )

    assert response.status_code == 200

    body = response.json()

    assert body["router"]["discovery_received"] is False
    assert body["router"]["wireless_detected"] is False
    assert body["discovery"]["snapshot"] is None
    assert body["discovery"]["capabilities"] is None
