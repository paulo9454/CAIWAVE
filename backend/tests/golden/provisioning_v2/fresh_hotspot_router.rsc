# section planned: header

# ========================================================================
# CAIWAVE Identity
# ========================================================================
# CAIWAVE Provisioning Bundle: bundle:snapshot:router-1
# Snapshot: snapshot:router-1
# Router ID: router-1
# Hotspot ID: hotspot-1
/system identity set name="GOODlife"

# section planned: interfaces

# ========================================================================
# CAIWAVE Bridge
# ========================================================================
# Bridge action: create
/interface bridge add comment="CAIWAVE managed hotspot bridge" name="bridge-hotspot"
/interface bridge port add bridge="bridge-hotspot" comment="CAIWAVE managed bridge member" interface="ether2"

# ========================================================================
# CAIWAVE Addressing
# ========================================================================
# Client network: 10.10.0.0/24
/ip address add address="10.10.0.1/24" comment="CAIWAVE managed hotspot gateway" interface="bridge-hotspot"

# ========================================================================
# CAIWAVE DHCP
# ========================================================================
# DHCP pool: 10.10.0.10-10.10.0.254
/ip pool add comment="CAIWAVE managed hotspot DHCP pool" name="caiwave-pool-hotspot" ranges="10.10.0.10-10.10.0.254"
/ip dhcp-server add address-pool="caiwave-pool-hotspot" authoritative=after-2sec-delay comment="CAIWAVE managed hotspot DHCP server" disabled=no interface="bridge-hotspot" lease-time="1h" name="caiwave-dhcp-hotspot"
/ip dhcp-server network add address="10.10.0.0/24" comment="CAIWAVE managed hotspot DHCP network" dns-server="10.10.0.1" gateway="10.10.0.1"

# ========================================================================
# CAIWAVE DNS
# ========================================================================
# Captive DNS name: wifi.caiwave.com
/ip dns set allow-remote-requests=yes servers="1.1.1.1"
/ip dns static add address="10.10.0.1" comment="CAIWAVE managed captive portal DNS record" name="wifi.caiwave.com"

# ========================================================================
# CAIWAVE NAT
# ========================================================================
# NAT strategy: masquerade
/ip firewall nat add action="masquerade" chain="srcnat" comment="CAIWAVE managed hotspot masquerade" out-interface="ether1" src-address="10.10.0.0/24"

# ========================================================================
# CAIWAVE Hotspot
# ========================================================================
# Hotspot auth mode: radius
/ip hotspot profile add dns-name="wifi.caiwave.com" hotspot-address="10.10.0.1" login-by=http-pap name="caiwave-profile" use-radius=yes
/ip hotspot add address-pool="caiwave-pool-hotspot" disabled=no interface="bridge-hotspot" name="caiwave-hotspot" profile="caiwave-profile"

# ========================================================================
# CAIWAVE Portal
# ========================================================================
# Portal strategy: redirect
# Login redirect URL: https://caiwave.com/portal/login
# Success URL: https://caiwave.com/portal/success
# Failure URL: https://caiwave.com/portal/failed
/file remove [find name="hotspot/login.html"]
/file add name="hotspot/login.html" contents="<html><head><meta http-equiv=\"refresh\" content=\"0; url=https://caiwave.com/portal/login\"></head><body>Redirecting to CAIWAVE...<script>window.location.href=\"https://caiwave.com/portal/login\";</script></body></html>"
/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="caiwave.com"
/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="checkout.paystack.com"

# ========================================================================
# CAIWAVE RADIUS
# ========================================================================
# NAS identifier: CAIWAVE-GOODLIFE
/radius add accounting-port="1813" address="radius.caiwave.com" authentication-port="1812" comment="CAIWAVE managed RADIUS server" secret="router-radius-secret:router-1" service=hotspot timeout="3s"
/radius incoming set accept=no

# ========================================================================
# CAIWAVE Firewall
# ========================================================================
# WAN interface: ether1
# Default input policy: drop
# Default forward policy: drop
/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow established and related traffic"
/ip firewall filter add action="drop" chain="input" comment="CAIWAVE: Drop invalid packets"
/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow hotspot clients to query router DNS" dst-port="53" protocol="udp" src-address="10.10.0.0/24"
/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow DHCP service for hotspot clients" dst-port="67" protocol="udp" src-address="10.10.0.0/24"
/ip firewall filter add action="drop" chain="input" comment="CAIWAVE default drop WAN input" in-interface="ether1"
/ip firewall filter add action="drop" chain="forward" comment="CAIWAVE default drop unmatched forward"

# section planned: schedulers

# section planned: validation

# section planned: footer
