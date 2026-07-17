from backend.services.provisioning_v2.production_input import (
    build_persisted_production_router_record,
    validate_production_router_input,
)


def incomplete_router_record():
    return {
        "id": "router-production-1",
        "name": "Production Router",
        "owner_id": "owner-production-1",
        "hotspot_id": "hotspot-production-1",
        "nas_identifier": "CAIWAVE-PRODUCTION-12345678",
        "radius_secret": "router-specific-production-secret",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "ether3", "ether4", "ether5"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "hotspot_cidr": "10.10.0.1/24",
        "hotspot_network": "10.10.0.0/24",
        "hotspot_gateway": "10.10.0.1",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "login.caiwave.local",
    }


def test_builds_complete_persisted_production_router_record():
    record = build_persisted_production_router_record(
        incomplete_router_record(),
        radius_host="34.134.75.132",
        portal_public_url="https://www.caiwave.com",
        api_public_url="https://www.caiwave.com/api",
        heartbeat_url=(
            "https://www.caiwave.com/"
            "api/mikrotik-onboard/heartbeat"
        ),
    )

    validated = validate_production_router_input(record)

    assert record["hotspot_cidr"] == "10.10.0.0/24"
    assert record["radius_host"] == "34.134.75.132"
    assert record["portal_public_url"] == "https://www.caiwave.com"
    assert record["api_public_url"] == "https://www.caiwave.com/api"
    assert record["heartbeat_url"].endswith(
        "/api/mikrotik-onboard/heartbeat"
    )

    assert validated.router_id == "router-production-1"
    assert validated.hotspot_cidr == "10.10.0.0/24"


def test_snapshot_does_not_replace_router_specific_radius_secret():
    original = incomplete_router_record()

    record = build_persisted_production_router_record(
        original,
        radius_host="34.134.75.132",
        portal_public_url="https://www.caiwave.com",
        api_public_url="https://www.caiwave.com/api",
        heartbeat_url=(
            "https://www.caiwave.com/"
            "api/mikrotik-onboard/heartbeat"
        ),
    )

    assert record["radius_secret"] == original["radius_secret"]
