################################################################################
#                    CAIWAVE MIKROTIK INTEGRATION SCRIPT                       #
#                         Universal Hotspot Setup                              #
#                                                                              #
#  This script configures any MikroTik router for CAIWAVE integration.        #
#  Copy, customize the variables below, and paste into your MikroTik terminal #
#                                                                              #
#  Version: 1.0                                                                #
#  Compatible: RouterOS v6.x and v7.x                                          #
#  Support: support@caiwave.com                                                #
################################################################################

#===============================================================================
# STEP 1: CUSTOMIZE THESE VARIABLES (REQUIRED)
#===============================================================================

# Your hotspot details - CHANGE THESE VALUES
:local hotspotName "CAIWAVE_Hotspot_001"
:local hotspotLocation "Nairobi, Kenya"
:local hotspotSSID "CAIWAVE_FREE_WIFI"
:local hotspotInterface "wlan1"

# CAIWAVE RADIUS Server - DO NOT CHANGE UNLESS INSTRUCTED
:local radiusServer "radius.caiwave.com"
:local radiusSecret "YOUR_RADIUS_SECRET_HERE"
:local radiusAuthPort "1812"
:local radiusAcctPort "1813"
:local radiusCoaPort "3799"

# Network Configuration - Adjust for your setup
:local hotspotNetwork "10.10.0.0/24"
:local hotspotGateway "10.10.0.1"
:local dhcpPoolStart "10.10.0.10"
:local dhcpPoolEnd "10.10.0.254"
:local dnsServer "8.8.8.8,8.8.4.4"

#===============================================================================
# STEP 2: CREATE IP ADDRESS POOL FOR HOTSPOT USERS
#===============================================================================

:put ">>> Creating IP Pool for hotspot users..."

/ip pool add name=caiwave-pool ranges=$dhcpPoolStart-$dhcpPoolEnd comment="CAIWAVE Hotspot User Pool"

#===============================================================================
# STEP 3: CONFIGURE IP ADDRESS ON HOTSPOT INTERFACE
#===============================================================================

:put ">>> Configuring IP address on hotspot interface..."

/ip address add address=$hotspotGateway/24 interface=$hotspotInterface network=$hotspotNetwork comment="CAIWAVE Hotspot Gateway"

#===============================================================================
# STEP 4: CREATE DHCP SERVER FOR HOTSPOT
#===============================================================================

:put ">>> Setting up DHCP server..."

# Create DHCP network
/ip dhcp-server network add address=$hotspotNetwork gateway=$hotspotGateway dns-server=$dnsServer comment="CAIWAVE DHCP Network"

# Create DHCP server
/ip dhcp-server add name=caiwave-dhcp interface=$hotspotInterface address-pool=caiwave-pool lease-time=1h disabled=no comment="CAIWAVE DHCP Server"

#===============================================================================
# STEP 5: ADD CAIWAVE RADIUS SERVER
#===============================================================================

:put ">>> Adding CAIWAVE RADIUS server..."

/radius add address=$radiusServer secret=$radiusSecret service=hotspot authentication-port=$radiusAuthPort accounting-port=$radiusAcctPort timeout=3s comment="CAIWAVE RADIUS Server"

# Enable RADIUS incoming (for CoA/Disconnect)
/radius incoming set accept=yes port=$radiusCoaPort

#===============================================================================
# STEP 6: CREATE USER PROFILES (RATE LIMITS)
#===============================================================================

:put ">>> Creating user profiles with rate limits..."

# Free Trial Profile - 512Kbps (for first-time users viewing ads)
/ip hotspot user profile add name="caiwave-free" rate-limit="512K/512K" session-timeout=10m idle-timeout=5m shared-users=1 transparent-proxy=no comment="CAIWAVE Free Trial (512Kbps, 10min)"

# Basic Package - 2Mbps
/ip hotspot user profile add name="caiwave-basic" rate-limit="2M/2M" session-timeout=1h idle-timeout=15m shared-users=1 transparent-proxy=no comment="CAIWAVE Basic (2Mbps)"

# Standard Package - 5Mbps
/ip hotspot user profile add name="caiwave-standard" rate-limit="5M/5M" session-timeout=3h idle-timeout=30m shared-users=1 transparent-proxy=no comment="CAIWAVE Standard (5Mbps)"

# Premium Package - 10Mbps
/ip hotspot user profile add name="caiwave-premium" rate-limit="10M/10M" session-timeout=unlimited idle-timeout=1h shared-users=2 transparent-proxy=no comment="CAIWAVE Premium (10Mbps)"

# Unlimited Package - No limit
/ip hotspot user profile add name="caiwave-unlimited" rate-limit="" session-timeout=unlimited idle-timeout=2h shared-users=3 transparent-proxy=no comment="CAIWAVE Unlimited"

# Default profile for RADIUS users
/ip hotspot user profile add name="caiwave-radius" rate-limit="" session-timeout=unlimited idle-timeout=30m shared-users=1 transparent-proxy=no comment="CAIWAVE RADIUS Default"

#===============================================================================
# STEP 7: CREATE HOTSPOT SERVER PROFILE
#===============================================================================

:put ">>> Creating hotspot server profile..."

