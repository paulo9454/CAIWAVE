import hashlib
import pytest
import asyncio
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import server
from backend.services.mikrotik_control_plane.credentials import hash_control_secret

class FakeCollection:
    def __init__(self, documents=None, collection_name=""):
        self.documents = list(documents or [])
        self.collection_name = collection_name

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

    def find(self, query, projection=None):
        matching = []

        for document in self.documents:
            matched = True

            for key, value in query.items():
                if isinstance(value, dict) and "$in" in value:
                    if document.get(key) not in value["$in"]:
                        matched = False
                        break
                elif document.get(key) != value:
                    matched = False
                    break

            if matched:
                matching.append(dict(document))

        class FakeCursor:
            def __init__(self, documents):
                self.documents = documents

            def sort(self, *args, **kwargs):
                if args:
                    sort_spec = args[0]
                    if isinstance(sort_spec, list):
                        for field, direction in reversed(sort_spec):
                            self.documents.sort(
                                key=lambda item: item.get(field),
                                reverse=direction == -1,
                            )
                return self

            async def to_list(self, length=None):
                if length is None:
                    return self.documents
                return self.documents[:length]

        return FakeCursor(matching)

    async def update_one(self, query, update):
        for document in self.documents:
            if all(
                document.get(key) == value
                for key, value in query.items()
            ):
                if "$set" in update:
                    document.update(update["$set"])
                return SimpleNamespace(matched_count=1)

        return SimpleNamespace(matched_count=0)

    async def insert_one(self, document):
        document = dict(document)

        if self.collection_name == "mikrotik_routers":
            document["discovery"] = {
                "capabilities": {
                    "supports_wireless": False,
                    "wireless_interfaces": [],
                    "bridge_count": 1,
                    "dhcp_server_count": 1,
                    "hotspot_count": 1,
                }
            }

        self.documents.append(document)

        return SimpleNamespace(
            inserted_id=document.get("id", "fake-id")
        )


def hotspot():
    return {
        "id": "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf",
        "owner_id": "4369263d-3dd3-4f80-b151-e7a499eb2897",
        "name": "Test Hotspot",
    }


def register_payload():
    return {
        "bootstrap_token": "test-token",
        "name": "Test Router",
        "hotspot_id": "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "ether3"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "mode": "fresh",
        "hotspot_enabled": True,
        "wifi_enabled": False,
        "wifi_ssid": "CAIWAVE",
        "hotspot_cidr": "10.10.0.1/24",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "login.caiwave.local",
    }


def test_register_mikrotik_runs_v2_provisioning(monkeypatch):
    fake_db = SimpleNamespace(
        hotspots=FakeCollection([hotspot()]),
        mikrotik_routers=FakeCollection(
            [],
            collection_name="mikrotik_routers",
        ),
        nas_clients=FakeCollection(),
        mikrotik_router_control_credentials=FakeCollection(),
    )
    monkeypatch.setattr(server, "db", fake_db)

    control_credential_repository = (
        server.RouterControlCredentialRepository(
            fake_db.mikrotik_router_control_credentials
        )
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        control_credential_repository,
    )
    monkeypatch.setenv(
        "RADIUS_HOST",
        "radius.caiwave.com",
    )
    monkeypatch.setenv(
        "MPESA_CALLBACK_URL",
        "https://www.caiwave.com/api/mpesa/callback",
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    async def fake_current_user():
        return {
            "id": "4369263d-3dd3-4f80-b151-e7a499eb2897",
            "role": server.UserRole.HOTSPOT_OWNER.value,
        }

    app.dependency_overrides[server.get_current_user] = fake_current_user

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/register",
            json=register_payload(),
        )

    assert response.status_code == 200

    body = response.json()

    assert body["router_name"] == "Test Router"
    assert body["nas_identifier"].startswith("CAIWAVE-TESTROUTER-")
    assert body["radius_secret"]
    assert body["status"] == "pending_discovery"
    assert body["topology_status"] == "pending_discovery"

    assert body["discovery_rsc"]["filename"].endswith("-discovery.rsc")
    assert body["discovery_rsc"]["content"]
    assert body["discovery_rsc"]["checksum"]
    assert body["control_bootstrap_rsc"]["filename"].endswith(
        "-control-bootstrap.rsc"
    )
    assert body["control_bootstrap_rsc"]["content"]
    assert body["control_bootstrap_rsc"]["checksum"]

    assert body["bootstrap_rsc"]["filename"].endswith(
        "-caiwave-bootstrap.rsc"
    )
    assert body["bootstrap_rsc"]["content"]
    assert body["bootstrap_rsc"]["checksum"]

    bootstrap = body["bootstrap_rsc"]["content"]

    assert bootstrap.endswith("\n")
    assert body["bootstrap_rsc"]["checksum"] == (
        hashlib.sha256(bootstrap.encode()).hexdigest()
    )

    discovery_marker = "CAIWAVE observational router discovery"
    control_marker = "CAIWAVE Control Agent Bootstrap"

    assert discovery_marker in bootstrap
    assert control_marker in bootstrap
    assert bootstrap.index(discovery_marker) < bootstrap.index(control_marker)

    assert "/api/mikrotik-onboard/discovery" in bootstrap
    assert "/api/mikrotik-onboard/poll" in bootstrap
    assert "/api/mikrotik-onboard/artifacts/" in bootstrap
    assert "/api/mikrotik-onboard/job-result" in bootstrap

    # The combined bootstrap intentionally contains observational
    # RouterOS "print as-value" commands used by discovery. Verify that
    # it does not contain production networking mutation commands.
    for forbidden_mutation in (
        "/ip address add",
        "/ip address set",
        "/ip address remove",
        "/ip dhcp-server add",
        "/ip dhcp-server set",
        "/ip dhcp-server remove",
        "/ip firewall add",
        "/ip firewall set",
        "/ip firewall remove",
        "/ip hotspot add",
        "/ip hotspot set",
        "/ip hotspot remove",
        "/ip route add",
        "/ip route set",
        "/ip route remove",
        "/interface bridge add",
        "/interface bridge set",
        "/interface bridge remove",
        "/interface bridge port add",
        "/interface bridge port set",
        "/interface bridge port remove",
        "/radius add",
        "/radius set",
        "/radius remove",
    ):
        assert forbidden_mutation not in bootstrap.lower()

    for interface_name in (
        "ether1",
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ):
        assert interface_name not in bootstrap.lower()

    control_bootstrap = body["control_bootstrap_rsc"]["content"]

    assert control_bootstrap.endswith("\n")
    assert body["control_bootstrap_rsc"]["checksum"] == (
        hashlib.sha256(control_bootstrap.encode()).hexdigest()
    )

    assert "CAIWAVE Control Agent Bootstrap" in control_bootstrap
    assert 'name="caiwave-control"' in control_bootstrap
    assert ":set caiwaveControlSecret" in control_bootstrap
    assert "/system scheduler add" in control_bootstrap
    assert "/system script run" in control_bootstrap

    assert "/api/mikrotik-onboard/poll" in control_bootstrap
    assert "/api/mikrotik-onboard/artifacts/" in control_bootstrap
    assert "/api/mikrotik-onboard/job-result" in control_bootstrap

    for forbidden_command in (
        "/ip address",
        "/ip dhcp-server",
        "/ip firewall",
        "/ip hotspot",
        "/ip route",
        "/interface bridge",
        "/interface bridge port",
        "/radius",
    ):
        assert forbidden_command not in control_bootstrap.lower()

    for interface_name in (
        "ether1",
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ):
        assert interface_name not in control_bootstrap.lower()

    assert "CAIWAVE observational router discovery" in body["discovery_rsc"]["content"]
    assert "/api/mikrotik-onboard/discovery" in body["discovery_rsc"]["content"]

    assert "single_rsc_provisioning" not in body


    assert len(fake_db.mikrotik_routers.documents) == 1
    assert len(fake_db.nas_clients.documents) == 1

    stored_router = fake_db.mikrotik_routers.documents[0]

    assert stored_router["id"] == body["router_id"]
    assert stored_router["hotspot_id"] == "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf"
    assert stored_router["owner_id"] == "4369263d-3dd3-4f80-b151-e7a499eb2897"
    assert stored_router["wan_interface"] is None
    assert stored_router["lan_interfaces"] is None
    assert stored_router["topology_status"] == "pending_discovery"
    assert stored_router["topology_confidence"] == "LOW"
    assert stored_router["topology_evidence"] == []
    assert stored_router["topology_warnings"] == []

    assert stored_router["create_bridge"] is True
    assert stored_router["bridge_name"] == "bridge-hotspot"
    assert stored_router["radius_host"] == "radius.caiwave.com"
    assert stored_router["provisioning_version"] == 2

    nas = fake_db.nas_clients.documents[0]

    assert stored_router["hotspot_id"] == "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf"
    assert nas["name"] == "Test Router"
    assert nas["secret"] == body["radius_secret"]
    assert nas["nas_type"] == "MikroTik"
    assert nas["is_active"] is True
    assert (
        len(
            fake_db.mikrotik_router_control_credentials.documents
        )
        == 1
    )

    stored_credential = (
        fake_db.mikrotik_router_control_credentials.documents[0]
    )

    assert stored_credential["router_id"] == body["router_id"]
    assert stored_credential["credential_id"]
    assert stored_credential["secret_hash"]
    assert stored_credential["status"] == "active"
    assert stored_credential["secret_hash"] != body["router_control_credential"]["secret"]

    assert (
        "Authorization: Bearer "
        in body["control_bootstrap_rsc"]["content"]
    )

