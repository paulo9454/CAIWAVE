# CAIWAVE MikroTik Quick Setup Guide

## Quick Copy-Paste Commands

### Before You Start
1. Access your MikroTik router via Winbox or SSH
2. Get your RADIUS secret from CAIWAVE dashboard
3. Note your wireless interface name (usually `wlan1`)

---

## MINIMAL SETUP (5 Commands)

Copy these commands one by one, replacing the placeholders:

```
# 1. Add RADIUS Server
/radius add address=radius.caiwave.com secret=YOUR_SECRET_HERE service=hotspot

# 2. Enable RADIUS Incoming (CoA)
/radius incoming set accept=yes port=3799

# 3. Create Hotspot Profile with RADIUS
/ip hotspot profile add name=caiwave use-radius=yes radius-accounting=yes radius-interim-update=5m

# 4. Create Hotspot Server
/ip hotspot add name=caiwave-hotspot interface=wlan1 profile=caiwave

# 5. Add Walled Garden for CAIWAVE
/ip hotspot walled-garden ip add dst-host=*.caiwave.com action=accept
/ip hotspot walled-garden ip add dst-host=*.safaricom.co.ke action=accept
```

---

## FULL SETUP (Recommended)

### Step 1: Network Setup
```
# Create IP Pool
/ip pool add name=caiwave-pool ranges=10.10.0.10-10.10.0.254

# Set Gateway IP
/ip address add address=10.10.0.1/24 interface=wlan1

# Create DHCP Server
/ip dhcp-server network add address=10.10.0.0/24 gateway=10.10.0.1 dns-server=8.8.8.8
/ip dhcp-server add name=caiwave-dhcp interface=wlan1 address-pool=caiwave-pool
```

### Step 2: RADIUS Configuration
```
# Add CAIWAVE RADIUS (CHANGE YOUR_SECRET_HERE)
/radius add address=radius.caiwave.com secret=YOUR_SECRET_HERE service=hotspot authentication-port=1812 accounting-port=1813

# Enable CoA/Disconnect
/radius incoming set accept=yes port=3799
```

### Step 3: User Profiles
```
# Free (512Kbps, 10min)
/ip hotspot user profile add name=caiwave-free rate-limit=512K/512K session-timeout=10m

# Basic (2Mbps)
/ip hotspot user profile add name=caiwave-basic rate-limit=2M/2M session-timeout=1h

# Standard (5Mbps)
/ip hotspot user profile add name=caiwave-standard rate-limit=5M/5M session-timeout=3h

# Premium (10Mbps)
/ip hotspot user profile add name=caiwave-premium rate-limit=10M/10M
```

### Step 4: Hotspot Server
```
# Create Profile
/ip hotspot profile add name=caiwave-profile hotspot-address=10.10.0.1 dns-name=wifi.caiwave.com use-radius=yes radius-accounting=yes radius-interim-update=5m login-by=http-chap,http-pap,cookie

# Create Hotspot
/ip hotspot add name=caiwave-hotspot interface=wlan1 address-pool=caiwave-pool profile=caiwave-profile
```

### Step 5: Walled Garden
```
# CAIWAVE Platform
/ip hotspot walled-garden ip add dst-host=*.caiwave.com action=accept
/ip hotspot walled-garden ip add dst-host=caiwave.com action=accept

# M-Pesa Payments
/ip hotspot walled-garden ip add dst-host=*.safaricom.co.ke action=accept

# Captive Portal Detection
/ip hotspot walled-garden ip add dst-host=connectivitycheck.gstatic.com action=accept
/ip hotspot walled-garden ip add dst-host=captive.apple.com action=accept
```

### Step 6: Firewall
```
# Allow RADIUS ports
/ip firewall filter add chain=input protocol=udp dst-port=1812 action=accept comment="RADIUS Auth"
/ip firewall filter add chain=input protocol=udp dst-port=1813 action=accept comment="RADIUS Acct"
/ip firewall filter add chain=input protocol=udp dst-port=3799 action=accept comment="RADIUS CoA"

# NAT for internet
/ip firewall nat add chain=srcnat src-address=10.10.0.0/24 action=masquerade
```

---

## Verification Commands

```
# Check hotspot status
/ip hotspot print

# Check RADIUS connection
/radius print
/radius monitor 0

# View active users
/ip hotspot active print

# View RADIUS logs
/log print where topics~"radius"
```

---

## Troubleshooting

| Issue | Command |
|-------|---------|
| RADIUS not connecting | `/radius monitor 0` |
| Users can't get IP | `/ip dhcp-server print` |
| No internet after login | `/ip firewall nat print` |
| Captive portal not showing | `/ip hotspot print` |

---

## Port Reference

| Port | Protocol | Purpose |
|------|----------|---------|
| 1812 | UDP | RADIUS Authentication |
| 1813 | UDP | RADIUS Accounting |
| 3799 | UDP | RADIUS CoA/Disconnect |

---

## Support

- Email: support@caiwave.com
- WhatsApp: +254738570630
- Documentation: www.caiwave.com/docs

---

*Quick Setup Guide v1.0 - February 2026*
