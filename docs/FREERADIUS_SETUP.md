# FreeRADIUS + MikroTik Setup Guide for CAIWAVE

This guide walks you through setting up FreeRADIUS to work with CAIWAVE's hotspot billing system.

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WiFi User     │────▶│  MikroTik       │────▶│  FreeRADIUS     │
│   Device        │     │  Router         │     │  Server         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  CAIWAVE API    │
                                                │  (MongoDB)      │
                                                └─────────────────┘
```

**Flow:**
1. User connects to WiFi → MikroTik redirects to Captive Portal
2. User watches ads, buys package via CAIWAVE
3. CAIWAVE generates RADIUS credentials
4. User authenticates → MikroTik asks FreeRADIUS
5. FreeRADIUS checks CAIWAVE API → Grants/Denies access
6. User gets internet access with time/data limits

---

## Part 1: FreeRADIUS Server Setup

### 1.1 Install FreeRADIUS (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install FreeRADIUS and REST module
sudo apt install freeradius freeradius-rest freeradius-utils -y

# Verify installation
freeradius -v
```

### 1.2 Install on CentOS/RHEL

```bash
sudo yum install freeradius freeradius-rest freeradius-utils -y
```

---

## Part 2: Configure FreeRADIUS for CAIWAVE

### 2.1 Enable REST Module

```bash
# Navigate to mods-available
cd /etc/freeradius/3.0/mods-available/

# Edit REST module
sudo nano rest
```

**Replace content with:**

```
rest {
    # CAIWAVE API endpoint
    connect_uri = "https://your-caiwave-domain.com/api"
    
    # Connection settings
    connect_timeout = 4.0
    http_timeout = 4.0
    
    # Authentication endpoint
    authorize {
        uri = "${..connect_uri}/radius/authorize"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "password": "%{User-Password}", "nas_ip": "%{NAS-IP-Address}", "called_station": "%{Called-Station-Id}"}'
        tls = ${..tls}
    }
    
    # Accounting endpoint (session start/stop)
    accounting {
        uri = "${..connect_uri}/radius/accounting"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "session_id": "%{Acct-Session-Id}", "status_type": "%{Acct-Status-Type}", "nas_ip": "%{NAS-IP-Address}", "session_time": "%{Acct-Session-Time}", "input_octets": "%{Acct-Input-Octets}", "output_octets": "%{Acct-Output-Octets}"}'
        tls = ${..tls}
    }
    
    # Post-auth (after successful authentication)
    post-auth {
        uri = "${..connect_uri}/radius/post-auth"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "session_id": "%{Acct-Session-Id}", "nas_ip": "%{NAS-IP-Address}", "result": "%{reply:Packet-Type}"}'
        tls = ${..tls}
    }
    
    # TLS settings (for HTTPS)
    tls {
        verify_cert = no
        verify_cert_cn = no
    }
}
```

### 2.2 Enable the REST Module

```bash
# Create symlink to enable module
cd /etc/freeradius/3.0/mods-enabled/
sudo ln -s ../mods-available/rest rest
```

### 2.3 Configure Virtual Server

Edit the default site:

```bash
sudo nano /etc/freeradius/3.0/sites-available/default
```

**Modify these sections:**

```
authorize {
    # Remove or comment out 'files' and 'sql'
    # files
    # sql
    
    # Add REST authorization
    rest
    
    # If REST returns OK, user is authorized
    if (ok) {
        update control {
            Auth-Type := rest
        }
    }
}

authenticate {
    # Add REST authentication
    Auth-Type rest {
        rest
    }
}

accounting {
    # Add REST accounting
    rest
}

post-auth {
    # Add REST post-auth
    rest
}
```

### 2.4 Configure Clients (MikroTik NAS)

Edit clients.conf:

```bash
sudo nano /etc/freeradius/3.0/clients.conf
```

**Add your MikroTik routers:**

```
# MikroTik Router 1
client mikrotik_router_1 {
    ipaddr = 192.168.1.1
    secret = your_shared_secret_here
    nastype = mikrotik
    shortname = hotspot_nairobi_cbd
}

# MikroTik Router 2 (example)
client mikrotik_router_2 {
    ipaddr = 192.168.2.1
    secret = another_secret_here
    nastype = mikrotik
    shortname = hotspot_westlands
}

# Allow any IP (for dynamic routers) - USE WITH CAUTION
# client dynamic_clients {
#     ipaddr = 0.0.0.0/0
#     secret = global_shared_secret
#     nastype = mikrotik
# }
```