def test_rotate_mikrotik_control_credential_for_owner(monkeypatch):
    hotspot_id = "hotspot-rotation-1"
    router_id = "router-rotation-1"

    old_credential = server.build_control_credential()

    fake_db = SimpleNamespace(
        hotspots=FakeCollection([
            {
                "id": hotspot_id,
                "owner_id": "owner-rotation-1",
            }
        ]),
        mikrotik_routers=FakeCollection([
            {
                "id": router_id,
                "name": "Rotation Router",
                "hotspot_id": hotspot_id,
                "owner_id": "owner-rotation-1",
                "nas_identifier": "CAIWAVE-ROTATION-1",
                "heartbeat_url": (
                    "https://www.caiwave.com/"
                    "api/mikrotik-onboard/heartbeat"
                ),
                "wan_interface": "ether1",
                "lan_interfaces": [
                    "ether2",
                    "ether3",
                ],
                "bridge_name": "bridge-hotspot",
            }
        ]),
        mikrotik_router_control_credentials=FakeCollection(),
    )

    credential_document = {
        "credential_id": old_credential.credential_id,
        "router_id": router_id,
        "secret_hash": old_credential.secret_hash,
        "created_at": old_credential.created_at.isoformat(),
        "expires_at": old_credential.expires_at.isoformat(),
        "status": "active",
    }

    fake_db.mikrotik_router_control_credentials.documents.append(
        credential_document
    )

    monkeypatch.setattr(server, "db", fake_db)

    repository = server.RouterControlCredentialRepository(
        fake_db.mikrotik_router_control_credentials
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    async def fake_current_user():
        return {
            "id": "owner-rotation-1",
            "role": server.UserRole.HOTSPOT_OWNER.value,
        }

    app.dependency_overrides[
        server.get_current_user
    ] = fake_current_user

    with TestClient(app) as client:
        response = client.post(
            f"/api/mikrotik-onboard/routers/"
            f"{router_id}/rotate-control-credential"
        )

    assert response.status_code == 200

    body = response.json()

    assert body["router_id"] == router_id
    assert body["router_name"] == "Rotation Router"
    assert body["nas_identifier"] == "CAIWAVE-ROTATION-1"
    assert body["credential_id"]
    assert body["secret"]
    assert body["expires_at"]

    assert body["discovery_rsc"]["content"]
    assert (
        "/api/mikrotik-onboard/discovery"
        in body["discovery_rsc"]["content"]
    )
    assert "Authorization: Bearer" in body["discovery_rsc"]["content"]
    assert body["control_bootstrap_rsc"]["content"]
    assert body["control_bootstrap_rsc"]["filename"].endswith(
        "-control-bootstrap.rsc"
    )
    assert body["control_bootstrap_rsc"]["checksum"]

    assert body["bootstrap_rsc"]["filename"].endswith(
        "-caiwave-bootstrap.rsc"
    )
    assert body["bootstrap_rsc"]["content"]
    assert body["bootstrap_rsc"]["checksum"]

    bootstrap = body["bootstrap_rsc"]["content"]

    assert bootstrap.endswith("\n")
    assert body["bootstrap_rsc"]["checksum"] == (
        hashlib.sha256(bootstrap.encode()).hexdigest()
    )

    discovery_marker = "CAIWAVE observational router discovery"
    control_marker = "CAIWAVE Control Agent Bootstrap"

    assert discovery_marker in bootstrap
    assert control_marker in bootstrap
    assert bootstrap.index(discovery_marker) < bootstrap.index(control_marker)

    assert "/api/mikrotik-onboard/discovery" in bootstrap
    assert "/api/mikrotik-onboard/poll" in bootstrap
    assert "/api/mikrotik-onboard/artifacts/" in bootstrap
    assert "/api/mikrotik-onboard/job-result" in bootstrap

    # The combined bootstrap contains observational "print as-value"
    # commands, but must not contain production networking mutations.
    for forbidden_mutation in (
        "/ip address add",
        "/ip address set",
        "/ip address remove",
        "/ip dhcp-server add",
        "/ip dhcp-server set",
        "/ip dhcp-server remove",
        "/ip firewall add",
        "/ip firewall set",
        "/ip firewall remove",
        "/ip hotspot add",
        "/ip hotspot set",
        "/ip hotspot remove",
        "/ip route add",
        "/ip route set",
        "/ip route remove",
        "/interface bridge add",
        "/interface bridge set",
        "/interface bridge remove",
        "/interface bridge port add",
        "/interface bridge port set",
        "/interface bridge port remove",
        "/radius add",
        "/radius set",
        "/radius remove",
    ):
        assert forbidden_mutation not in bootstrap.lower()

    for interface_name in (
        "ether1",
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ):
        assert interface_name not in bootstrap.lower()

    control_bootstrap = body["control_bootstrap_rsc"]["content"]

    assert "CAIWAVE Control Agent Bootstrap" in control_bootstrap
    assert "/poll" in control_bootstrap
    assert "/artifacts/" in control_bootstrap
    assert "/job-result" in control_bootstrap
    assert "/system script add" in control_bootstrap
    assert "/system scheduler add" in control_bootstrap
    assert "/system script run" in control_bootstrap

    assert "ether1" not in control_bootstrap
    assert "ether2" not in control_bootstrap
    assert "ether3" not in control_bootstrap
    assert "ether4" not in control_bootstrap
    assert "ether5" not in control_bootstrap

    assert "/ip address" not in control_bootstrap
    assert "/ip dhcp-server" not in control_bootstrap
    assert "/ip firewall" not in control_bootstrap
    assert "/ip hotspot" not in control_bootstrap
    assert "/radius" not in control_bootstrap
    assert "/interface bridge" not in control_bootstrap

    stored_credentials = (
        fake_db.mikrotik_router_control_credentials.documents
    )

    assert len(stored_credentials) == 2

    old_stored = next(
        item
        for item in stored_credentials
        if item["credential_id"] == old_credential.credential_id
    )

    new_stored = next(
        item
        for item in stored_credentials
        if item["credential_id"] == body["credential_id"]
    )

    assert old_stored["status"] == "active"

    assert new_stored["status"] == "pending"

    assert "secret" not in new_stored

    stored_router = fake_db.mikrotik_routers.documents[0]

    assert stored_router["wan_interface"] == "ether1"
    assert stored_router["lan_interfaces"] == [
        "ether2",
        "ether3",
    ]
    assert stored_router["bridge_name"] == "bridge-hotspot"


def test_rotate_mikrotik_control_credential_denies_other_owner(
    monkeypatch,
):
    fake_db = SimpleNamespace(
        hotspots=FakeCollection([
            {
                "id": "hotspot-owner-a",
                "owner_id": "owner-a",
            }
        ]),
        mikrotik_routers=FakeCollection([
            {
                "id": "router-owner-a",
                "name": "Protected Router",
                "hotspot_id": "hotspot-owner-a",
                "owner_id": "owner-a",
                "nas_identifier": "CAIWAVE-PROTECTED",
            }
        ]),
        mikrotik_router_control_credentials=FakeCollection(),
    )

    monkeypatch.setattr(server, "db", fake_db)

    repository = server.RouterControlCredentialRepository(
        fake_db.mikrotik_router_control_credentials
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    async def fake_current_user():
        return {
            "id": "owner-b",
            "role": server.UserRole.HOTSPOT_OWNER.value,
        }

    app.dependency_overrides[
        server.get_current_user
    ] = fake_current_user

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/routers/"
            "router-owner-a/rotate-control-credential"
        )

    assert response.status_code == 403

def test_mikrotik_control_credential_accepts_valid_secret(monkeypatch):
    secret = "test-control-secret-123"

    fake_credential = {
        "credential_id": "credential-test-1",
        "router_id": "router-test-1",
        "secret_hash": hash_control_secret(secret),
        "created_at": "2026-09-06T00:00:00+00:00",
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    fake_collection = FakeCollection([fake_credential])

    repository = server.RouterControlCredentialRepository(
        fake_collection
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        repository,
    )

    credentials = server.HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=secret,
    )

    result = asyncio.run(
        server.require_mikrotik_control_credential(credentials)
    )

    assert result["credential_id"] == "credential-test-1"
    assert result["router_id"] == "router-test-1"

def test_confirm_mikrotik_connection_creates_provisioning_job(monkeypatch):
    router_id = "router-confirm-test"
    nas_identifier = "CAIWAVE-CONFIRM-TEST"
    control_secret = "confirm-control-secret"

    router = {
        "id": router_id,
        "nas_identifier": nas_identifier,
        "hotspot_id": "hotspot-confirm-test",
        "owner_id": "owner-confirm-test",
    }

    credential = {
        "credential_id": "credential-confirm-test",
        "router_id": router_id,
        "secret_hash": hash_control_secret(control_secret),
        "created_at": "2026-09-08T00:00:00+00:00",
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    artifact = {
        "artifact_id": "artifact-confirm-test",
        "bundle_id": "bundle-confirm-test",
        "snapshot_id": "snapshot-confirm-test",
        "router_id": router_id,
        "checksum": "checksum-confirm-test",
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        nas_clients=FakeCollection(),
        hotspots=FakeCollection([
            {
                "id": "hotspot-confirm-test",
                "status": "inactive",
            }
        ]),
        mikrotik_router_control_credentials=FakeCollection([credential]),
        provisioning_artifacts=FakeCollection([artifact]),
        provisioning_jobs=FakeCollection(),
    )

    monkeypatch.setattr(server, "db", fake_db)

    control_credential_repository = (
        server.RouterControlCredentialRepository(
            fake_db.mikrotik_router_control_credentials
        )
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        control_credential_repository,
    )

    artifact_repository = (
        server.ProvisioningArtifactRepository(
            fake_db.provisioning_artifacts
        )
    )

    monkeypatch.setattr(
        server,
        "provisioning_artifact_repository",
        artifact_repository,
    )

    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        job_repository,
    )

    monkeypatch.setattr(
        server,
        "mikrotik_provisioning_orchestrator",
        server.MikroTikProvisioningOrchestrator(
            job_repository
        ),
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/confirm",
            json={
                "router_id": router_id,
                "nas_identifier": nas_identifier,
            },
            headers={
                "Authorization": f"Bearer {control_secret}",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["router_id"] == router_id
    assert body["status"] == "connected"

    assert len(fake_db.provisioning_jobs.documents) == 1

    second_response = client.post(
        "/api/mikrotik-onboard/confirm",
        json={
            "router_id": router_id,
            "nas_identifier": nas_identifier,
        },
        headers={
            "Authorization": f"Bearer {control_secret}",
        },
    )

    assert second_response.status_code == 200
    assert len(fake_db.provisioning_jobs.documents) == 1

    job = fake_db.provisioning_jobs.documents[0]

    job = fake_db.provisioning_jobs.documents[0]

    assert job["router_id"] == router_id
    assert job["artifact_id"] == "artifact-confirm-test"
    assert job["bundle_id"] == "bundle-confirm-test"
    assert job["snapshot_id"] == "snapshot-confirm-test"
    assert job["artifact_checksum"] == "checksum-confirm-test"
    assert job["status"] == "queued"

def test_confirm_promotes_pending_control_credential(monkeypatch):
    router_id = "router-confirm-pending"
    nas_identifier = "CAIWAVE-CONFIRM-PENDING"
    old_secret = "old-confirm-secret"
    new_secret = "new-confirm-secret"

    router = {
        "id": router_id,
        "nas_identifier": nas_identifier,
        "hotspot_id": "hotspot-confirm-pending",
        "owner_id": "owner-confirm-pending",
    }

    old_credential = {
        "credential_id": "credential-old-confirm-pending",
        "router_id": router_id,
        "secret_hash": hash_control_secret(old_secret),
        "created_at": "2026-09-01T00:00:00+00:00",
        "expires_at": "2099-10-01T00:00:00+00:00",
        "status": "active",
    }

    pending_credential = {
        "credential_id": "credential-new-confirm-pending",
        "router_id": router_id,
        "secret_hash": hash_control_secret(new_secret),
        "created_at": "2026-09-20T00:00:00+00:00",
        "expires_at": "2099-10-20T00:00:00+00:00",
        "status": "pending",
    }

    artifact = {
        "artifact_id": "artifact-confirm-pending",
        "bundle_id": "bundle-confirm-pending",
        "snapshot_id": "snapshot-confirm-pending",
        "router_id": router_id,
        "checksum": "checksum-confirm-pending",
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        nas_clients=FakeCollection(),
        hotspots=FakeCollection([
            {
                "id": "hotspot-confirm-pending",
                "status": "inactive",
            }
        ]),
        mikrotik_router_control_credentials=FakeCollection(
            [old_credential, pending_credential]
        ),
        provisioning_artifacts=FakeCollection([artifact]),
        provisioning_jobs=FakeCollection(),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        fake_db.mikrotik_router_control_credentials
    )
    artifact_repository = server.ProvisioningArtifactRepository(
        fake_db.provisioning_artifacts
    )
    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )
    monkeypatch.setattr(
        server,
        "provisioning_artifact_repository",
        artifact_repository,
    )

    class FakeOrchestrator:
        async def get_or_create_provisioning_job(
            self,
            router_id,
            artifact_id,
            bundle_id,
            snapshot_id,
            artifact_checksum,
        ):
            return {
                "job_id": "job-confirm-pending",
                "router_id": router_id,
                "artifact_id": artifact_id,
                "bundle_id": bundle_id,
                "snapshot_id": snapshot_id,
                "artifact_checksum": artifact_checksum,
                "status": "queued",
            }

    monkeypatch.setattr(
        server,
        "mikrotik_provisioning_orchestrator",
        FakeOrchestrator(),
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/confirm",
            json={
                "router_id": router_id,
                "nas_identifier": nas_identifier,
            },
            headers={
                "Authorization": f"Bearer {new_secret}",
            },
        )

    assert response.status_code == 200
    assert response.json()["success"] is True

    stored = fake_db.mikrotik_router_control_credentials.documents

    stored_old = next(
        item
        for item in stored
        if item["credential_id"] == old_credential["credential_id"]
    )
    stored_pending = next(
        item
        for item in stored
        if item["credential_id"] == pending_credential["credential_id"]
    )

    assert stored_old["status"] == "superseded"
    assert stored_old["superseded_by"] == pending_credential["credential_id"]

    assert stored_pending["status"] == "active"
    assert "activated_at" in stored_pending

def test_confirm_does_not_promote_pending_when_artifact_missing(monkeypatch):
    router_id = "router-confirm-no-artifact"
    nas_identifier = "CAIWAVE-CONFIRM-NO-ARTIFACT"
    old_secret = "old-no-artifact-secret"
    new_secret = "new-no-artifact-secret"

    router = {
        "id": router_id,
        "nas_identifier": nas_identifier,
        "hotspot_id": "hotspot-confirm-no-artifact",
        "owner_id": "owner-confirm-no-artifact",
    }

    old_credential = {
        "credential_id": "credential-old-no-artifact",
        "router_id": router_id,
        "secret_hash": hash_control_secret(old_secret),
        "created_at": "2026-09-01T00:00:00+00:00",
        "expires_at": "2099-10-01T00:00:00+00:00",
        "status": "active",
    }

    pending_credential = {
        "credential_id": "credential-new-no-artifact",
        "router_id": router_id,
        "secret_hash": hash_control_secret(new_secret),
        "created_at": "2026-09-20T00:00:00+00:00",
        "expires_at": "2099-10-20T00:00:00+00:00",
        "status": "pending",
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        nas_clients=FakeCollection(),
        hotspots=FakeCollection([
            {
                "id": "hotspot-confirm-no-artifact",
                "status": "inactive",
            }
        ]),
        mikrotik_router_control_credentials=FakeCollection(
            [old_credential, pending_credential]
        ),
        provisioning_artifacts=FakeCollection(),
        provisioning_jobs=FakeCollection(),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        fake_db.mikrotik_router_control_credentials
    )
    artifact_repository = server.ProvisioningArtifactRepository(
        fake_db.provisioning_artifacts
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )
    monkeypatch.setattr(
        server,
        "provisioning_artifact_repository",
        artifact_repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/confirm",
            json={
                "router_id": router_id,
                "nas_identifier": nas_identifier,
            },
            headers={
                "Authorization": f"Bearer {new_secret}",
            },
        )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Provisioning artifact not found for router"
    )

    stored = fake_db.mikrotik_router_control_credentials.documents

    stored_old = next(
        item
        for item in stored
        if item["credential_id"] == old_credential["credential_id"]
    )
    stored_pending = next(
        item
        for item in stored
        if item["credential_id"] == pending_credential["credential_id"]
    )

    assert stored_old["status"] == "active"
    assert stored_pending["status"] == "pending"

@pytest.mark.parametrize("artifact_tamper", ["none", "router", "checksum"])
def test_mikrotik_job_poll_claims_and_returns_artifact(artifact_tamper):
    import asyncio
    from datetime import datetime, timezone

    from backend.services.mikrotik_control_plane.credentials import (
        hash_control_secret,
    )

    async def run():
        from backend import server

        now = datetime.now(timezone.utc)

        router = {
            "id": "router-poll-1",
            "nas_identifier": "CAIWAVE-POLL-001",
            "hotspot_id": "hotspot-poll-1",
        }

        credential = {
            "credential_id": "credential-poll-1",
            "router_id": "router-poll-1",
            "secret_hash": hash_control_secret("poll-secret"),
            "expires_at": (now.replace(year=now.year + 1)).isoformat(),
            "status": "active",
        }

        artifact = {
            "artifact_id": "artifact-poll-1",
            "router_id": "router-poll-1",
            "bundle_id": "bundle-poll-1",
            "snapshot_id": "snapshot-poll-1",
            "filename": "router-poll-1-provisioning-v2.rsc",
            "content_type": "text/routeros-script",
            "checksum": hashlib.sha256(
                "/system identity set name=CAIWAVE".encode("utf-8")
            ).hexdigest(),
            "content": "/system identity set name=CAIWAVE",
        }

        if artifact_tamper == "router":
            artifact["router_id"] = "router-not-the-owner"
        elif artifact_tamper == "checksum":
            artifact["content"] += "\n# content changed after checksum"

        job = {
            "job_id": "job-poll-1",
            "router_id": "router-poll-1",
            "artifact_id": "artifact-poll-1",
            "bundle_id": "bundle-poll-1",
            "snapshot_id": "snapshot-poll-1",
            "artifact_checksum": artifact["checksum"],
            "status": "queued",
            "created_at": now,
        }

        class FakeDB:
            class Routers:
                async def find_one(self, query, projection=None):
                    if query.get("nas_identifier") == router["nas_identifier"]:
                        return router
                    return None

            mikrotik_routers = Routers()

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        class FakeJobRepository:
            def __init__(self):
                self.claimed = False
                self.current_job = None

            async def get_manual_verification_for_router(self, router_id):
                if (
                    self.current_job is not None
                    and self.current_job.get("router_id") == router_id
                    and self.current_job.get("requires_manual_verification") is True
                ):
                    return dict(self.current_job)
                return None

            async def get_active_for_router(self, router_id, job_type=None):
                current = self.current_job
                if (
                    current is None
                    or current.get("router_id") != router_id
                    or current.get("status") not in {"queued", "dispatched", "running"}
                ):
                    return None

                current_type = current.get("job_type")
                if (
                    job_type is None
                    or current_type == job_type
                    or (job_type == "provisioning" and "job_type" not in current)
                ):
                    return dict(current)
                return None

            async def claim_next_for_router(self, router_id, job_type=None):
                if self.claimed:
                    return None
                self.claimed = True
                self.current_job = dict(
                    job, status="dispatched", dispatched_at=now
                )
                return dict(self.current_job)

            async def update_if_status(self, job_id, expected_status, updates):
                if (
                    self.current_job is None
                    or self.current_job["job_id"] != job_id
                    or self.current_job["status"] != expected_status
                ):
                    return None
                self.current_job.update(updates)
                return dict(self.current_job)

            async def get_by_id(self, job_id):
                if (
                    self.current_job is not None
                    and self.current_job["job_id"] == job_id
                ):
                    return dict(self.current_job)
                return None

            async def update(self, job_id, updates):
                return dict(job, **updates)

        class FakeArtifactRepository:
            async def get_by_id(self, artifact_id):
                if artifact_id == artifact["artifact_id"]:
                    return artifact
                return None

        class FakeOrchestrator:
            pass

        original_db = server.db
        original_credentials = server.router_control_credential_repository
        original_jobs = server.provisioning_job_repository
        original_artifacts = server.provisioning_artifact_repository
        original_orchestrator = server.mikrotik_provisioning_orchestrator

        try:
            server.db = FakeDB()
            server.router_control_credential_repository = FakeCredentialRepository()
            fake_jobs = FakeJobRepository()
            server.provisioning_job_repository = fake_jobs
            server.provisioning_artifact_repository = FakeArtifactRepository()
            server.mikrotik_provisioning_orchestrator = FakeOrchestrator()

            app = FastAPI()
            app.include_router(server.mikrotik_onboard_router, prefix="/api")

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.post(
                    "/api/mikrotik-onboard/poll",
                    json={
                        "nas_identifier": router["nas_identifier"],
                    },
                    headers={
                        "Authorization": "Bearer poll-secret",
                    },
                )

                if artifact_tamper != "none":
                    assert response.status_code == 500, response.text
                    assert fake_jobs.current_job is not None
                    assert fake_jobs.current_job["status"] == "failed"
                    assert (
                        fake_jobs.current_job["last_error"]
                        == "Provisioning artifact integrity check failed"
                    )
                    return

                assert response.status_code == 200

                data = response.json()

                assert data["success"] is True
                assert data["router_id"] == router["id"]
                assert data["nas_identifier"] == router["nas_identifier"]
                assert data["job_available"] is True
                assert data["job"]["job_id"] == job["job_id"]
                assert data["job"]["status"] == "dispatched"
                assert data["artifact"]["artifact_id"] == artifact["artifact_id"]
                assert data["artifact"]["content"] == artifact["content"]

                response = client.post(
                    "/api/mikrotik-onboard/poll",
                    json={
                        "nas_identifier": router["nas_identifier"],
                    },
                    headers={
                        "Authorization": "Bearer poll-secret",
                    },
                )

                assert response.status_code == 200
                assert response.json()["job_available"] is False

        finally:
            server.db = original_db
            server.router_control_credential_repository = original_credentials
            server.provisioning_job_repository = original_jobs
            server.provisioning_artifact_repository = original_artifacts
            server.mikrotik_provisioning_orchestrator = original_orchestrator

    asyncio.run(run())

def test_mikrotik_artifact_download_returns_owned_artifact():
    import asyncio
    from datetime import datetime, timezone

    from backend.services.mikrotik_control_plane.credentials import (
        hash_control_secret,
    )

    async def run():
        from backend import server

        now = datetime.now(timezone.utc)

        router = {
            "id": "router-download-1",
            "nas_identifier": "CAIWAVE-DOWNLOAD-001",
        }

        credential = {
            "credential_id": "credential-download-1",
            "router_id": "router-download-1",
            "secret_hash": hash_control_secret("download-secret"),
            "expires_at": (now.replace(year=now.year + 1)).isoformat(),
            "status": "active",
        }

        artifact = {
            "artifact_id": "artifact-download-1",
            "router_id": "router-download-1",
            "filename": "router-download-1-provisioning-v2.rsc",
            "content_type": "text/routeros-script",
            "checksum": "checksum-download-1",
            "content": "/system identity set name=CAIWAVE-DOWNLOAD",
        }

        class FakeDB:
            class Routers:
                async def find_one(self, query, projection=None):
                    if query.get("id") == router["id"]:
                        return router
                    if query.get("nas_identifier") == router["nas_identifier"]:
                        return router
                    return None

            mikrotik_routers = Routers()

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        class FakeArtifactRepository:
            async def get_by_id(self, artifact_id):
                if artifact_id == artifact["artifact_id"]:
                    return artifact
                return None

        original_db = server.db
        original_credentials = server.router_control_credential_repository
        original_artifacts = server.provisioning_artifact_repository

        try:
            server.db = FakeDB()
            server.router_control_credential_repository = (
                FakeCredentialRepository()
            )
            server.provisioning_artifact_repository = (
                FakeArtifactRepository()
            )

            app = FastAPI()
            app.include_router(
                server.mikrotik_onboard_router,
                prefix="/api",
            )

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.get(
                    "/api/mikrotik-onboard/artifacts/"
                    "artifact-download-1/download",
                    headers={
                        "Authorization": "Bearer download-secret",
                    },
                )

                assert response.status_code == 200
                assert response.text == artifact["content"]
                assert (
                    response.headers["content-type"]
                    .startswith("text/routeros-script")
                )
                assert (
                    response.headers["content-disposition"]
                    == 'attachment; filename="router-download-1-provisioning-v2.rsc"'
                )
                assert (
                    response.headers["x-caiwave-artifact-id"]
                    == artifact["artifact_id"]
                )
                assert (
                    response.headers["x-caiwave-artifact-checksum"]
                    == artifact["checksum"]
                )

        finally:
            server.db = original_db
            server.router_control_credential_repository = original_credentials
            server.provisioning_artifact_repository = original_artifacts

    asyncio.run(run())

def test_mikrotik_artifact_download_rejects_different_router():
    import asyncio
    from datetime import datetime, timezone

    from backend.services.mikrotik_control_plane.credentials import (
        hash_control_secret,
    )

    async def run():
        from backend import server

        now = datetime.now(timezone.utc)

        credential = {
            "credential_id": "credential-owner-1",
            "router_id": "router-owner-1",
            "secret_hash": hash_control_secret("owner-secret"),
            "expires_at": (now.replace(year=now.year + 1)).isoformat(),
            "status": "active",
        }

        artifact = {
            "artifact_id": "artifact-other-router-1",
            "router_id": "router-owner-2",
            "filename": "other-router-provisioning.rsc",
            "content_type": "text/routeros-script",
            "checksum": "checksum-other-router-1",
            "content": "/system identity set name=OTHER",
        }

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        class FakeArtifactRepository:
            async def get_by_id(self, artifact_id):
                if artifact_id == artifact["artifact_id"]:
                    return artifact
                return None

        original_credentials = server.router_control_credential_repository
        original_artifacts = server.provisioning_artifact_repository

        try:
            server.router_control_credential_repository = (
                FakeCredentialRepository()
            )
            server.provisioning_artifact_repository = (
                FakeArtifactRepository()
            )

            app = FastAPI()
            app.include_router(
                server.mikrotik_onboard_router,
                prefix="/api",
            )

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.get(
                    "/api/mikrotik-onboard/artifacts/"
                    "artifact-other-router-1/download",
                    headers={
                        "Authorization": "Bearer owner-secret",
                    },
                )

                assert response.status_code == 401
                assert (
                    response.json()["detail"]
                    == "Provisioning artifact does not belong to this router"
                )

        finally:
            server.router_control_credential_repository = (
                original_credentials
            )
            server.provisioning_artifact_repository = original_artifacts

    asyncio.run(run())

def test_mikrotik_job_poll_rejects_invalid_control_credential():
    import asyncio
    from backend.services.mikrotik_control_plane.credentials import hash_control_secret

    async def run():
        from backend import server

        router = {
            "id": "router-poll-auth-1",
            "nas_identifier": "CAIWAVE-POLL-AUTH-001",
            "hotspot_id": "hotspot-poll-auth-1",
        }

        credential = {
            "credential_id": "credential-poll-auth-1",
            "router_id": router["id"],
            "secret_hash": hash_control_secret("correct-secret"),
            "expires_at": "2099-01-01T00:00:00+00:00",
            "status": "active",
        }

        class FakeDB:
            class Routers:
                async def find_one(self, query, projection=None):
                    if query.get("nas_identifier") == router["nas_identifier"]:
                        return router
                    return None

            mikrotik_routers = Routers()

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        original_db = server.db
        original_credentials = server.router_control_credential_repository

        try:
            server.db = FakeDB()
            server.router_control_credential_repository = FakeCredentialRepository()

            app = FastAPI()
            app.include_router(server.mikrotik_onboard_router, prefix="/api")

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.post(
                    "/api/mikrotik-onboard/poll",
                    json={
                        "nas_identifier": router["nas_identifier"],
                    },
                    headers={
                        "Authorization": "Bearer wrong-secret",
                    },
                )

                assert response.status_code == 401
                assert response.json()["detail"] == "Invalid MikroTik control credential"

        finally:
            server.db = original_db
            server.router_control_credential_repository = original_credentials

    asyncio.run(run())

def test_mikrotik_job_poll_rejects_credential_for_different_router():
    import asyncio
    from backend.services.mikrotik_control_plane.credentials import hash_control_secret

    async def run():
        from backend import server

        router = {
            "id": "router-poll-owner-1",
            "nas_identifier": "CAIWAVE-POLL-OWNER-001",
            "hotspot_id": "hotspot-poll-owner-1",
        }

        credential = {
            "credential_id": "credential-other-router-1",
            "router_id": "router-different-1",
            "secret_hash": hash_control_secret("valid-secret"),
            "expires_at": "2099-01-01T00:00:00+00:00",
            "status": "active",
        }

        class FakeDB:
            class Routers:
                async def find_one(self, query, projection=None):
                    if query.get("nas_identifier") == router["nas_identifier"]:
                        return router
                    return None

            mikrotik_routers = Routers()

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        original_db = server.db
        original_credentials = server.router_control_credential_repository

        try:
            server.db = FakeDB()
            server.router_control_credential_repository = FakeCredentialRepository()

            app = FastAPI()
            app.include_router(server.mikrotik_onboard_router, prefix="/api")

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.post(
                    "/api/mikrotik-onboard/poll",
                    json={
                        "nas_identifier": router["nas_identifier"],
                    },
                    headers={
                        "Authorization": "Bearer valid-secret",
                    },
                )

                assert response.status_code == 401
                assert response.json()["detail"] == "Invalid MikroTik control credential"

        finally:
            server.db = original_db
            server.router_control_credential_repository = original_credentials

    asyncio.run(run())

def test_mikrotik_job_poll_rejects_unknown_router():
    import asyncio
    from backend.services.mikrotik_control_plane.credentials import hash_control_secret

    async def run():
        from backend import server

        credential = {
            "credential_id": "credential-unknown-router-1",
            "router_id": "router-unknown-1",
            "secret_hash": hash_control_secret("valid-secret"),
            "expires_at": "2099-01-01T00:00:00+00:00",
            "status": "active",
        }

        class FakeDB:
            class Routers:
                async def find_one(self, query, projection=None):
                    return None

            mikrotik_routers = Routers()

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        original_db = server.db
        original_credentials = server.router_control_credential_repository

        try:
            server.db = FakeDB()
            server.router_control_credential_repository = FakeCredentialRepository()

            app = FastAPI()
            app.include_router(server.mikrotik_onboard_router, prefix="/api")

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.post(
                    "/api/mikrotik-onboard/poll",
                    json={
                        "nas_identifier": "CAIWAVE-NOT-REGISTERED",
                    },
                    headers={
                        "Authorization": "Bearer valid-secret",
                    },
                )

                assert response.status_code == 404
                assert response.json()["detail"] == "Router not registered"

        finally:
            server.db = original_db
            server.router_control_credential_repository = original_credentials

    asyncio.run(run())

def test_mikrotik_job_poll_fails_when_artifact_is_missing():
    import asyncio
    from datetime import datetime, timezone
    from backend.services.mikrotik_control_plane.credentials import hash_control_secret

    async def run():
        from backend import server

        now = datetime.now(timezone.utc)

        router = {
            "id": "router-poll-missing-artifact-1",
            "nas_identifier": "CAIWAVE-POLL-MISSING-001",
            "hotspot_id": "hotspot-poll-missing-1",
        }

        credential = {
            "credential_id": "credential-poll-missing-1",
            "router_id": router["id"],
            "secret_hash": hash_control_secret("missing-artifact-secret"),
            "expires_at": "2099-01-01T00:00:00+00:00",
            "status": "active",
        }

        job = {
            "job_id": "job-poll-missing-1",
            "router_id": router["id"],
            "artifact_id": "artifact-does-not-exist",
            "bundle_id": "bundle-poll-missing-1",
            "snapshot_id": "snapshot-poll-missing-1",
            "artifact_checksum": "checksum-missing-1",
            "status": "queued",
            "created_at": now,
        }

        class FakeDB:
            class Routers:
                async def find_one(self, query, projection=None):
                    if query.get("nas_identifier") == router["nas_identifier"]:
                        return router
                    return None

            mikrotik_routers = Routers()

        class FakeCredentialRepository:
            async def get_active_credentials(self):
                return [credential]

            async def get_active_and_pending_credentials(self):
                return [credential]

        class FakeJobRepository:
            async def get_manual_verification_for_router(self, router_id):
                return None

            async def get_active_for_router(self, router_id, job_type=None):
                return None

            async def claim_next_for_router(self, router_id, job_type=None):
                claimed = dict(job)
                claimed["status"] = "dispatched"
                return claimed

            async def update_if_status(
                self,
                job_id,
                expected_status,
                updates,
            ):
                assert job_id == job["job_id"]
                assert expected_status == "dispatched"
                assert updates["status"] == "failed"
                assert updates["last_error"] == "Provisioning artifact not found"
                result = dict(job)
                result["status"] = expected_status
                result.update(updates)
                return result

            async def update(self, job_id, updates):
                assert job_id == job["job_id"]
                assert updates["status"] == "failed"
                assert updates["last_error"] == "Provisioning artifact not found"
                return dict(job, **updates)

        class FakeArtifactRepository:
            async def get_by_id(self, artifact_id):
                return None

        original_db = server.db
        original_credentials = server.router_control_credential_repository
        original_jobs = server.provisioning_job_repository
        original_artifacts = server.provisioning_artifact_repository

        try:
            server.db = FakeDB()
            server.router_control_credential_repository = FakeCredentialRepository()
            server.provisioning_job_repository = FakeJobRepository()
            server.provisioning_artifact_repository = FakeArtifactRepository()

            app = FastAPI()
            app.include_router(server.mikrotik_onboard_router, prefix="/api")

            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.post(
                    "/api/mikrotik-onboard/poll",
                    json={
                        "nas_identifier": router["nas_identifier"],
                    },
                    headers={
                        "Authorization": "Bearer missing-artifact-secret",
                    },
                )

                assert response.status_code == 500
                assert response.json()["detail"] == "Provisioning artifact not found for claimed job"

        finally:
            server.db = original_db
            server.router_control_credential_repository = original_credentials
            server.provisioning_job_repository = original_jobs
            server.provisioning_artifact_repository = original_artifacts

    asyncio.run(run())

def test_mikrotik_job_result_marks_job_running(monkeypatch):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    router = {
        "id": "router-result-1",
        "nas_identifier": "CAIWAVE-RESULT-001",
    }

    secret = "result-secret"

    credential = {
        "credential_id": "credential-result-1",
        "router_id": router["id"],
        "secret_hash": hash_control_secret(secret),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    job = {
        "job_id": "job-result-1",
        "router_id": router["id"],
        "artifact_id": "artifact-result-1",
        "bundle_id": "bundle-result-1",
        "snapshot_id": "snapshot-result-1",
        "artifact_checksum": "checksum-result-1",
        "status": "dispatched",
        "attempts": 0,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "last_error": None,
        "result": None,
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        provisioning_jobs=FakeCollection([job]),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        FakeCollection([credential])
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )

    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        job_repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "running",
            },
            headers={
                "Authorization": f"Bearer {secret}",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["router_id"] == router["id"]
    assert body["nas_identifier"] == router["nas_identifier"]
    assert body["job_id"] == job["job_id"]
    assert body["status"] == "running"

    stored_job = fake_db.provisioning_jobs.documents[0]

    assert stored_job["status"] == "running"
    assert stored_job["attempts"] == 1
    assert stored_job["started_at"] is not None
    assert stored_job["completed_at"] is None

def test_mikrotik_job_result_marks_job_succeeded(monkeypatch):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    router = {
        "id": "router-result-success-1",
        "nas_identifier": "CAIWAVE-RESULT-SUCCESS-001",
    }

    secret = "result-success-secret"

    credential = {
        "credential_id": "credential-result-success-1",
        "router_id": router["id"],
        "secret_hash": hash_control_secret(secret),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    job = {
        "job_id": "job-result-success-1",
        "router_id": router["id"],
        "artifact_id": "artifact-result-success-1",
        "bundle_id": "bundle-result-success-1",
        "snapshot_id": "snapshot-result-success-1",
        "artifact_checksum": "checksum-result-success-1",
        "status": "dispatched",
        "attempts": 0,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "last_error": None,
        "result": None,
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        provisioning_jobs=FakeCollection([job]),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        FakeCollection([credential])
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )

    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        job_repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        running_response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "running",
            },
            headers={
                "Authorization": f"Bearer {secret}",
            },
        )

        assert running_response.status_code == 200

        success_response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "succeeded",
                "result": {
                    "router_status": "provisioned",
                    "message": "Provisioning completed successfully",
                },
            },
            headers={
                "Authorization": f"Bearer {secret}",
            },
        )
        late_failure_response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "failed",
                "error": "Late stale failure callback",
                "result": {"router_status": "failed"},
            },
            headers={"Authorization": f"Bearer {secret}"},
        )

        assert late_failure_response.status_code == 409


    assert success_response.status_code == 200

    body = success_response.json()

    assert body["success"] is True
    assert body["router_id"] == router["id"]
    assert body["nas_identifier"] == router["nas_identifier"]
    assert body["job_id"] == job["job_id"]
    assert body["status"] == "succeeded"

    stored_job = fake_db.provisioning_jobs.documents[0]

    assert stored_job["status"] == "succeeded"
    assert stored_job["attempts"] == 1
    assert stored_job["started_at"] is not None
    assert stored_job["completed_at"] is not None
    assert stored_job["result"] == {
        "router_status": "provisioned",
        "message": "Provisioning completed successfully",
    }

