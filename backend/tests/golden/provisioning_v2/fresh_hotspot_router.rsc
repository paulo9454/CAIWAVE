# section planned: header

# ========================================================================
# CAIWAVE Identity
# ========================================================================
# CAIWAVE Provisioning Bundle: bundle:snapshot:router-1
# Snapshot: snapshot:router-1
# Router ID: router-1
# Hotspot ID: hotspot-1
/system identity set name="GOODlife"

# ========================================================================
# CAIWAVE Interfaces
# ========================================================================
# WAN interface: ether1
/ip dhcp-client remove [find where interface="ether1"]
/ip dhcp-client add add-default-route=yes comment="CAIWAVE managed WAN DHCP client" default-route-distance="1" disabled=no interface="ether1" use-peer-dns=yes use-peer-ntp=yes

# section planned: wireless

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
/ip hotspot profile add dns-name="wifi.caiwave.com" hotspot-address="10.10.0.1" login-by=http-pap name="caiwave-profile" radius-accounting=yes radius-interim-update=5m use-radius=yes
/ip hotspot add address-pool="caiwave-pool-hotspot" disabled=no interface="bridge-hotspot" name="caiwave-hotspot" profile="caiwave-profile"

# ========================================================================
# CAIWAVE Portal
# ========================================================================
# Portal strategy: redirect
# Login redirect URL: https://caiwave.com/portal/portal/hotspot-1?mac=\$(mac)&ip=\$(ip)&dst=\$(link-orig-esc)&login_url=\$(link-login-only)
# Success URL: https://caiwave.com/portal/success
# Failure URL: https://caiwave.com/portal/failed
/file remove [find name="hotspot/login.html"]
/file add name="hotspot/login.html" contents="<html><head><meta http-equiv=\"refresh\" content=\"0; url=https://caiwave.com/portal/portal/hotspot-1?mac=\$(mac)&ip=\$(ip)&dst=\$(link-orig-esc)&login_url=\$(link-login-only)\"></head><body>Redirecting to CAIWAVE...<script>window.location.href=\"https://caiwave.com/portal/portal/hotspot-1?mac=\$(mac)&ip=\$(ip)&dst=\$(link-orig-esc)&login_url=\$(link-login-only)\";</script></body></html>"
/file remove [find name="hotspot/redirect.html"]
/file add name="hotspot/redirect.html" contents="\$(if http-status == 302)Hotspot login required\$(endif)\$(if http-header == \"Location\")\$(link-redirect)\$(endif)"
/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="caiwave.com"
/ip hotspot walled-garden add action="allow" comment="CAIWAVE managed portal walled garden host" dst-host="checkout.paystack.com"

# ========================================================================
# CAIWAVE RADIUS
# ========================================================================
# NAS identifier: CAIWAVE-GOODLIFE
# RADIUS host: radius.caiwave.com -> 136.65.3.100
/radius add accounting-port="1813" address="136.65.3.100" authentication-port="1812" comment="CAIWAVE managed RADIUS server" require-message-auth=no secret="router-radius-secret:router-1" service=hotspot timeout="3s"
/radius incoming set accept=no

# ========================================================================
# CAIWAVE Firewall
# ========================================================================
# WAN interface: ether1
# Default input policy: drop
# Default forward policy: drop
/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow established and related traffic" connection-state="established,related"
/ip firewall filter add action="accept" chain="forward" comment="CAIWAVE: Allow established and related forwarding" connection-state="established,related"
/ip firewall filter add action="accept" chain="forward" comment="CAIWAVE: Allow authenticated hotspot clients to internet" hotspot="auth"
/ip firewall filter add action="drop" chain="input" comment="CAIWAVE: Drop invalid packets" connection-state="invalid"
/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow hotspot clients to query router DNS" dst-port="53" protocol="udp" src-address="10.10.0.0/24"
/ip firewall filter add action="accept" chain="input" comment="CAIWAVE: Allow DHCP service for hotspot clients" dst-port="67" protocol="udp" src-address="10.10.0.0/24"
/ip firewall address-list add address="caiwave.com" comment="CAIWAVE pre-auth host" list="CAIWAVE-PREAUTH"
/ip firewall address-list add address="checkout.paystack.com" comment="CAIWAVE pre-auth host" list="CAIWAVE-PREAUTH"
/ip firewall filter add action="accept" chain="forward" comment="CAIWAVE: Allow pre-auth portal and payment traffic" dst-address-list="CAIWAVE-PREAUTH" dst-port="80,443" hotspot="from-client,!auth" protocol="tcp"
/ip firewall filter add action="drop" chain="input" comment="CAIWAVE default drop WAN input" in-interface="ether1"
/ip firewall filter add action="drop" chain="forward" comment="CAIWAVE default drop unmatched forward"

# section planned: validation

# section planned: footer
