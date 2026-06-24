from services.single_rsc_provisioning_generator import generate_single_rsc_provisioning_file
import os


class MikroTikLegacyEngine:
    @staticmethod
    def generate(router: dict):
        single_rsc = generate_single_rsc_provisioning_file(
            router_name=router["name"],
            nas_id=router["nas_identifier"],
            radius_secret=router["radius_secret"],
            radius_host=os.environ.get("RADIUS_HOST", "radius.caiwave.com"),
            callback_url=os.environ.get("MPESA_CALLBACK_URL", "").replace(
                "/mpesa/callback", "/mikrotik-onboard/confirm"
            )
        )

        return {
            "script": single_rsc.content,
            "mode": "legacy",
            "single_rsc_provisioning": single_rsc
        }


class MikroTikV1Engine:
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
            "mode"
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
            "hotspot_network": router.get("hotspot_network")
        }

    @staticmethod
    def generate(router: dict):
        MikroTikV1Engine.validate(router)
        normalized = MikroTikV1Engine.normalize(router)

        single_rsc = generate_single_rsc_provisioning_file(
            router_name=normalized["name"],
            nas_id=normalized["nas_identifier"],
            radius_secret=normalized["radius_secret"],
            radius_host=os.environ.get("RADIUS_HOST", "radius.caiwave.com"),
            callback_url=""
        )

        return {
            "script": single_rsc.content,
            "mode": "v1",
            "normalized_router": normalized
        }


class MikroTikRouterEngine:
    @staticmethod
    def generate(router: dict):
        version = router.get("provisioning_version", 1)

        if version == 0:
            return MikroTikLegacyEngine.generate(router)

        return MikroTikV1Engine.generate(router)