def test_mikrotik_job_result_marks_job_failed(monkeypatch):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    router = {
        "id": "router-result-failed-1",
        "nas_identifier": "CAIWAVE-RESULT-FAILED-001",
    }

    secret = "result-failed-secret"

    credential = {
        "credential_id": "credential-result-failed-1",
        "router_id": router["id"],
        "secret_hash": hash_control_secret(secret),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    job = {
        "job_id": "job-result-failed-1",
        "router_id": router["id"],
        "artifact_id": "artifact-result-failed-1",
        "bundle_id": "bundle-result-failed-1",
        "snapshot_id": "snapshot-result-failed-1",
        "artifact_checksum": "checksum-result-failed-1",
        "status": "dispatched",
        "attempts": 0,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "last_error": None,
        "result": None,
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        provisioning_jobs=FakeCollection([job]),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        FakeCollection([credential])
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )

    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        job_repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "failed",
                "error": "RouterOS import failed",
                "result": {
                    "router_status": "provisioning_failed",
                },
            },
            headers={
                "Authorization": f"Bearer {secret}",
            },
        )
        late_success_response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "succeeded",
                "result": {"router_status": "incorrect_late_success"},
            },
            headers={"Authorization": f"Bearer {secret}"},
        )

        assert late_success_response.status_code == 409


    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["router_id"] == router["id"]
    assert body["nas_identifier"] == router["nas_identifier"]
    assert body["job_id"] == job["job_id"]
    assert body["status"] == "failed"

    stored_job = fake_db.provisioning_jobs.documents[0]

    assert stored_job["status"] == "failed"
    assert stored_job["completed_at"] is not None
    assert stored_job["last_error"] == "RouterOS import failed"
    assert stored_job["result"] == {
        "router_status": "provisioning_failed",
    }

