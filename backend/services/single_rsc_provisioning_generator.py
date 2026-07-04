"""
CAIWAVE Single RSC Provisioning Generator

Pure helpers for producing a one-time MikroTik .rsc onboarding script.
This module intentionally does not import the FastAPI app, database, auth,
billing, marketplace, or router modules so importing it cannot change existing
runtime behavior.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class SingleRscProvisioningInput:
    router_name: str
    nas_identifier: str
    radius_secret: str
    radius_host: str
    hotspot_id: str = ""
    callback_url: str = ""
    generated_at: Optional[datetime] = None


@dataclass(frozen=True)
class SingleRscProvisioningOutput:
    filename: str
    content: str
    content_type: str = "text/plain"


def _format_generated_at(generated_at: Optional[datetime]) -> str:
    if generated_at is None:
        generated_at = datetime.now(timezone.utc)
    return generated_at.isoformat()


def _safe_filename(value: str) -> str:
    safe = "".join(c.lower() if c.isalnum() else "-" for c in value).strip("-")
    return safe or "caiwave-router"


def build_single_rsc_provisioning_script(config: SingleRscProvisioningInput) -> str:
    generated_at = _format_generated_at(config.generated_at)

    radius_host = config.radius_host
    radius_secret = config.radius_secret
    router_name = config.router_name
    nas_identifier = config.nas_identifier
    hotspot_id = config.hotspot_id
    callback_url = config.callback_url or "https://caiwave.com/api/mikrotik-onboard/confirm"
    heartbeat_url = callback_url.replace("/confirm", "/heartbeat")
    portal_url = f"https://caiwave.com/portal/{hotspot_id}"
    login_html = (
        '<html><head><meta http-equiv="refresh" content="0; url='
        + portal_url
        + '?mac=$(mac)&ip=$(ip)&dst=$(link-orig)">'
        + '<title>CAIWAVE WiFi</title></head>'
        + '<body style="font-family:Arial;text-align:center;padding:40px;">'
        + '<h2>Redirecting to CAIWAVE...</h2>'
        + '<p><a href="'
        + portal_url
        + '?mac=$(mac)&ip=$(ip)&dst=$(link-orig)">Continue to WiFi Portal</a></p>'
        + '</body></html>'
    )
    login_html = login_html.replace("\\", "\\\\").replace('"', '\\"')

    return f"""# =========================================================
# CAIWAVE MikroTik Auto-Configuration Script
# Router: {router_name}
# NAS Identifier: {nas_identifier}
# Generated: {generated_at}
# =========================================================

:log info "CAIWAVE: Starting auto-configuration..."

# SYSTEM IDENTITY
/system identity set name="{router_name}"

# NTP
/system ntp client set enabled=yes servers=time.google.com

# BRIDGE
:if ([:len [/interface bridge find name=bridge-hotspot]] = 0) do={{
    /interface bridge add name=bridge-hotspot comment="CAIWAVE Hotspot Bridge"
}}

# ADD LAN PORTS TO BRIDGE, KEEP ether1 AS WAN
:foreach i in=[/interface ethernet find] do={{
    :local ethName [/interface ethernet get $i name]
    :if ($ethName != "ether1") do={{
        :if ([:len [/interface bridge port find interface=$ethName]] = 0) do={{
            /interface bridge port add bridge=bridge-hotspot interface=$ethName comment="CAIWAVE"
        }}
    }}
}}

# IP CONFIG
:if ([:len [/ip address find interface=bridge-hotspot address="10.10.0.1/24"]] = 0) do={{
    /ip address add address=10.10.0.1/24 interface=bridge-hotspot comment="CAIWAVE Hotspot Gateway"
}}

# DHCP POOL
:if ([:len [/ip pool find name=pool-hotspot]] = 0) do={{
    /ip pool add name=pool-hotspot ranges=10.10.0.10-10.10.0.254
}}

# DHCP SERVER
:if ([:len [/ip dhcp-server find name=dhcp-hotspot]] = 0) do={{
    /ip dhcp-server add name=dhcp-hotspot interface=bridge-hotspot address-pool=pool-hotspot disabled=no
}}

:if ([:len [/ip dhcp-server network find address=10.10.0.0/24]] = 0) do={{
    /ip dhcp-server network add address=10.10.0.0/24 gateway=10.10.0.1 dns-server=8.8.8.8,1.1.1.1 comment="CAIWAVE Hotspot Network"
}}

# DNS
/ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1

# NAT
:if ([:len [/ip firewall nat find comment="CAIWAVE NAT"]] = 0) do={{
    /ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade comment="CAIWAVE NAT"
}}

# RADIUS
:foreach r in=[/radius find comment~"CAIWAVE"] do={{
    /radius remove $r
}}
/radius add address={radius_host} secret="{radius_secret}" service=hotspot comment="CAIWAVE" timeout=3s