---

## Part 3: CAIWAVE Backend RADIUS Endpoints

Add these endpoints to your CAIWAVE backend (`server.py`):

```python
# ==================== RADIUS Authentication Endpoints ====================

class RADIUSAuthorizeRequest(BaseModel):
    username: str
    password: str
    nas_ip: str = ""
    called_station: str = ""

class RADIUSAccountingRequest(BaseModel):
    username: str
    session_id: str
    status_type: str  # Start, Stop, Interim-Update
    nas_ip: str = ""
    session_time: int = 0
    input_octets: int = 0
    output_octets: int = 0

@radius_router.post("/authorize")
async def radius_authorize(request: RADIUSAuthorizeRequest):
    """FreeRADIUS calls this to authenticate users"""
    
    # Find active WiFi session with these credentials
    session = await db.wifi_sessions.find_one({
        "username": request.username,
        "status": "active"
    })
    
    if not session:
        return {"reply": "Access-Reject", "message": "Invalid credentials"}
    
    # Verify password
    if session.get("password") != request.password:
        return {"reply": "Access-Reject", "message": "Invalid password"}
    
    # Check if session expired
    if session.get("expires_at") and datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc):
        return {"reply": "Access-Reject", "message": "Session expired"}
    
    # Calculate remaining time (in seconds)
    remaining_seconds = 0
    if session.get("expires_at"):
        expires = datetime.fromisoformat(session["expires_at"])
        remaining_seconds = int((expires - datetime.now(timezone.utc)).total_seconds())
    
    # Return access granted with session limits
    return {
        "reply": "Access-Accept",
        "attributes": {
            "Session-Timeout": remaining_seconds,
            "Acct-Interim-Interval": 300,  # Update every 5 minutes
            "Mikrotik-Rate-Limit": session.get("rate_limit", "2M/2M"),  # Upload/Download limit
        }
    }

@radius_router.post("/accounting")
async def radius_accounting(request: RADIUSAccountingRequest):
    """FreeRADIUS calls this to track session usage"""
    
    session = await db.wifi_sessions.find_one({"username": request.username})
    
    if not session:
        return {"status": "error", "message": "Session not found"}
    
    now = datetime.now(timezone.utc).isoformat()
    
    if request.status_type == "Start":
        # Session started
        await db.wifi_sessions.update_one(
            {"username": request.username},
            {"$set": {
                "radius_session_id": request.session_id,
                "started_at": now,
                "nas_ip": request.nas_ip,
                "status": "connected"
            }}
        )
        
    elif request.status_type == "Stop":
        # Session ended
        await db.wifi_sessions.update_one(
            {"username": request.username},
            {"$set": {
                "ended_at": now,
                "total_session_time": request.session_time,
                "total_upload": request.input_octets,
                "total_download": request.output_octets,
                "status": "completed"
            }}
        )
        
        # Update hotspot statistics
        await db.hotspots.update_one(
            {"id": session.get("hotspot_id")},
            {"$inc": {"total_sessions": 1}}
        )
        
    elif request.status_type == "Interim-Update":
        # Periodic update during session
        await db.wifi_sessions.update_one(
            {"username": request.username},
            {"$set": {
                "current_session_time": request.session_time,
                "current_upload": request.input_octets,
                "current_download": request.output_octets,
                "last_update": now
            }}
        )
    
    return {"status": "ok"}

@radius_router.post("/post-auth")
async def radius_post_auth(request: dict):
    """Called after authentication decision"""
    # Log authentication attempts
    await db.radius_logs.insert_one({
        "id": str(uuid4()),
        "username": request.get("username"),
        "nas_ip": request.get("nas_ip"),
        "result": request.get("result"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "ok"}
```

---

## Part 4: MikroTik Router Configuration

### 4.1 Generated Script from CAIWAVE

When an owner registers a router in CAIWAVE, they get a script like this:

