"""
Provisioning Intent for CAIWAVE Provisioning Engine v2.

Safety:
- no database access
- no RouterOS generation
- no provisioning mutation

ProvisioningIntent represents what the owner/operator wants CAIWAVE to
configure. It does not describe router hardware and does not contain
RouterOS syntax.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProvisioningIntentError(ValueError):
    """Raised when a provisioning intent is invalid."""


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class ProvisioningIntent(StrictModel):
    hotspot_enabled: bool = True

    wifi_enabled: bool = False
    wifi_ssid: str = "CAIWAVE"

    wired_enabled: bool = True

    client_isolation: bool = True

    # Reserved for the next capability phase.
    poe_enabled: bool = False

    @model_validator(mode="after")
    def validate_intent(self) -> "ProvisioningIntent":
        if self.wifi_enabled:
            ssid = self.wifi_ssid.strip()

            if not ssid:
                raise ProvisioningIntentError(
                    "wifi_ssid is required when Wi-Fi is enabled"
                )

            if len(ssid) > 32:
                raise ProvisioningIntentError(
                    "wifi_ssid must not exceed 32 characters"
                )

        if (
            not self.hotspot_enabled
            and not self.wifi_enabled
            and not self.wired_enabled
        ):
            raise ProvisioningIntentError(
                "At least one client service must be enabled"
            )

        return self


def build_default_provisioning_intent() -> ProvisioningIntent:
    """
    Return the current CAIWAVE default service intent.

    Keeps the existing HotSpot-oriented behavior while making the decision
    explicit and typed.
    """
    return ProvisioningIntent(
        hotspot_enabled=True,
        wifi_enabled=False,
        wifi_ssid="CAIWAVE",
        wired_enabled=True,
        client_isolation=True,
        poe_enabled=False,
    )
