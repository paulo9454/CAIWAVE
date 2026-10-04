"""
CAIWAVE MikroTik Router Engine.

Compatibility facade for existing callers.

All RouterOS provisioning generation is delegated to
Provisioning Engine v2.
"""

from __future__ import annotations

from backend.services.provisioning_v2.mikrotik_builder_adapter import (
    build_provisioning_v2_rsc_from_router,
)


class MikroTikLegacyEngine:
    """
    Compatibility facade for legacy callers.

    Generation is handled exclusively by Provisioning Engine v2.
    """

    @staticmethod
    def generate(router: dict):
        result = build_provisioning_v2_rsc_from_router(router)

        return {
            "script": result.content,
            "mode": "legacy",
            "single_rsc_provisioning": result,
        }


class MikroTikV1Engine:
    """
    Compatibility facade for V1 callers.

    Generation is handled exclusively by Provisioning Engine v2.
    """

    @staticmethod
    def validate(router: dict):
        required_fields = [
            "wan_interface",
            "lan_interfaces",
            "hotspot_cidr",
            "dhcp_pool",
            "dns_name",
            "effective_lan_interface",
            "bridge_name",
            "create_bridge",
            "mode",
        ]

        missing = [f for f in required_fields if not router.get(f)]

        if missing:
            raise ValueError(f"Missing fields: {missing}")

        return True

    @staticmethod
    def normalize(router: dict):
        return {
            "name": router["name"],
            "nas_identifier": router["nas_identifier"],
            "radius_secret": router["radius_secret"],
            "wan_interface": router["wan_interface"],
            "lan_interfaces": router["lan_interfaces"],
            "create_bridge": router["create_bridge"],
            "bridge_name": router.get("bridge_name"),
            "effective_lan_interface": router["effective_lan_interface"],
            "hotspot_cidr": router["hotspot_cidr"],
            "dhcp_pool": router["dhcp_pool"],
            "dns_name": router["dns_name"],
            "mode": router["mode"],
            "hotspot_gateway": router.get("hotspot_gateway"),
            "hotspot_network": router.get("hotspot_network"),
        }

    @staticmethod
    def generate(router: dict):
        MikroTikV1Engine.validate(router)

        normalized = MikroTikV1Engine.normalize(router)

        result = build_provisioning_v2_rsc_from_router(router)

        return {
            "script": result.content,
            "mode": "v1",
            "normalized_router": normalized,
            "single_rsc_provisioning": result,
        }


class MikroTikRouterEngine:
    """
    Public compatibility entry point.

    Existing callers may continue using:
        MikroTikRouterEngine.generate(router)

    Provisioning Engine v2 remains the only RouterOS generator.
    """

    @staticmethod
    def generate(router: dict):
        version = router.get("provisioning_version", 1)

        if version == 0:
            return MikroTikLegacyEngine.generate(router)

        return MikroTikV1Engine.generate(router)
