"""
CAIWAVE MikroTik RSC Generator V2 (Safe Parallel Version)
DO NOT USE IN PRODUCTION YET — FOR TESTING ONLY
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List


@dataclass(frozen=True)
class SingleRscProvisioningInput:
    router_name: str
    nas_identifier: str
    radius_secret: str
    radius_host: str
    wan_interface: str
    lan_interfaces: List[str]
    bridge_name: str
    hotspot_cidr: str
    hotspot_gateway: str
    dhcp_pool: str
    dns_name: str
    generated_at: Optional[datetime] = None


@dataclass(frozen=True)
class SingleRscProvisioningOutput:
    filename: str
    content: str
    content_type: str = "text/plain"


def _now(dt: Optional[datetime]) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.isoformat()


def _safe(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")


def _dhcp_net(pool: str) -> str:
    base = pool.split("-")[0].rsplit(".", 1)[0]
    return f"{base}.0/24"


def build_single_rsc_provisioning_script(cfg: SingleRscProvisioningInput) -> str:
    lan_ports = "\n".join(
        f'/interface bridge port add bridge="{cfg.bridge_name}" interface="{p}"'
        for p in cfg.lan_interfaces
    )

    return f"""# =====================================================
# CAIWAVE V2 PROVISIONING
# Router: {cfg.router_name}
# NAS: {cfg.nas_identifier}
# Generated: {_now(cfg.generated_at)}
# =====================================================

:log info "CAIWAVE V2 starting"

# SYSTEM IDENTITY
/system identity set name="{cfg.router_name}"

# BRIDGE
/interface bridge add name="{cfg.bridge_name}"

{lan_ports}

# IP ADDRESS
/ip address add address={cfg.hotspot_gateway}/24 interface="{cfg.bridge_name}"

# DHCP
/ip pool add name=pool-hotspot ranges={cfg.dhcp_pool}
/ip dhcp-server add name=dhcp-hotspot interface="{cfg.bridge_name}" address-pool=pool-hotspot
/ip dhcp-server network add address={_dhcp_net(cfg.dhcp_pool)} gateway={cfg.hotspot_gateway} dns-server={cfg.dns_name}

# NAT
/ip firewall nat add chain=srcnat action=masquerade out-interface={cfg.wan_interface}

# DNS
/ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1

# RADIUS
/radius add address={cfg.radius_host} secret="{cfg.radius_secret}" service=hotspot

# HOTSPOT
/ip hotspot profile add name=caiwave dns-name={cfg.dns_name} hotspot-address={cfg.hotspot_gateway}
/ip hotspot add name=hotspot interface="{cfg.bridge_name}" address-pool=pool-hotspot

:log info "CAIWAVE V2 complete"
"""


def generate_single_rsc_provisioning_file(
    router_name: str,
    nas_identifier: str,
    radius_secret: str,
    radius_host: str,
    wan_interface: str,
    lan_interfaces: list,
    bridge_name: str,
    hotspot_cidr: str,
    hotspot_gateway: str,
    dhcp_pool: str,
    dns_name: str,
    generated_at: Optional[datetime] = None,
):

    cfg = SingleRscProvisioningInput(
        router_name=router_name,
        nas_identifier=nas_identifier,
        radius_secret=radius_secret,
        radius_host=radius_host,
        wan_interface=wan_interface,
        lan_interfaces=lan_interfaces,
        bridge_name=bridge_name,
        hotspot_cidr=hotspot_cidr,
        hotspot_gateway=hotspot_gateway,
        dhcp_pool=dhcp_pool,
        dns_name=dns_name,
        generated_at=generated_at,
    )

    return SingleRscProvisioningOutput(
        filename=f"{_safe(router_name)}-{_safe(nas_identifier)}.rsc",
        content=build_single_rsc_provisioning_script(cfg),
    )