```routeros
# CAIWAVE Hotspot Configuration Script
# Router: Nairobi CBD Hotspot
# Generated: 2026-02-12

# Set RADIUS server
/radius
add address=YOUR_RADIUS_SERVER_IP secret=YOUR_SHARED_SECRET service=hotspot \
    authentication-port=1812 accounting-port=1813 timeout=3000ms

# Enable RADIUS for hotspot
/ip hotspot profile
set default use-radius=yes

# Create hotspot server
/ip hotspot
add name=caiwave-hotspot interface=wlan1 address-pool=hotspot-pool \
    profile=default disabled=no

# Set login page to redirect to CAIWAVE captive portal
/ip hotspot profile
set default login-by=http-chap,http-pap \
    html-directory=hotspot \
    http-cookie-lifetime=1d \
    login-url="https://your-caiwave-domain.com/portal/HOTSPOT_ID"

# Walled garden (allow access to these without auth)
/ip hotspot walled-garden ip
add dst-host=your-caiwave-domain.com action=accept
add dst-host=*.paystack.com action=accept
add dst-host=*.paystack.co action=accept

# Bandwidth profiles (optional)
/queue simple
add name=hotspot-users target=192.168.88.0/24 max-limit=10M/10M
```

### 4.2 Manual MikroTik Setup (via Winbox)

1. **Add RADIUS Server:**
   - Go to `RADIUS` → `Add New`
   - Address: Your FreeRADIUS server IP
   - Secret: Shared secret (same as in clients.conf)
   - Service: Check `hotspot`
   - Ports: Auth 1812, Accounting 1813

2. **Configure Hotspot:**
   - Go to `IP` → `Hotspot` → `Server Profiles`
   - Edit your profile
   - Check `Use RADIUS`
   - Set Login URL to your CAIWAVE captive portal

3. **Walled Garden:**
   - Go to `IP` → `Hotspot` → `Walled Garden`
   - Add your CAIWAVE domain
   - Add payment gateway domains (Paystack)

---

## Part 5: Testing the Integration

### 5.1 Test FreeRADIUS

```bash
# Stop FreeRADIUS service
sudo systemctl stop freeradius

# Run in debug mode
sudo freeradius -X
```

### 5.2 Test Authentication

```bash
# From another terminal, test with radtest
radtest testuser testpass localhost 0 testing123

# Expected output for valid user:
# Received Access-Accept
```

### 5.3 Test from MikroTik

```routeros
# In MikroTik terminal
/radius monitor 0
```

### 5.4 Test CAIWAVE API

```bash
# Test authorize endpoint
curl -X POST https://your-domain.com/api/radius/authorize \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass","nas_ip":"192.168.1.1"}'
```

---

## Part 6: Production Deployment Checklist

### Server Requirements
- [ ] Ubuntu 20.04+ or CentOS 8+
- [ ] 2GB RAM minimum
- [ ] Open ports: 1812/UDP (Auth), 1813/UDP (Accounting), 3799/UDP (CoA)
- [ ] Static IP address

### Security Checklist
- [ ] Use strong RADIUS shared secrets (32+ characters)
- [ ] Enable firewall, only allow MikroTik IPs to RADIUS ports
- [ ] Use HTTPS for CAIWAVE API
- [ ] Rotate secrets periodically
- [ ] Monitor failed authentication attempts

### Environment Variables for CAIWAVE

Add to your `backend/.env`:

```env
# RADIUS Configuration
RADIUS_ENABLED=true
RADIUS_HOST=your-radius-server-ip
RADIUS_SECRET=your-strong-shared-secret
RADIUS_AUTH_PORT=1812
RADIUS_ACCT_PORT=1813
RADIUS_COA_PORT=3799
```

---

## Part 7: Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| "Access-Reject" for valid users | Check password in DB matches, check session not expired |
| MikroTik can't reach RADIUS | Check firewall, verify IP and ports |
| REST module not working | Check FreeRADIUS logs, verify CAIWAVE API URL |
| Sessions not tracking | Verify accounting endpoint, check MikroTik sends accounting |

### Log Locations

```bash
# FreeRADIUS logs
tail -f /var/log/freeradius/radius.log

# Debug mode output
sudo freeradius -X

# CAIWAVE backend logs
tail -f /var/log/supervisor/backend.err.log
```

---

## Quick Reference: Port Numbers

| Service | Port | Protocol |
|---------|------|----------|
| RADIUS Auth | 1812 | UDP |
| RADIUS Accounting | 1813 | UDP |
| RADIUS CoA | 3799 | UDP |
| CAIWAVE API | 443 | TCP (HTTPS) |
| MikroTik API | 8728 | TCP |
| MikroTik API-SSL | 8729 | TCP |

---

## Support

For issues with:
- **FreeRADIUS**: Check [FreeRADIUS Wiki](https://wiki.freeradius.org/)
- **MikroTik**: Check [MikroTik Wiki](https://wiki.mikrotik.com/)
- **CAIWAVE**: Contact your administrator

---

*Document Version: 1.0 | Last Updated: February 2026*
