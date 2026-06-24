from backend.services.single_rsc_provisioning_generator import generate_single_rsc_provisioning_file as v1
from backend.services.single_rsc_provisioning_generator_v2 import generate_single_rsc_provisioning_file as v2
import os


def build_mikrotik_script(router: dict):
    """
    CAIWAVE SAFE MIGRATION BUILDER

    - Uses V2 if enabled
    - Falls back to V1 if anything fails
    """

    use_v2 = os.getenv("CAIWAVE_MIKROTIK_V2", "false").lower() == "true"

    try:
        if use_v2:
            single_rsc = v2(
                router_name=router.get("name", "unknown"),
                nas_identifier=router.get("nas_identifier", ""),
                radius_secret=router.get("radius_secret", ""),
                radius_host=router.get(
                    "radius_host",
                    os.environ.get("RADIUS_HOST", "radius.caiwave.com")
                ),
                wan_interface=router.get("wan_interface", "ether1"),
                lan_interfaces=router.get("lan_interfaces", ["ether2"]),
                bridge_name=router.get("bridge_name", "bridge-hotspot"),
                hotspot_cidr=router.get("hotspot_cidr", "10.10.0.0/24"),
                hotspot_gateway=router.get("hotspot_gateway", "10.10.0.1"),
                dhcp_pool=router.get("dhcp_pool", "10.10.0.10-10.10.0.254"),
                dns_name=router.get("dns_name", "wifi.caiwave.com"),
            )
        else:
            single_rsc = v1(
                router_name=router.get("name", "unknown"),
                nas_identifier=router.get("nas_identifier", ""),
                radius_secret=router.get("radius_secret", ""),
                radius_host=router.get(
                    "radius_host",
                    os.environ.get("RADIUS_HOST", "radius.caiwave.com")
                )
            )

        return single_rsc.content

    except Exception as e:
        # HARD FALLBACK (never break provisioning)
        try:
            single_rsc = v1(
                router_name=router.get("name", "unknown"),
                nas_identifier=router.get("nas_identifier", ""),
                radius_secret=router.get("radius_secret", ""),
                radius_host=router.get(
                    "radius_host",
                    os.environ.get("RADIUS_HOST", "radius.caiwave.com")
                )
            )
            return single_rsc.content + f"\n# FALLBACK USED: {str(e)}\n"
        except Exception as e2:
            return f"# CRITICAL PROVISIONING FAILURE\n# {str(e2)}\n"
