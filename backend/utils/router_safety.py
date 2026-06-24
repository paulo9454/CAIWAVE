def safe_router_get(router: dict, key: str, default=None):
    """
    Safe access layer for MikroTik router objects.
    Prevents KeyError crashes and normalizes missing fields.
    """
    if not isinstance(router, dict):
        return default

    value = router.get(key, default)

    # Normalize empty values
    if value in ("", [], None):
        return default

    return value


def require_router_fields(router: dict, fields: list):
    """
    Validate required router fields exist.
    Used only for provisioning-critical paths.
    """
    missing = [f for f in fields if safe_router_get(router, f) is None]
    if missing:
        raise ValueError(f"Missing required router fields: {missing}")

    return True

def normalize_router(router: dict) -> dict:
    """
    Normalize router object so downstream code NEVER crashes.
    Converts missing fields into safe defaults.
    """

    if not isinstance(router, dict):
        return {}

    return {
        "id": router.get("id"),
        "name": router.get("name", "unnamed-router"),
        "nas_identifier": router.get("nas_identifier", ""),
        "radius_secret": router.get("radius_secret", ""),
        "owner_id": router.get("owner_id"),
        "hotspot_id": router.get("hotspot_id"),

        # Network config defaults
        "wan_interface": router.get("wan_interface", "ether1"),
        "lan_interfaces": router.get("lan_interfaces", []),
        "bridge_name": router.get("bridge_name", "bridge-hotspot"),
        "effective_lan_interface": router.get("effective_lan_interface", "bridge-hotspot"),

        # Hotspot network defaults
        "hotspot_cidr": router.get("hotspot_cidr", "10.10.0.0/24"),
        "dhcp_pool": router.get("dhcp_pool", "10.10.0.10-10.10.0.254"),
        "dns_name": router.get("dns_name", "wifi.caiwave.com"),
        "hotspot_gateway": router.get("hotspot_gateway", "10.10.0.1"),
        "hotspot_network": router.get("hotspot_network", "10.10.0.0/24"),

        # Status fields
        "status": router.get("status", "unknown"),
        "health_status": router.get("health_status", "unknown"),
        "last_seen": router.get("last_seen"),
    }
