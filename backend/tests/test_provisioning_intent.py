import pytest
from pydantic import ValidationError

from backend.services.provisioning_v2.provisioning_intent import (
    ProvisioningIntent,
    build_default_provisioning_intent,
)


def test_default_provisioning_intent_preserves_current_hotspot_behavior():
    intent = build_default_provisioning_intent()

    assert intent.hotspot_enabled is True
    assert intent.wifi_enabled is False
    assert intent.wired_enabled is True
    assert intent.client_isolation is True
    assert intent.poe_enabled is False


def test_wifi_intent_accepts_valid_ssid():
    intent = ProvisioningIntent(
        hotspot_enabled=True,
        wifi_enabled=True,
        wifi_ssid="CAIWAVE",
        wired_enabled=True,
        client_isolation=True,
    )

    assert intent.wifi_enabled is True
    assert intent.wifi_ssid == "CAIWAVE"


def test_wifi_intent_rejects_blank_ssid():
    with pytest.raises(
        ValidationError,
        match="wifi_ssid is required",
    ):
        ProvisioningIntent(
            hotspot_enabled=True,
            wifi_enabled=True,
            wifi_ssid="   ",
            wired_enabled=True,
        )


def test_wifi_intent_rejects_oversized_ssid():
    with pytest.raises(
        ValidationError,
        match="wifi_ssid must not exceed 32 characters",
    ):
        ProvisioningIntent(
            hotspot_enabled=True,
            wifi_enabled=True,
            wifi_ssid="A" * 33,
            wired_enabled=True,
        )


def test_intent_requires_at_least_one_client_service():
    with pytest.raises(
        ValidationError,
        match="At least one client service must be enabled",
    ):
        ProvisioningIntent(
            hotspot_enabled=False,
            wifi_enabled=False,
            wired_enabled=False,
        )


def test_wifi_can_be_enabled_without_hotspot():
    intent = ProvisioningIntent(
        hotspot_enabled=False,
        wifi_enabled=True,
        wifi_ssid="CAIWAVE",
        wired_enabled=False,
    )

    assert intent.wifi_enabled is True
    assert intent.hotspot_enabled is False
    assert intent.wired_enabled is False
