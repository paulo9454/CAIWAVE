from backend.services.provisioning_v2.routeros_wireless_renderer import (
    render_wireless_section,
)
from backend.services.provisioning_v2.wireless_planner import (
    WirelessMode,
    WirelessPlan,
    WirelessRadioPlan,
)


def test_legacy_wireless_ap_renderer():
    plan = WirelessPlan(
        radios=[
            WirelessRadioPlan(
                interface="wlan1",
                mode=WirelessMode.AP,
                ssid="MAIN_caiwave",
                enabled=True,
            )
        ]
    )

    section = render_wireless_section(plan)

    assert section.status.value == "rendered"
    assert "/interface wireless" in section.content
    assert 'mode="ap-bridge"' in section.content
    assert 'ssid="MAIN_caiwave"' in section.content
    assert "wlan1" in section.content


def test_empty_wireless_plan_is_planned_with_warning():
    plan = WirelessPlan(
        radios=[],
        warnings=["Router has no discovered wireless interfaces"],
    )

    section = render_wireless_section(plan)

    assert section.status.value == "planned"
    assert section.warnings == [
        "Router has no discovered wireless interfaces"
    ]
