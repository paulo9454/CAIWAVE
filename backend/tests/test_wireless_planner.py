import pytest

from backend.services.provisioning_v2.router_capabilities import (
    RouterCapabilityFacts,
)
from backend.services.provisioning_v2.wireless_planner import (
    WirelessMode,
    WirelessPlannerError,
    plan_wireless,
)


def test_wireless_interfaces_are_planned_as_access_points():
    capabilities = RouterCapabilityFacts(
        router_id="router-1",
        board_name="hAP",
        routeros_version="7.18",
        architecture="arm",
        interface_count=2,
        ethernet_interfaces=["ether1"],
        wireless_interfaces=["wlan1"],
        supports_wireless=True,
    )

    plan = plan_wireless(
        capabilities=capabilities,
        ssid="MAIN_caiwave",
    )

    assert len(plan.radios) == 1
    assert plan.radios[0].interface == "wlan1"
    assert plan.radios[0].mode == WirelessMode.AP
    assert plan.radios[0].ssid == "MAIN_caiwave"
    assert plan.radios[0].enabled is True
    assert plan.warnings == []


def test_router_without_wireless_returns_warning():
    capabilities = RouterCapabilityFacts(
        router_id="router-2",
        board_name="hEX",
        routeros_version="7.18",
        architecture="arm",
        interface_count=2,
        ethernet_interfaces=["ether1", "ether2"],
        wireless_interfaces=[],
        supports_wireless=False,
    )

    plan = plan_wireless(
        capabilities=capabilities,
        ssid="MAIN_caiwave",
    )

    assert plan.radios == []
    assert "no discovered wireless interfaces" in plan.warnings[0].lower()


def test_blank_ssid_is_rejected():
    capabilities = RouterCapabilityFacts(
        router_id="router-3",
        board_name="hAP",
        routeros_version="7.18",
        architecture="arm",
        wireless_interfaces=["wlan1"],
        supports_wireless=True,
    )

    with pytest.raises(WirelessPlannerError):
        plan_wireless(
            capabilities=capabilities,
            ssid="   ",
        )


def test_ssid_longer_than_32_characters_is_rejected():
    capabilities = RouterCapabilityFacts(
        router_id="router-4",
        board_name="hAP",
        routeros_version="7.18",
        architecture="arm",
        wireless_interfaces=["wlan1"],
        supports_wireless=True,
    )

    with pytest.raises(WirelessPlannerError):
        plan_wireless(
            capabilities=capabilities,
            ssid="A" * 33,
        )


def test_inconsistent_wireless_capability_is_rejected():
    capabilities = RouterCapabilityFacts(
        router_id="router-5",
        board_name="hAP",
        routeros_version="7.18",
        architecture="arm",
        wireless_interfaces=[],
        supports_wireless=True,
    )

    with pytest.raises(WirelessPlannerError):
        plan_wireless(
            capabilities=capabilities,
            ssid="MAIN_caiwave",
        )
