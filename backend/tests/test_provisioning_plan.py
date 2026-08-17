import pytest

from backend.services.provisioning_v2.provisioning_intent import (
    ProvisioningIntent,
)
from backend.services.provisioning_v2.provisioning_plan import (
    ProvisioningPlanError,
    build_provisioning_plan,
)
from backend.services.provisioning_v2.router_capabilities import (
    RouterCapabilityFacts,
)


def rb951_capabilities():
    return RouterCapabilityFacts(
        router_id="router-rb951",
        board_name="RB951Ui-2HnD",
        routeros_version="7.22",
        architecture="mipsbe",
        interface_count=8,
        ethernet_interfaces=[
            "ether1",
            "ether2",
            "ether3",
            "ether4",
            "ether5",
        ],
        wireless_interfaces=["wlan1"],
        bridge_count=1,
        vlan_count=0,
        route_count=3,
        dhcp_server_count=1,
        hotspot_count=1,
        supports_wireless=True,
    )


def rb750_capabilities():
    return RouterCapabilityFacts(
        router_id="router-rb750",
        board_name="RB750",
        routeros_version="7.21.4",
        architecture="mipsbe",
        interface_count=7,
        ethernet_interfaces=[
            "ether1",
            "ether2",
            "ether3",
            "ether4",
            "ether5",
        ],
        wireless_interfaces=[],
        bridge_count=1,
        vlan_count=0,
        route_count=3,
        dhcp_server_count=1,
        hotspot_count=1,
        supports_wireless=False,
    )


def test_rb951_plan_includes_wireless_and_wired_interfaces():
    plan = build_provisioning_plan(
        capabilities=rb951_capabilities(),
        intent=ProvisioningIntent(
            hotspot_enabled=True,
            wifi_enabled=True,
            wifi_ssid="CAIWAVE",
            wired_enabled=True,
            client_isolation=True,
        ),
        requested_wan_interface="ether1",
    )

    assert plan.wan_interface == "ether1"
    assert plan.client_interfaces == [
        "ether2",
        "ether3",
        "ether4",
        "ether5",
        "wlan1",
    ]
    assert plan.wifi_interfaces == ["wlan1"]
    assert plan.wifi_enabled is True
    assert plan.hotspot_enabled is True
    assert plan.client_isolation is True


def test_rb750_rejects_requested_wifi():
    with pytest.raises(
        ProvisioningPlanError,
        match="does not support wireless",
    ):
        build_provisioning_plan(
            capabilities=rb750_capabilities(),
            intent=ProvisioningIntent(
                hotspot_enabled=True,
                wifi_enabled=True,
                wifi_ssid="CAIWAVE",
                wired_enabled=True,
            ),
            requested_wan_interface="ether1",
        )


def test_rb750_can_plan_wired_hotspot_without_wifi():
    plan = build_provisioning_plan(
        capabilities=rb750_capabilities(),
        intent=ProvisioningIntent(
            hotspot_enabled=True,
            wifi_enabled=False,
            wired_enabled=True,
            client_isolation=True,
        ),
        requested_wan_interface="ether1",
    )

    assert plan.wan_interface == "ether1"
    assert plan.client_interfaces == [
        "ether2",
        "ether3",
        "ether4",
        "ether5",
    ]
    assert plan.wifi_interfaces == []
    assert plan.wifi_enabled is False


def test_requested_wired_interface_must_exist():
    with pytest.raises(
        ProvisioningPlanError,
        match="were not discovered",
    ):
        build_provisioning_plan(
            capabilities=rb951_capabilities(),
            intent=ProvisioningIntent(
                hotspot_enabled=True,
                wifi_enabled=False,
                wired_enabled=True,
            ),
            requested_wan_interface="ether1",
            requested_wired_interfaces=["ether9"],
        )


def test_wireless_only_intent_is_supported():
    plan = build_provisioning_plan(
        capabilities=rb951_capabilities(),
        intent=ProvisioningIntent(
            hotspot_enabled=False,
            wifi_enabled=True,
            wifi_ssid="CAIWAVE",
            wired_enabled=False,
        ),
        requested_wan_interface="ether1",
    )

    assert plan.wan_interface == "ether1"
    assert plan.client_interfaces == ["wlan1"]
    assert plan.wifi_interfaces == ["wlan1"]
    assert plan.hotspot_enabled is False
    assert plan.wired_enabled is False
