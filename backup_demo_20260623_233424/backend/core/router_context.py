from pydantic import BaseModel, Field
from typing import List


class RouterContext(BaseModel):
    """
    Single source of truth for ALL router provisioning data.
    """

    name: str

    # 🔒 Canonical identity field (NO ALIASES ALLOWED)
    nas_identifier: str = Field(min_length=3)

    radius_secret: str
    radius_host: str = "radius.caiwave.com"

    wan_interface: str = "ether1"
    lan_interfaces: List[str] = ["ether2"]

    bridge_name: str = "bridge-hotspot"

    hotspot_cidr: str = "10.10.0.0/24"
    hotspot_gateway: str = "10.10.0.1"
    dhcp_pool: str = "10.10.0.10-10.10.0.254"

    dns_name: str = "wifi.caiwave.com"
