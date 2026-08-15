import pytest

from backend.services.provisioning_v2.router_discovery import (
    RouterDiscoveryError,
)
from backend.services.provisioning_v2.router_discovery_ingest import (
    RouterDiscoveryIngestionError,
    build_discovery_snapshot_from_payload,
)

def _payload():
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
                "name": "wlan1",
                "type": "wireless",
                "running": True,
            },
        ],
        "bridges": [
            {
                "name": "bridge-hotspot",
                "running": True,
            }
        ],
        "vlans": [],
        "addresses": [
            {
                "interface": "ether1",
                "address": "192.168.1.2/24",
            }
        ],
        "routes": [
            {
                "dst-address": "0.0.0.0/0",
                "gateway": "192.168.1.1",
            }
        ],
        "packages": [],
        "wireless_interfaces": [],
    }


def test_raw_discovery_payload_becomes_snapshot():
    snapshot = build_discovery_snapshot_from_payload(_payload())

    assert snapshot.router_id == "CAIWAVE-TEST"
    assert snapshot.board_name == "hAP-test"
    assert snapshot.routeros_version == "7.18"
    assert snapshot.architecture == "arm"
    assert [item.name for item in snapshot.interfaces] == [
        "ether1",
        "wlan1",
    ]
    assert snapshot.interfaces[1].type == "wireless"
    assert snapshot.routes[0].gateway == "192.168.1.1"


def test_missing_router_metadata_is_rejected():
    payload = _payload()
    del payload["router"]["routeros_version"]

    with pytest.raises(RouterDiscoveryIngestionError):
        build_discovery_snapshot_from_payload(payload)


def test_duplicate_interfaces_are_rejected():
    payload = _payload()
    payload["interfaces"].append(
        {
            "name": "ether1",
            "type": "ethernet",
        }
    )

    with pytest.raises(RouterDiscoveryError):
        build_discovery_snapshot_from_payload(payload)

def test_internal_router_id_can_override_nas_identifier():
    snapshot = build_discovery_snapshot_from_payload(
        _payload(),
        router_id="mongo-router-123",
    )

    assert snapshot.router_id == "mongo-router-123"
