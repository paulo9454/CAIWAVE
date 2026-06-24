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
    /interface bridge add name=bridge-hotspot
}}

# IP CONFIG
/ip address add address=10.10.0.1/24 interface=bridge-hotspot

# DHCP POOL
/ip pool add name=pool-hotspot ranges=10.10.0.10-10.10.0.254

# DHCP SERVER
/ip dhcp-server add name=dhcp-hotspot interface=bridge-hotspot address-pool=pool-hotspot disabled=no

# DNS
/ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1

# RADIUS
/radius add address={radius_host} secret="{radius_secret}" service=hotspot comment="CAIWAVE"

# HOTSPOT PROFILE
/ip hotspot profile add name=caiwave-profile hotspot-address=10.10.0.1 dns-name=caiwave.local use-radius=yes

# HOTSPOT SERVER
/ip hotspot add name=caiwave-hotspot interface=bridge-hotspot profile=caiwave-profile address-pool=pool-hotspot

:log info "CAIWAVE provisioning complete"
"""

def generate_single_rsc_provisioning_script(
    router_name: str,
    nas_identifier: str,
    radius_secret: str,
    radius_host: str,
    callback_url: str = "",
    generated_at: Optional[datetime] = None,
) -> str:
    return build_single_rsc_provisioning_script(
        SingleRscProvisioningInput(
            router_name=router_name,
            nas_identifier=nas_identifier,
            radius_secret=radius_secret,
            radius_host=radius_host,
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
    callback_url: str = "",
    generated_at: Optional[datetime] = None,
) -> SingleRscProvisioningOutput:
    return build_single_rsc_provisioning_file(
        SingleRscProvisioningInput(
            router_name=router_name,
            nas_identifier=nas_identifier,
            radius_secret=radius_secret,
            radius_host=radius_host,
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