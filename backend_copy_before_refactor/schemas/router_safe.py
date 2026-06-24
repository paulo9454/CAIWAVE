from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class RouterSafe(BaseModel):
    id: str
    name: str

    # Identity layer
    nas_identifier: str
    radius_secret: str

    # Network config
    hotspot_cidr: Optional[str] = None
    dhcp_pool: Optional[str] = None
    dns_name: Optional[str] = None
    mode: Optional[str] = "hotspot"

    hotspot_gateway: Optional[str] = None
    hotspot_network: Optional[str] = None

    # Status layer
    status: Optional[str] = "unknown"
    health_status: Optional[str] = "unknown"
    last_seen: Optional[str] = None

    # Provisioning
    provisioning_version: int = 1
    provisioning_source: Optional[str] = None

    # Extra flexible fields (prevents breakage)
    extra: Dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def from_db(router: dict) -> "RouterSafe":
        """
        Normalize DB router into safe structure
        """
        base_fields = {
            "id": router.get("id"),
            "name": router.get("name", "unknown"),

            "nas_identifier": router.get("nas_identifier", ""),
            "radius_secret": router.get("radius_secret", ""),

            "hotspot_cidr": router.get("hotspot_cidr"),
            "dhcp_pool": router.get("dhcp_pool"),
            "dns_name": router.get("dns_name"),
            "mode": router.get("mode", "hotspot"),

            "hotspot_gateway": router.get("hotspot_gateway"),
            "hotspot_network": router.get("hotspot_network"),

            "status": router.get("status", "unknown"),
            "health_status": router.get("health_status", "unknown"),
            "last_seen": router.get("last_seen"),

            "provisioning_version": router.get("provisioning_version", 1),
            "provisioning_source": router.get("provisioning_source"),
        }

        known_keys = set(base_fields.keys())

        extra = {
            k: v for k, v in router.items()
            if k not in known_keys and k != "_id"
        }

        base_fields["extra"] = extra

        return RouterSafe(**base_fields)