/ip hotspot profile add \
    name="caiwave-profile" \
    hotspot-address=$hotspotGateway \
    dns-name="wifi.caiwave.com" \
    html-directory="hotspot" \
    http-cookie-lifetime=1d \
    login-by=http-chap,http-pap,cookie,trial \
    trial-uptime-limit=10m \
    trial-uptime-reset=1d \
    use-radius=yes \
    radius-accounting=yes \
    radius-interim-update=5m \
    radius-default-domain="" \
    rate-limit="" \
    comment="CAIWAVE Hotspot Profile"

#===============================================================================
# STEP 8: CREATE HOTSPOT SERVER
#===============================================================================

:put ">>> Creating hotspot server..."

/ip hotspot add \
    name=$hotspotName \
    interface=$hotspotInterface \
    address-pool=caiwave-pool \
    profile=caiwave-profile \
    idle-timeout=5m \
    keepalive-timeout=none \
    disabled=no \
    comment="CAIWAVE Hotspot - $hotspotLocation"

#===============================================================================
# STEP 9: CONFIGURE WALLED GARDEN (BYPASS SITES)
#===============================================================================

:put ">>> Setting up walled garden (sites accessible without login)..."

# CAIWAVE Platform (REQUIRED)
/ip hotspot walled-garden ip add dst-host=*.caiwave.com action=accept comment="CAIWAVE Platform"
/ip hotspot walled-garden ip add dst-host=caiwave.com action=accept comment="CAIWAVE Main"
/ip hotspot walled-garden ip add dst-host=www.caiwave.com action=accept comment="CAIWAVE WWW"

# M-Pesa Payment Gateway (REQUIRED for payments)
/ip hotspot walled-garden ip add dst-host=*.safaricom.co.ke action=accept comment="M-Pesa Safaricom"
/ip hotspot walled-garden ip add dst-host=*.mpesa.in action=accept comment="M-Pesa Gateway"

# DNS Resolution (REQUIRED)
/ip hotspot walled-garden ip add dst-host=8.8.8.8 action=accept comment="Google DNS"
/ip hotspot walled-garden ip add dst-host=8.8.4.4 action=accept comment="Google DNS Alt"

# Captive Portal Detection (Recommended for better UX)
/ip hotspot walled-garden ip add dst-host=connectivitycheck.gstatic.com action=accept comment="Android Captive Portal"
/ip hotspot walled-garden ip add dst-host=www.gstatic.com action=accept comment="Google Static"
/ip hotspot walled-garden ip add dst-host=captive.apple.com action=accept comment="Apple Captive Portal"
/ip hotspot walled-garden ip add dst-host=www.apple.com action=accept comment="Apple"

#===============================================================================
# STEP 10: CONFIGURE FIREWALL FOR RADIUS
#===============================================================================

:put ">>> Configuring firewall rules for RADIUS..."

# Allow RADIUS Authentication (UDP 1812)
/ip firewall filter add chain=input protocol=udp dst-port=$radiusAuthPort action=accept comment="CAIWAVE: RADIUS Auth" place-before=0

# Allow RADIUS Accounting (UDP 1813)
/ip firewall filter add chain=input protocol=udp dst-port=$radiusAcctPort action=accept comment="CAIWAVE: RADIUS Acct" place-before=0

# Allow RADIUS CoA/Disconnect (UDP 3799)
/ip firewall filter add chain=input protocol=udp dst-port=$radiusCoaPort action=accept comment="CAIWAVE: RADIUS CoA" place-before=0

# Allow incoming from RADIUS server
/ip firewall filter add chain=input src-address=$radiusServer action=accept comment="CAIWAVE: RADIUS Server" place-before=0

#===============================================================================
# STEP 11: NAT MASQUERADE FOR INTERNET ACCESS
#===============================================================================

:put ">>> Setting up NAT for internet access..."

/ip firewall nat add chain=srcnat src-address=$hotspotNetwork action=masquerade comment="CAIWAVE Hotspot NAT"

#===============================================================================
# STEP 12: SET ROUTER IDENTITY
#===============================================================================

:put ">>> Setting router identity..."

/system identity set name=$hotspotName

#===============================================================================
# STEP 13: ENABLE RADIUS DEBUG LOGGING (OPTIONAL)
#===============================================================================

:put ">>> Enabling RADIUS logging..."

/system logging add topics=radius action=memory comment="CAIWAVE RADIUS Logging"

#===============================================================================
# VERIFICATION COMMANDS
#===============================================================================

:put ""
:put "=============================================="
:put "       CAIWAVE HOTSPOT SETUP COMPLETE!       "
:put "=============================================="
:put ""
:put "Hotspot Name: $hotspotName"
:put "Location: $hotspotLocation"
:put "SSID: $hotspotSSID"
:put "Gateway: $hotspotGateway"
:put "RADIUS Server: $radiusServer"
:put ""
:put ">>> Run these commands to verify setup:"
:put ""
:put "/ip hotspot print"
:put "/radius print"
:put "/ip hotspot user profile print"
:put "/ip hotspot walled-garden ip print"
:put "/ip firewall filter print where comment~\"CAIWAVE\""
:put ""
:put ">>> Test RADIUS connectivity:"
:put "/radius monitor 0"
:put ""
:put ">>> View connected users:"
:put "/ip hotspot active print"
:put ""
:put ">>> Need help? Contact support@caiwave.com"
:put "=============================================="

################################################################################
#                          END OF CAIWAVE SETUP SCRIPT                         #
################################################################################
