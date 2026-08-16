from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])

    async def find_one(self, query, projection=None):
        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                result = dict(document)
                result.pop("_id", None)
                return result

        return None

    async def update_one(self, query, operation, upsert=False):
        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                document.update(operation.get("$set", {}))
                return SimpleNamespace(modified_count=1)

        if upsert:
            new_document = dict(operation.get("$setOnInsert", {}))
            new_document.update(operation.get("$set", {}))
            self.documents.append(new_document)

        return SimpleNamespace(modified_count=0)

    async def insert_one(self, document):
        self.documents.append(dict(document))
        return SimpleNamespace(inserted_id=document.get("id", "fake-id"))


@pytest.fixture
def discovery_environment(monkeypatch):
    router = {
        "id": "router-1",
        "nas_identifier": "CAIWAVE-TEST",
        "hotspot_id": "hotspot-1",
        "owner_id": "owner-1",
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        router_diagnostics=FakeCollection(),
        router_events=FakeCollection(),
    )

    monkeypatch.setattr(server, "db", fake_db)

    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    with TestClient(app) as client:
        yield client, fake_db


def valid_payload():
    return {
        "nas_identifier": "CAIWAVE-TEST",
        "router": {
            "board_name": "hAP-test",
            "routeros_version": "7.18",
            "architecture": "arm",
        },
        "interfaces": [
            {
                "name": "ether1",
                "type": "ethernet",
                "running": True,
            },
            {
                "name": "ether2",
                "type": "ethernet",
                "running": True,
            },
            {
                "name": "wlan1",
                "type": "wireless",
                "running": True,
            },
            {
                "name": "bridge-hotspot",
                "type": "bridge",
                "running": True,
            },
        ],
        "bridges": [
            {
                "name": "bridge-hotspot",
                "running": True,
            }
        ],
        "bridge_ports": [
            {
                "bridge": "bridge-hotspot",
                "interface": "ether2",
            }
        ],
        "vlans": [],
        "addresses": [],
        "routes": [],
        "dhcp_servers": [
            {
                "name": "caiwave-dhcp-hotspot",
                "interface": "bridge-hotspot",
                "address-pool": "caiwave-pool-hotspot",
            }
        ],
        "hotspots": [
            {
                "name": "caiwave-hotspot",
                "interface": "bridge-hotspot",
                "profile": "caiwave-profile",
            }
        ],
        "routes": [],
        "packages": [],
        "wireless_interfaces": [],
    }


def test_discovery_endpoint_accepts_registered_router(
    discovery_environment,
):
    client, fake_db = discovery_environment

    response = client.post(
        "/api/mikrotik-onboard/discovery",
        json=valid_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["router_id"] == "router-1"
    assert body["nas_identifier"] == "CAIWAVE-TEST"
    assert body["capabilities"]["supports_wireless"] is True
    assert body["capabilities"]["wireless_interfaces"] == ["wlan1"]
    assert body["capabilities"]["bridge_count"] == 1
    assert body["capabilities"]["dhcp_server_count"] == 1
    assert body["capabilities"]["hotspot_count"] == 1

    stored_router = fake_db.mikrotik_routers.documents[0]

    assert "discovery" in stored_router
    assert stored_router["discovery"]["snapshot"]["router_id"] == "router-1"

    assert len(fake_db.router_events.documents) == 1
    assert (
        fake_db.router_events.documents[0]["event_type"]
        == "discovery"
    )


def test_discovery_endpoint_returns_404_for_unknown_router(
    discovery_environment,
):
    client, _ = discovery_environment

    payload = valid_payload()
    payload["nas_identifier"] = "CAIWAVE-UNKNOWN"

    response = client.post(
        "/api/mikrotik-onboard/discovery",
        json=payload,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Router not registered"


def test_discovery_endpoint_returns_422_for_invalid_payload(
    discovery_environment,
):
    client, _ = discovery_environment

    payload = valid_payload()
    del payload["router"]["routeros_version"]

    response = client.post(
        "/api/mikrotik-onboard/discovery",
        json=payload,
    )

    assert response.status_code == 422
    assert "Invalid router discovery payload" in response.json()["detail"]
