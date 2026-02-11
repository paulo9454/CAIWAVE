"""
CAIWAVE MikroTik Auto-Configuration and Onboarding Routes
Centipaid-style workflow for automated MikroTik setup
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import secrets
import os

mikrotik_router = APIRouter(prefix="/mikrotik", tags=["MikroTik"])

# ==================== Models ====================

class MikroTikRegisterRequest(BaseModel):
    """Request to register a new MikroTik router"""
    name: str = Field(..., min_length=3, max_length=50, description="Router name")
    hotspot_id: str = Field(..., description="Associated hotspot ID")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")

class MikroTikRouter(BaseModel):
    """Registered MikroTik router model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    hotspot_id: str
    owner_id: str
    
    # RADIUS credentials (auto-generated)
    radius_secret: str
    nas_identifier: str
    
    # Status tracking
    status: str = "pending_configuration"  # pending_configuration, configured, connected, offline, error
    connection_confirmed: bool = False
    last_seen: Optional[datetime] = None
    
    # Detected capabilities (populated after script runs)
    detected_ports: List[str] = Field(default_factory=list)
    detected_services: List[str] = Field(default_factory=list)
    firmware_version: Optional[str] = None
    model: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    configured_at: Optional[datetime] = None
    
    notes: Optional[str] = None

class MikroTikConfigResponse(BaseModel):
    """Response containing the auto-configuration script"""
    router_id: str
    router_name: str
    script: str
    instructions: List[str]
    radius_secret: str
    nas_identifier: str
    callback_url: str

class MikroTikConfirmRequest(BaseModel):
    """Request to confirm router connection"""
    router_id: str
    nas_identifier: str
    detected_ports: Optional[List[str]] = None
    detected_services: Optional[List[str]] = None
    firmware_version: Optional[str] = None
    model: Optional[str] = None

class MikroTikStatusResponse(BaseModel):
    """Router status response"""
    id: str
    name: str
    status: str
    connection_confirmed: bool
    last_seen: Optional[str]
    detected_ports: List[str]
    detected_services: List[str]


def generate_radius_secret() -> str:
    """Generate a secure RADIUS secret"""
    return secrets.token_hex(16)

def generate_nas_identifier(name: str) -> str:
    """Generate a unique NAS identifier"""
    clean_name = "".join(c for c in name if c.isalnum())[:10].upper()
    return f"CAIWAVE-{clean_name}-{secrets.token_hex(4).upper()}"