def test_mikrotik_job_result_rejects_invalid_control_credential(monkeypatch):
    router = {
        "id": "router-result-auth-1",
        "nas_identifier": "CAIWAVE-RESULT-AUTH-001",
    }

    credential = {
        "credential_id": "credential-result-auth-1",
        "router_id": router["id"],
        "secret_hash": hash_control_secret("correct-result-secret"),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    job = {
        "job_id": "job-result-auth-1",
        "router_id": router["id"],
        "artifact_id": "artifact-result-auth-1",
        "bundle_id": "bundle-result-auth-1",
        "snapshot_id": "snapshot-result-auth-1",
        "artifact_checksum": "checksum-result-auth-1",
        "status": "dispatched",
        "attempts": 0,
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        provisioning_jobs=FakeCollection([job]),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        FakeCollection([credential])
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )

    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        job_repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "succeeded",
            },
            headers={
                "Authorization": "Bearer wrong-result-secret",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid MikroTik control credential"

def test_mikrotik_job_result_rejects_job_from_different_router(monkeypatch):
    router = {
        "id": "router-result-owner-1",
        "nas_identifier": "CAIWAVE-RESULT-OWNER-001",
    }

    secret = "owner-result-secret"

    credential = {
        "credential_id": "credential-result-owner-1",
        "router_id": router["id"],
        "secret_hash": hash_control_secret(secret),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }

    job = {
        "job_id": "job-result-other-router-1",
        "router_id": "router-result-other-1",
        "artifact_id": "artifact-result-other-1",
        "bundle_id": "bundle-result-other-1",
        "snapshot_id": "snapshot-result-other-1",
        "artifact_checksum": "checksum-result-other-1",
        "status": "dispatched",
        "attempts": 0,
    }

    fake_db = SimpleNamespace(
        mikrotik_routers=FakeCollection([router]),
        provisioning_jobs=FakeCollection([job]),
    )

    monkeypatch.setattr(server, "db", fake_db)

    credential_repository = server.RouterControlCredentialRepository(
        FakeCollection([credential])
    )

    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        credential_repository,
    )

    job_repository = server.ProvisioningJobRepository(
        fake_db.provisioning_jobs
    )

    monkeypatch.setattr(
        server,
        "provisioning_job_repository",
        job_repository,
    )

    app = FastAPI()
    app.include_router(
        server.mikrotik_onboard_router,
        prefix="/api",
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/job-result",
            json={
                "nas_identifier": router["nas_identifier"],
                "job_id": job["job_id"],
                "status": "succeeded",
            },
            headers={
                "Authorization": f"Bearer {secret}",
            },
        )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Provisioning job does not belong to this router"
    )

    stored_job = fake_db.provisioning_jobs.documents[0]

    assert stored_job["status"] == "dispatched"