# HOTSPOT PROFILE
:if ([:len [/ip hotspot profile find name=caiwave-profile]] = 0) do={{
    /ip hotspot profile add name=caiwave-profile hotspot-address=10.10.0.1 dns-name=login.caiwave.local use-radius=yes radius-accounting=yes login-by=http-chap,http-pap
}} else={{
    /ip hotspot profile set caiwave-profile use-radius=yes radius-accounting=yes login-by=http-chap,http-pap
}}

# HOTSPOT SERVER
:if ([:len [/ip hotspot find name=caiwave-hotspot]] = 0) do={{
    /ip hotspot add name=caiwave-hotspot interface=bridge-hotspot profile=caiwave-profile address-pool=pool-hotspot disabled=no
}} else={{
    /ip hotspot set caiwave-hotspot profile=caiwave-profile disabled=no
}}

# WALLED GARDEN
:if ([:len [/ip hotspot walled-garden find comment="CAIWAVE Portal"]] = 0) do={{
    /ip hotspot walled-garden add dst-host=caiwave.com action=allow comment="CAIWAVE Portal"
    /ip hotspot walled-garden add dst-host=www.caiwave.com action=allow comment="CAIWAVE Portal"
    /ip hotspot walled-garden add dst-host=*.caiwave.com action=allow comment="CAIWAVE Portal"
    /ip hotspot walled-garden add dst-host=*.paystack.com action=allow comment="CAIWAVE Paystack"
}}

# CONFIRM CALLBACK
/tool fetch url="{callback_url}" http-method=post http-header-field="Content-Type: application/json" http-data="{{\\"router_id\\":\\"\\",\\"nas_identifier\\":\\"{nas_identifier}\\"}}" keep-result=no

# HEARTBEAT SCRIPT
/system script remove [find name="caiwave-heartbeat"]
/system script add name="caiwave-heartbeat" policy=read,write,test source="/tool fetch url=\\"{heartbeat_url}\\" http-method=post http-header-field=\\"Content-Type: application/json\\" http-data=\\"{{\\\\\\"nas_identifier\\\\\\":\\\\\\"{nas_identifier}\\\\\\"}}\\" keep-result=no"

# HEARTBEAT SCHEDULER
/system scheduler remove [find name="caiwave-heartbeat"]
/system scheduler add name="caiwave-heartbeat" interval=2m on-event=caiwave-heartbeat disabled=no

/system script run caiwave-heartbeat

:log info "CAIWAVE provisioning complete"
:put "CAIWAVE provisioning complete"
:put "NAS Identifier: {nas_identifier}"
"""


def generate_single_rsc_provisioning_script(
    router_name: str,
    nas_identifier: str,
    radius_secret: str,
    radius_host: str,
    hotspot_id: str = "",
    callback_url: str = "",
    generated_at: Optional[datetime] = None,
) -> str:
    return build_single_rsc_provisioning_script(
        SingleRscProvisioningInput(
            router_name=router_name,
            nas_identifier=nas_identifier,
            radius_secret=radius_secret,
            radius_host=radius_host,
            hotspot_id=hotspot_id,
            callback_url=callback_url,
            generated_at=generated_at,
        )
    )


def build_single_rsc_provisioning_file(
    config: SingleRscProvisioningInput,
) -> SingleRscProvisioningOutput:
    return SingleRscProvisioningOutput(
        filename=f"{_safe_filename(config.router_name)}-{_safe_filename(config.nas_identifier)}.rsc",
        content=build_single_rsc_provisioning_script(config),
    )


def generate_single_rsc_provisioning_file(
    router_name: str,
    nas_identifier: str,
    radius_secret: str,
    radius_host: str,
    hotspot_id: str = "",
    callback_url: str = "",
    generated_at: Optional[datetime] = None,
) -> SingleRscProvisioningOutput:
    return build_single_rsc_provisioning_file(
        SingleRscProvisioningInput(
            router_name=router_name,
            nas_identifier=nas_identifier,
            radius_secret=radius_secret,
            radius_host=radius_host,
            hotspot_id=hotspot_id,
            callback_url=callback_url,
            generated_at=generated_at,
        )
    )


generate_single_rsc_script = generate_single_rsc_provisioning_script
generate_single_rsc_file = generate_single_rsc_provisioning_file


__all__ = [
    "SingleRscProvisioningInput",
    "SingleRscProvisioningOutput",
    "build_single_rsc_provisioning_script",
    "build_single_rsc_provisioning_file",
    "generate_single_rsc_provisioning_script",
    "generate_single_rsc_provisioning_file",
    "generate_single_rsc_script",
    "generate_single_rsc_file",
]