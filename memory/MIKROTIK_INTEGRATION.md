# CAIWAVE MikroTik Integration Guide

## Overview
This guide provides step-by-step instructions for integrating MikroTik routers with the CAIWAVE Wi-Fi Hotspot Billing Platform using FreeRADIUS for authentication.

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Wi-Fi     │────▶│  MikroTik   │────▶│ FreeRADIUS  │────▶│  CAIWAVE    │
│   Client    │     │   Router    │     │   Server    │     │   Backend   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │                    │                    │
                          │                    │                    │
                          ▼                    ▼                    ▼
                    Captive Portal      Authentication         MongoDB
                    (Login Page)         & Accounting          Database
```

---

## Prerequisites

1. **MikroTik Router** with RouterOS v6.x or v7.x
2. **Linux Server** (Ubuntu 20.04+ recommended) for FreeRADIUS
3. **CAIWAVE Backend** running and accessible
4. **Static IP** for the FreeRADIUS server

---

## Step 1: Install FreeRADIUS on Linux Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install FreeRADIUS and required modules
sudo apt install freeradius freeradius-utils freeradius-rest -y

# Verify installation
freeradius -v
```

---

## Step 2: Configure FreeRADIUS

### 2.1 Edit clients.conf
Add your MikroTik router as a RADIUS client:

```bash
sudo nano /etc/freeradius/3.0/clients.conf
```

Add at the end of the file:
```
client mikrotik_hotspot {
    ipaddr = 192.168.88.1    # Your MikroTik router IP
    secret = caiwave_radius_secret_2026
    nastype = mikrotik
    shortname = caiwave_hotspot
}
```

### 2.2 Configure REST Module
Create REST module configuration:

```bash
sudo nano /etc/freeradius/3.0/mods-enabled/rest
```

```
rest {
    tls {
        check_cert = no
        check_cert_cn = no
    }
    
    connect_uri = "https://www.caiwave.com/api"
    
    # Authentication
    authorize {
        uri = "${..connect_uri}/radius/authorize"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "password": "%{User-Password}", "nas_ip": "%{NAS-IP-Address}", "mac": "%{Calling-Station-Id}"}'
        tls = ${..tls}
    }
    
    # Accounting Start
    accounting {
        uri = "${..connect_uri}/radius/accounting"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "session_id": "%{Acct-Session-Id}", "status_type": "%{Acct-Status-Type}", "input_octets": %{Acct-Input-Octets}, "output_octets": %{Acct-Output-Octets}, "session_time": %{Acct-Session-Time}, "nas_ip": "%{NAS-IP-Address}"}'
        tls = ${..tls}
    }
    
    pool {
        start = 5
        min = 3
        max = 10
        spare = 3
        uses = 0
        lifetime = 0
        idle_timeout = 60
    }
}
```

### 2.3 Update sites-enabled/default
```bash
sudo nano /etc/freeradius/3.0/sites-enabled/default
```

In the `authorize` section, add:
```
authorize {
    rest
    if (ok) {
        update control {
            Auth-Type := rest
        }
    }
}
```

In the `authenticate` section, add:
```
authenticate {
    Auth-Type rest {
        rest
    }
}
```

In the `accounting` section, add:
```
accounting {
    rest
}
```

### 2.4 Restart FreeRADIUS
```bash
sudo systemctl restart freeradius
sudo systemctl enable freeradius
sudo systemctl status freeradius
```

---

## Step 3: Configure MikroTik Router

### 3.1 Access MikroTik via Winbox or SSH

### 3.2 Configure RADIUS Server
```
/radius add address=YOUR_RADIUS_SERVER_IP secret=caiwave_radius_secret_2026 service=hotspot
```

### 3.3 Create Hotspot Server
```
# Create IP pool for hotspot users
/ip pool add name=hotspot-pool ranges=192.168.100.10-192.168.100.254

# Create DHCP server (if not exists)
/ip dhcp-server add name=hotspot-dhcp interface=wlan1 address-pool=hotspot-pool lease-time=1h

# Create hotspot profile
/ip hotspot profile add name=caiwave-profile hotspot-address=192.168.100.1 dns-name=wifi.caiwave.com html-directory=hotspot login-by=http-chap,http-pap use-radius=yes radius-accounting=yes

# Create hotspot server
/ip hotspot add name=caiwave-hotspot interface=wlan1 address-pool=hotspot-pool profile=caiwave-profile
```