def test_confirm_and_heartbeat_reject_missing_authentication():
    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    with TestClient(app) as client:
        confirm_response = client.post(
            "/api/mikrotik-onboard/confirm",
            json={
                "router_id": "router-auth-required",
                "nas_identifier": "CAIWAVE-AUTH-REQUIRED",
            },
        )
        heartbeat_response = client.post(
            "/api/mikrotik-onboard/heartbeat",
            json={"nas_identifier": "CAIWAVE-AUTH-REQUIRED"},
        )

    assert confirm_response.status_code == 401
    assert heartbeat_response.status_code in {401, 403}


def test_confirm_rejects_control_credential_for_different_router(monkeypatch):
    router = {
        "id": "router-confirm-bound",
        "nas_identifier": "CAIWAVE-CONFIRM-BOUND",
        "status": "pending_discovery",
        "connection_confirmed": False,
    }
    secret = "valid-secret-for-another-router"
    credential = {
        "credential_id": "credential-other-router",
        "router_id": "router-not-confirm-bound",
        "secret_hash": hash_control_secret(secret),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }
    fake_routers = FakeCollection([router])
    fake_credentials = FakeCollection([credential])
    fake_db = SimpleNamespace(mikrotik_routers=fake_routers)

    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        server.RouterControlCredentialRepository(fake_credentials),
    )

    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/confirm",
            json={
                "router_id": router["id"],
                "nas_identifier": router["nas_identifier"],
            },
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid MikroTik control credential"
    assert fake_routers.documents[0]["status"] == "pending_discovery"
    assert fake_routers.documents[0]["connection_confirmed"] is False