def generate_mikrotik_script(
    router_name: str,
    nas_identifier: str,
    radius_secret: str,
    radius_host: str,
    callback_url: str
) -> str:
    """
    Generate a complete MikroTik auto-configuration script.
    This script configures:
    - Hotspot service on all ethernet ports except wlan1
    - RADIUS integration with CAIWAVE backend
    - Anti-sharing protection
    - Proper DNS and firewall rules
    """
    
    script = f'''# =========================================================
# CAIWAVE MikroTik Auto-Configuration Script
# Router: {router_name}
# NAS Identifier: {nas_identifier}
# Generated: {datetime.now(timezone.utc).isoformat()}
# =========================================================

# IMPORTANT: Run this script in MikroTik Terminal after:
# 1. System Reset (optional but recommended for fresh install)
# 2. DHCP Client configured on ether1 for internet

:log info "CAIWAVE: Starting auto-configuration..."

# =========================================================
# 1. BASIC SYSTEM CONFIGURATION
# =========================================================
/system identity set name="{router_name}"
:log info "CAIWAVE: System identity set to {router_name}"

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
/radius add address={radius_host} secret="{radius_secret}" service=hotspot comment="CAIWAVE RADIUS Server" timeout=3s

:log info "CAIWAVE: RADIUS server configured - {radius_host}"

# Enable RADIUS for hotspot
/ip hotspot profile set [find default=yes] use-radius=yes radius-interim-update=5m

# =========================================================
# 6. HOTSPOT SERVER PROFILE
# =========================================================
# Create or update hotspot profile
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
# Limit one device per user (anti-sharing)
/ip hotspot set caiwave-hotspot addresses-per-mac=1

# Add connection tracking rules to prevent MAC spoofing
:if ([:len [/ip firewall filter find comment="CAIWAVE Anti-Sharing"]] = 0) do={{
    /ip firewall filter add chain=forward action=drop connection-state=invalid comment="CAIWAVE Anti-Sharing"
}}

:log info "CAIWAVE: Anti-sharing protection enabled"

# =========================================================
# 9. FIREWALL RULES
# =========================================================
# NAT Masquerade for internet access
:if ([:len [/ip firewall nat find comment="CAIWAVE NAT"]] = 0) do={{
    /ip firewall nat add chain=srcnat out-interface=ether1 action=masquerade comment="CAIWAVE NAT"
    :log info "CAIWAVE: NAT masquerade configured"
}}

# Basic firewall protection
:if ([:len [/ip firewall filter find comment="CAIWAVE Firewall"]] = 0) do={{
    /ip firewall filter add chain=input connection-state=established,related action=accept comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input connection-state=invalid action=drop comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input protocol=icmp action=accept comment="CAIWAVE Firewall"
    /ip firewall filter add chain=input in-interface=bridge-hotspot action=accept comment="CAIWAVE Firewall"
    :log info "CAIWAVE: Firewall rules configured"
}}

# =========================================================
# 10. USER MANAGER / LOCAL AUTH FALLBACK
# =========================================================
# Create a local user for testing (optional)
:if ([:len [/ip hotspot user find name=caiwave-test]] = 0) do={{
    /ip hotspot user add name=caiwave-test password=test123 server=caiwave-hotspot profile=default limit-uptime=5m comment="CAIWAVE Test User - Delete after testing"
    :log info "CAIWAVE: Test user created (delete after testing)"
}}

# =========================================================
# 11. WALLED GARDEN
# =========================================================
# Allow access to CAIWAVE portal without login
/ip hotspot walled-garden add dst-host=*.caiwave.com action=allow comment="CAIWAVE Portal"
/ip hotspot walled-garden add dst-host=caiwave.com action=allow comment="CAIWAVE Portal"

# Allow M-Pesa endpoints
/ip hotspot walled-garden add dst-host=*.safaricom.co.ke action=allow comment="M-Pesa"
/ip hotspot walled-garden add dst-host=safaricom.co.ke action=allow comment="M-Pesa"

:log info "CAIWAVE: Walled garden configured"

# =========================================================
# 12. CALLBACK TO CAIWAVE SERVER
# =========================================================
# Notify CAIWAVE server that configuration is complete
:local callbackUrl "{callback_url}"
:local nasId "{nas_identifier}"

# Collect system information
:local fwVersion [/system resource get version]
:local model [/system routerboard get model]

# Get active ports
:local activePorts ""
:foreach i in=[/interface ethernet find running=yes] do={{
    :set activePorts ($activePorts . [/interface ethernet get $i name] . ",")
}}

:log info ("CAIWAVE: Configuration complete. NAS ID: " . $nasId)
:log info ("CAIWAVE: Active ports: " . $activePorts)
:log info ("CAIWAVE: Firmware: " . $fwVersion . " Model: " . $model)

# =========================================================
# CONFIGURATION COMPLETE
# =========================================================
:log info "=========================================="
:log info "CAIWAVE AUTO-CONFIGURATION COMPLETE!"
:log info "=========================================="
:log info ("NAS Identifier: " . "{nas_identifier}")
:log info "Hotspot Server: caiwave-hotspot"
:log info "Hotspot Network: 10.10.0.0/24"
:log info "RADIUS Server: {radius_host}"
:log info "=========================================="
:log info "Next steps:"
:log info "1. Test hotspot by connecting a device"
:log info "2. Verify CAIWAVE portal loads"
:log info "3. Confirm connection in CAIWAVE dashboard"
:log info "=========================================="

:put ""
:put "==========================================="
:put "CAIWAVE CONFIGURATION COMPLETE!"
:put "==========================================="
:put ""
:put "NAS Identifier: {nas_identifier}"
:put "RADIUS Secret: {radius_secret}"
:put ""
:put "Please confirm the connection in your"
:put "CAIWAVE dashboard to complete setup."
:put ""
:put "==========================================="
'''
    
    return script


# The actual router functions will be added to server.py
# This file contains the models and script generation logic
