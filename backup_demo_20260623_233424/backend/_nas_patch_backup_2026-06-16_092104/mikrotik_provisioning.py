from schemas.mikrotik import MikroTikProvisionRequest
import secrets
import ipaddress


# =========================================================
# NORMALIZATION
# =========================================================
def normalize_request(req: MikroTikProvisionRequest) -> dict:
    data = req.model_dump()
    if not data.get("radius_secret"):
        data["radius_secret"] = secrets.token_hex(12)
    # Ensure NAS identifier exists
    if not data.get("nas_id"):
        clean = "".join(c for c in data["name"] if c.isalnum())[:10].upper()
        data["nas_id"] = f"CAIWAVE-{clean}-{secrets.token_hex(4).upper()}"

    # Clean LAN interfaces
    data["lan_interfaces"] = [
        i.strip() for i in data.get("lan_interfaces", []) if i and i.strip()
    ]

    return data


# =========================================================
# VALIDATION LAYER (PRODUCTION CRITICAL)
# =========================================================
def validate_request(data: dict) -> None:
    # LAN check
    if not data["lan_interfaces"]:
        raise ValueError("At least one LAN interface is required")

    # CIDR validation
    try:
        network = ipaddress.ip_network(data["hotspot_cidr"], strict=False)
    except Exception:
        raise ValueError("Invalid hotspot CIDR")

    # Gateway must be inside subnet
    gateway_ip = ipaddress.ip_address(data["hotspot_gateway"])
    if gateway_ip not in network:
        raise ValueError("Gateway is not inside hotspot CIDR")

    # DHCP pool sanity check (basic guard)
    try:
        start, end = data["dhcp_pool"].split("-")
        ipaddress.ip_address(start.strip())
        ipaddress.ip_address(end.strip())
    except Exception:
        raise ValueError("Invalid DHCP pool format")


# =========================================================
# BUILD CONTEXT (FOR SCRIPT ENGINE)
# =========================================================
def build_context(req: MikroTikProvisionRequest) -> dict:
    data = normalize_request(req)
    validate_request(data)

    return {
        "name": data["name"],
        "nas_id": data["nas_id"],
        "radius_secret": data["radius_secret"],
        "radius_host": data["radius_host"],
        "wan_interface": data["wan_interface"],
        "lan_interfaces": data["lan_interfaces"],
        "bridge_name": data["bridge_name"],
        "hotspot_cidr": data["hotspot_cidr"],
        "hotspot_gateway": data["hotspot_gateway"],
        "dhcp_pool": data["dhcp_pool"],
        "dns_name": data["dns_name"],
    }


# =========================================================
# PUBLIC ENTRY POINT (USED BY ROUTE)
# =========================================================
def provision_router(req: MikroTikProvisionRequest) -> dict:
    try:
        context = build_context(req)

        return {
            "status": "success",
            "router": context
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
