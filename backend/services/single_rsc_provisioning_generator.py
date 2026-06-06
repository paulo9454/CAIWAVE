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
    """Inputs required to generate a CAIWAVE MikroTik provisioning .rsc file."""
    router_name: str
    nas_id: str
    radius_secret: str
    radius_host: str
    callback_url: str = ""
    generated_at: Optional[datetime] = None


@dataclass(frozen=True)
class SingleRscProvisioningOutput:
    """Generated .rsc file metadata and content."""
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
    """
    Build the same RouterOS provisioning commands used by the existing
    generate_mikrotik_script flow, returned as a single .rsc-compatible string.
    """
    generated_at = _format_generated_at(config.generated_at)

    return f'''# =========================================================
# CAIWAVE MikroTik Auto-Configuration Script
# Router: {config.router_name}
# NAS Identifier: {config.nas_id}
# Generated: {generated_at}
# =========================================================

# IMPORTANT: Run this script in MikroTik Terminal after:
# 1. System Reset (optional but recommended for fresh install)
# 2. DHCP Client configured on ether1 for internet

:log info "CAIWAVE: Starting auto-configuration..."

# =========================================================
# 1. BASIC SYSTEM CONFIGURATION
# =========================================================
/system identity set name="{config.router_name}"
:log info "CAIWAVE: System identity set to {config.router_name}"

# Set system clock (NTP)
/system ntp client set enabled=yes servers=time.google.com

# =========================================================
# 2. BRIDGE CONFIGURATION
# =========================================================
# Create bridge for hotspot if not exists
:if ([:len [/interface bridge find name=bridge-hotspot]] = 0) do={{
    /interface bridge add name=bridge-hotspot comment="CAIWAVE Hotspot Bridge"
    :log info "CAIWAVE: Created bridge-hotspot"
}}

# Add all ethernet ports to bridge EXCEPT ether1 (WAN)
:foreach i in=[/interface ethernet find] do={{
    :local ethName [/interface ethernet get $i name]
    :if ($ethName != "ether1") do={{
        :if ([:len [/interface bridge port find interface=$ethName]] = 0) do={{
            /interface bridge port add bridge=bridge-hotspot interface=$ethName comment="CAIWAVE"
            :log info ("CAIWAVE: Added " . $ethName . " to bridge-hotspot")
        }}
    }}
}}

# =========================================================
# 3. IP CONFIGURATION FOR HOTSPOT
# =========================================================
:if ([:len [/ip address find interface=bridge-hotspot]] = 0) do={{
    /ip address add address=10.10.0.1/24 interface=bridge-hotspot comment="CAIWAVE Hotspot Network"
    :log info "CAIWAVE: Added IP 10.10.0.1/24 to bridge-hotspot"
}}

# DHCP Pool for hotspot clients
:if ([:len [/ip pool find name=pool-hotspot]] = 0) do={{
    /ip pool add name=pool-hotspot ranges=10.10.0.10-10.10.0.254
    :log info "CAIWAVE: Created DHCP pool for hotspot"
}}

# DHCP Server for hotspot
:if ([:len [/ip dhcp-server find name=dhcp-hotspot]] = 0) do={{
    /ip dhcp-server add name=dhcp-hotspot interface=bridge-hotspot address-pool=pool-hotspot disabled=no
    /ip dhcp-server network add address=10.10.0.0/24 gateway=10.10.0.1 dns-server=8.8.8.8,8.8.4.4 comment="CAIWAVE Hotspot Network"
    :log info "CAIWAVE: Configured DHCP server for hotspot"
}}

# =========================================================
# 4. DNS CONFIGURATION
# =========================================================
/ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4,1.1.1.1
:log info "CAIWAVE: DNS configured"

# =========================================================
# 5. RADIUS CONFIGURATION
# =========================================================
# Remove existing CAIWAVE RADIUS config if any
:foreach r in=[/radius find comment~"CAIWAVE"] do={{
    /radius remove $r
}}

# Add CAIWAVE RADIUS server
/radius add address={config.radius_host} secret="{config.radius_secret}" service=hotspot comment="CAIWAVE RADIUS Server" timeout=3s

:log info "CAIWAVE: RADIUS server configured - {config.radius_host}"

# Enable RADIUS for hotspot
/ip hotspot profile set [find default=yes] use-radius=yes radius-interim-update=5m

# =========================================================
# 6. HOTSPOT SERVER PROFILE
# =========================================================
:if ([:len [/ip hotspot profile find name=caiwave-profile]] = 0) do={{
    /ip hotspot profile add name=caiwave-profile \\
        hotspot-address=10.10.0.1 \\
        dns-name=wifi.caiwave.com \\
        login-by=http-pap,http-chap \\
        use-radius=yes \\
        radius-accounting=yes \\
        nas-port-type=wireless-802.11 \\
        radius-interim-update=5m \\
        html-directory=hotspot \\
        rate-limit="" \\
        http-cookie-lifetime=1d \\
        split-user-domain=no
    :log info "CAIWAVE: Hotspot profile created"
}} else={{
    /ip hotspot profile set caiwave-profile \\
        use-radius=yes \\
        radius-accounting=yes \\
        radius-interim-update=5m
    :log info "CAIWAVE: Hotspot profile updated"
}}

# =========================================================
# 7. HOTSPOT SERVER SETUP
# =========================================================
:if ([:len [/ip hotspot find name=caiwave-hotspot]] = 0) do={{
    /ip hotspot add name=caiwave-hotspot interface=bridge-hotspot \\
        address-pool=pool-hotspot \\
        profile=caiwave-profile \\
        disabled=no
    :log info "CAIWAVE: Hotspot server created"
}} else={{
    /ip hotspot set caiwave-hotspot profile=caiwave-profile disabled=no
    :log info "CAIWAVE: Hotspot server updated"
}}

# Set NAS identifier
/ip hotspot set caiwave-hotspot addresses-per-mac=1

# =========================================================
# 8. ANTI-SHARING PROTECTION
# =========================================================
/ip hotspot set caiwave-hotspot addresses-per-mac=1

# Add connection tracking rules
:if ([:len [/ip firewall filter find comment="CAIWAVE Anti-Sharing"]] = 0) do={{
    /ip firewall filter add chain=forward action=drop connection-state=invalid comment="CAIWAVE Anti-Sharing"
}}

:log info "CAIWAVE: Anti-sharing protection enabled"

# =========================================================
# 9. FIREWALL RULES
# =========================================================
:if ([:len [/ip firewall nat find comment="CAIWAVE NAT"]] = 0) do={{
    /ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade comment="CAIWAVE NAT"
    :log info "CAIWAVE: NAT masquerade configured"
}}

:if ([:len [/ip firewall filter find comment="CAIWAVE Firewall"]] = 0) do={{
    /ip firewall filter add chain=input connection-state=established,related action=accept comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input connection-state=invalid action=drop comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input protocol=icmp action=accept comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input in-interface=bridge-hotspot action=accept comment="CAIWAVE Firewall"
    :log info "CAIWAVE: Firewall rules configured"
}}

# =========================================================
# 10. WALLED GARDEN
# =========================================================
/ip hotspot walled-garden add dst-host=*.caiwave.com action=allow comment="CAIWAVE Portal"
/ip hotspot walled-garden add dst-host=caiwave.com action=allow comment="CAIWAVE Portal"
/ip hotspot walled-garden add dst-host=*.paystack.com action=allow comment="Paystack Payment"
/ip hotspot walled-garden add dst-host=paystack.com action=allow comment="Paystack Payment"
/ip hotspot walled-garden add dst-host=*.paystack.co action=allow comment="Paystack Payment"
/ip hotspot walled-garden add dst-host=*.flutterwave.com action=allow comment="Payment Fallback"

:log info "CAIWAVE: Walled garden configured"

# =========================================================
# 11. REMOTE MANAGEMENT (API)
# =========================================================
# Enable API for remote management
/ip service set api address=0.0.0.0/0 disabled=no
/ip service set api-ssl disabled=no

# Add CAIWAVE management user
:if ([:len [/user find name=caiwave-admin]] = 0) do={{
    /user add name=caiwave-admin password={config.radius_secret} group=full
    :log info "CAIWAVE: Management user created"
}}

:log info "CAIWAVE: Remote management enabled"

# =========================================================
# CONFIGURATION COMPLETE
# =========================================================
:log info "=========================================="
:log info "CAIWAVE AUTO-CONFIGURATION COMPLETE!"
:log info "=========================================="
:log info ("NAS Identifier: " . "{config.nas_id}")
:log info "Hotspot Server: caiwave-hotspot"
:log info "Hotspot Network: 10.10.0.0/24"
:log info "RADIUS Server: {config.radius_host}"
:log info "=========================================="

:put ""
:put "==========================================="
:put "CAIWAVE CONFIGURATION COMPLETE!"
:put "==========================================="
:put ""
:put "NAS Identifier: {config.nas_id}"
:put "RADIUS Secret: {config.radius_secret}"
:put ""
:put "Please confirm the connection in your"
:put "CAIWAVE dashboard to complete setup."
:put ""
:put "==========================================="
'''