def test_heartbeat_rejects_control_credential_for_different_router(monkeypatch):
    router = {
        "id": "router-heartbeat-bound",
        "nas_identifier": "CAIWAVE-HEARTBEAT-BOUND",
        "status": "pending_discovery",
        "connection_confirmed": False,
    }
    secret = "valid-secret-for-a-different-heartbeat-router"
    credential = {
        "credential_id": "credential-heartbeat-other-router",
        "router_id": "router-not-heartbeat-bound",
        "secret_hash": hash_control_secret(secret),
        "expires_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }
    fake_routers = FakeCollection([router])
    fake_credentials = FakeCollection([credential])
    fake_db = SimpleNamespace(mikrotik_routers=fake_routers)

    monkeypatch.setattr(server, "db", fake_db)
    monkeypatch.setattr(
        server,
        "router_control_credential_repository",
        server.RouterControlCredentialRepository(fake_credentials),
    )

    app = FastAPI()
    app.include_router(server.mikrotik_onboard_router, prefix="/api")

    with TestClient(app) as client:
        response = client.post(
            "/api/mikrotik-onboard/heartbeat",
            json={"nas_identifier": router["nas_identifier"]},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid MikroTik control credential"
    assert fake_routers.documents[0]["status"] == "pending_discovery"
    assert fake_routers.documents[0]["connection_confirmed"] is False