### 3.4 Configure Hotspot to Use RADIUS
```
/ip hotspot profile set caiwave-profile use-radius=yes radius-accounting=yes radius-interim-update=5m
```

### 3.5 Configure Walled Garden (Allow CAIWAVE without login)
```
/ip hotspot walled-garden ip add dst-host=www.caiwave.com action=accept
/ip hotspot walled-garden ip add dst-host=*.caiwave.com action=accept
/ip hotspot walled-garden ip add dst-host=*.safaricom.co.ke action=accept comment="M-Pesa"
```

---

## Step 4: Customize Captive Portal

### 4.1 Download CAIWAVE Captive Portal Template
Upload these files to MikroTik's hotspot directory:
- `login.html` - Main login page
- `alogin.html` - After login redirect
- `status.html` - Status page
- `logout.html` - Logout page
- `error.html` - Error page

### 4.2 Basic login.html Template
```html
<!DOCTYPE html>
<html>
<head>
    <title>CAIWAVE WiFi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: #050505; color: white; margin: 0; padding: 20px; }
        .container { max-width: 400px; margin: 50px auto; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { color: #0032FA; }
        input { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #333; background: #111; color: white; border-radius: 8px; }
        button { width: 100%; padding: 15px; background: #0032FA; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0028d4; }
        .packages { margin-top: 30px; }
        .package { background: #111; border: 1px solid #333; padding: 15px; border-radius: 8px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>CAIWAVE WiFi</h1>
            <p>Fast & Affordable Internet</p>
        </div>
        
        <form action="$(link-login-only)" method="post">
            <input type="hidden" name="dst" value="$(link-orig)">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Connect</button>
        </form>
        
        <div class="packages">
            <h3>Buy WiFi Access</h3>
            <a href="https://www.caiwave.com/buy?hotspot=$(identity)" style="text-decoration:none;">
                <div class="package">
                    <strong>KES 10</strong> - 30 Minutes<br>
                    <small>Perfect for quick browsing</small>
                </div>
            </a>
            <a href="https://www.caiwave.com/buy?hotspot=$(identity)" style="text-decoration:none;">
                <div class="package">
                    <strong>KES 50</strong> - 3 Hours<br>
                    <small>Great for streaming</small>
                </div>
            </a>
        </div>
        
        <p style="text-align:center; margin-top:30px; color:#666; font-size:12px;">
            Powered by CAIWAVE WiFi © 2026
        </p>
    </div>
</body>
</html>
```

---

## Step 5: CAIWAVE Backend RADIUS Endpoints

The following endpoints should be implemented in CAIWAVE backend:

### 5.1 POST /api/radius/authorize
Validates username/password and returns access attributes.

### 5.2 POST /api/radius/accounting
Records session start, interim updates, and stop events.

### 5.3 Current Implementation Status
- ✅ Basic RADIUS structure in server.py
- ⏳ Full FreeRADIUS REST integration (pending)
- ⏳ Session tracking via RADIUS accounting (pending)

---

## Step 6: Testing

### 6.1 Test RADIUS Connection
```bash
# From FreeRADIUS server
radtest testuser testpass YOUR_RADIUS_SERVER_IP 0 caiwave_radius_secret_2026
```

### 6.2 Test from MikroTik
```
/radius monitor 0
```

### 6.3 Check FreeRADIUS Logs
```bash
sudo tail -f /var/log/freeradius/radius.log
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| RADIUS timeout | Check firewall (ports 1812/1813 UDP) |
| Auth rejected | Verify secret matches on both sides |
| No accounting | Enable radius-accounting in hotspot profile |
| Captive portal not showing | Check walled garden configuration |

---

## Environment Variables Required

Add these to `/app/backend/.env`:

```
RADIUS_HOST=your-radius-server-ip
RADIUS_SECRET=caiwave_radius_secret_2026
RADIUS_AUTH_PORT=1812
RADIUS_ACCT_PORT=1813
```

---

## Security Recommendations

1. Use strong RADIUS secret (32+ characters)
2. Limit RADIUS client IPs in firewall
3. Use HTTPS for REST API calls
4. Rotate credentials periodically
5. Monitor failed authentication attempts

---

## Next Steps

1. Set up FreeRADIUS server
2. Configure MikroTik router
3. Implement full RADIUS endpoints in CAIWAVE
4. Test authentication flow
5. Deploy captive portal template

---

*Document Version: 1.0*
*Last Updated: February 2026*
