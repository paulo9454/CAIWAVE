from pydantic import BaseModel, Field
from typing import List, Optional


class RouterSchema(BaseModel):
    # Identity
    id: Optional[str]
    name: str = Field(..., min_length=3)
    nas_identifier: str = Field(..., min_length=3)
    radius_secret: str = Field(..., min_length=6)

    owner_id: Optional[str]
    hotspot_id: Optional[str]

    # Interfaces
    wan_interface: str = "ether1"
    lan_interfaces: List[str] = []

    bridge_name: str = "bridge-hotspot"
    effective_lan_interface: Optional[str] = None

    # Network config
    hotspot_cidr: str = "10.10.0.0/24"
    dhcp_pool: str = "10.10.0.10-10.10.0.254"
    dns_name: str = "wifi.caiwave.com"
    hotspot_gateway: str = "10.10.0.1"
    hotspot_network: str = "10.10.0.0/24"

    # Status
    status: Optional[str] = "unknown"
    health_status: Optional[str] = "unknown"
    last_seen: Optional[str] = None
