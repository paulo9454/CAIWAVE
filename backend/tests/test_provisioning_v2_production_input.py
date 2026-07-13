import pytest

from backend.services.provisioning_v2.production_input import (
    ProductionProvisioningInputError,
    validate_production_router_input,
)


def valid_router(**overrides):
    data = {
        "id": "5531447b-7613-4452-92c5-1ca0c94f2dfb",
        "name": "qqqqqqqq",
        "owner_id": "4369263d-3dd3-4f80-b151-e7a499eb2897",
        "hotspot_id": "373bdbc6-88e9-47a6-9d8e-5ef9d0e6aaaf",
        "nas_identifier": "CAIWAVE-QQQQQQQQ-3384C0CE",
        "wan_interface": "ether1",
        "lan_interfaces": ["ether2", "ether3"],
        "create_bridge": True,
        "bridge_name": "bridge-hotspot",
        "hotspot_cidr": "10.10.0.0/24",
        "hotspot_gateway": "10.10.0.1",
        "dhcp_pool": "10.10.0.10-10.10.0.254",
        "dns_name": "login.caiwave.local",
        "radius_host": "34.134.75.132",
        "radius_secret": "real-router-specific-secret",
        "portal_public_url": "https://www.caiwave.com",
        "api_public_url": "https://www.caiwave.com/api",
        "heartbeat_url": (
            "https://www.caiwave.com/api/mikrotik-onboard/heartbeat"
        ),
    }
    data.update(overrides)
    return data


def test_accepts_complete_production_router_input():
    result = validate_production_router_input(valid_router())

    assert result.router_name == "qqqqqqqq"
    assert result.captive_dns_name == "login.caiwave.local"
    assert result.radius_host == "34.134.75.132"
    assert result.lan_interfaces == ("ether2", "ether3")


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "name",
        "owner_id",
        "hotspot_id",
        "nas_identifier",
        "wan_interface",
        "bridge_name",
        "hotspot_cidr",
        "hotspot_gateway",
        "dhcp_pool",
        "dns_name",
        "radius_host",
        "radius_secret",
        "portal_public_url",
        "api_public_url",
        "heartbeat_url",
    ],
)
def test_rejects_missing_required_fields(field):
    router = valid_router()
    router.pop(field)

    with pytest.raises(
        ProductionProvisioningInputError,
        match=field,
    ):
        validate_production_router_input(router)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "router-1"),
        ("owner_id", "owner-1"),
        ("hotspot_id", "hotspot-1"),
        ("dns_name", "wifi.caiwave.com"),
        ("radius_secret", "testing123"),
        ("radius_secret", "router-radius-secret:router-1"),
    ],
)
def test_rejects_development_placeholders(field, value):
    with pytest.raises(ProductionProvisioningInputError):
        validate_production_router_input(
            valid_router(**{field: value})
        )


def test_rejects_empty_lan_interfaces():
    with pytest.raises(
        ProductionProvisioningInputError,
        match="lan_interfaces",
    ):
        validate_production_router_input(
            valid_router(lan_interfaces=[])
        )


def test_rejects_duplicate_lan_interfaces():
    with pytest.raises(
        ProductionProvisioningInputError,
        match="duplicates",
    ):
        validate_production_router_input(
            valid_router(
                lan_interfaces=["ether2", "ether2"]
            )
        )


def test_rejects_wan_interface_in_lan_interfaces():
    with pytest.raises(
        ProductionProvisioningInputError,
        match="WAN interface",
    ):
        validate_production_router_input(
            valid_router(
                wan_interface="ether1",
                lan_interfaces=["ether1", "ether2"],
            )
        )


def test_rejects_gateway_outside_hotspot_network():
    with pytest.raises(
        ProductionProvisioningInputError,
        match="belong",
    ):
        validate_production_router_input(
            valid_router(
                hotspot_cidr="10.10.0.0/24",
                hotspot_gateway="10.20.0.1",
            )
        )


@pytest.mark.parametrize(
    "field",
    [
        "portal_public_url",
        "api_public_url",
        "heartbeat_url",
    ],
)
def test_public_urls_require_https(field):
    router = valid_router()
    router[field] = router[field].replace(
        "https://",
        "http://",
    )

    with pytest.raises(
        ProductionProvisioningInputError,
        match="HTTPS",
    ):
        validate_production_router_input(router)
