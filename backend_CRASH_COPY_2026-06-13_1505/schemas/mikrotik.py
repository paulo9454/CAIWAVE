from pydantic import BaseModel, Field
from typing import List, Optional


class MikroTikProvisionRequest(BaseModel):
    name: str = Field(default="Auto-Router", min_length=2)

    nas_identifier: Optional[str] = None

    radius_secret: Optional[str] = None
    radius_host: str = "radius.caiwave.com"

    wan_interface: str = "ether1"
    lan_interfaces: List[str] = Field(default_factory=lambda: ["ether2"])

    bridge_name: str = "bridge-hotspot"

    hotspot_cidr: str = "10.10.0.0/24"
    hotspot_gateway: str = "10.10.0.1"
    dhcp_pool: str = "10.10.0.10-10.10.0.254"

    dns_name: str = "wifi.caiwave.com"