def generate_single_rsc_provisioning_script(
    router_name: str,
    nas_id: str,
    radius_secret: str,
    radius_host: str,
    callback_url: str = "",
    generated_at: Optional[datetime] = None,
) -> str:
    """Generate the .rsc content for one MikroTik onboarding event."""
    return build_single_rsc_provisioning_script(
        SingleRscProvisioningInput(
            router_name=router_name,
            nas_id=nas_id,
            radius_secret=radius_secret,
            radius_host=radius_host,
            callback_url=callback_url,
            generated_at=generated_at,
        )
    )


def build_single_rsc_provisioning_file(
    config: SingleRscProvisioningInput,
) -> SingleRscProvisioningOutput:
    """Build .rsc file metadata and content for one MikroTik onboarding event."""
    return SingleRscProvisioningOutput(
        filename=f"{_safe_filename(config.router_name)}-{_safe_filename(config.nas_id)}.rsc",
        content=build_single_rsc_provisioning_script(config),
    )


def generate_single_rsc_provisioning_file(
    router_name: str,
    nas_id: str,
    radius_secret: str,
    radius_host: str,
    callback_url: str = "",
    generated_at: Optional[datetime] = None,
) -> SingleRscProvisioningOutput:
    """Generate .rsc file metadata and content for one MikroTik onboarding event."""
    return build_single_rsc_provisioning_file(
        SingleRscProvisioningInput(
            router_name=router_name,
            nas_id=nas_id,
            radius_secret=radius_secret,
            radius_host=radius_host,
            callback_url=callback_url,
            generated_at=generated_at,
        )
    )


# Backward-compatible short aliases for callers that use a shorter name.
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