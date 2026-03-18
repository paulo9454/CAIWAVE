# CAIWAVE MikroTik ↔ FreeRADIUS Troubleshooting Playbook

Use this checklist when a MikroTik hotspot is failing to authenticate users against FreeRADIUS/CAIWAVE.

---

## 1) Confirm Basic Network Reachability First

On the **MikroTik** terminal:

```routeros
# Replace with your FreeRADIUS server IP
/ping 10.10.10.5 count=5
```

On the **FreeRADIUS** server:

```bash
# Confirm UDP listeners
sudo ss -lunp | rg '1812|1813'

# If UFW is enabled, allow RADIUS from MikroTik only
sudo ufw allow from <MIKROTIK_IP> to any port 1812 proto udp
sudo ufw allow from <MIKROTIK_IP> to any port 1813 proto udp
```

If ping fails or UDP ports are closed, fix networking/firewall first before debugging RADIUS logic.

---

## 2) Validate Shared Secret + Client IP Mapping

Most "silent timeout" problems are either wrong secret or wrong NAS IP in `clients.conf`.

On FreeRADIUS (`/etc/freeradius/3.0/clients.conf`):

```conf
client mikrotik_hotspot_1 {
    ipaddr = 192.168.88.1
    secret = STRONG_SHARED_SECRET_HERE
    nastype = mikrotik
}
```

On MikroTik:

```routeros
/radius print detail
# verify:
# - address=<freeradius-ip>
# - service=hotspot
# - secret matches clients.conf exactly
# - authentication-port=1812
# - accounting-port=1813
```

> Tip: If MikroTik reaches FreeRADIUS but secret is wrong, you'll often see `Ignoring request from unknown client` or `Invalid Message-Authenticator` in debug logs.

---

## 3) Make Sure Hotspot Profile Is Actually Using RADIUS

```routeros
/ip hotspot profile print detail
# Expect:
# use-radius=yes
# radius-accounting=yes
# radius-interim-update=5m (recommended)
```

If this is disabled, users authenticate locally and FreeRADIUS is never queried.

---

## 4) Run FreeRADIUS in Debug Mode While Testing

```bash
sudo systemctl stop freeradius
sudo freeradius -X
```

Then try a hotspot login from a client and inspect output:

- **No request appears**: network/firewall/client IP mismatch.
- **Access-Reject from REST**: CAIWAVE API validation failed (credentials/session expiry).
- **REST timeouts**: API URL/DNS/TLS issue between FreeRADIUS and CAIWAVE backend.

---

## 5) Verify REST Module and CAIWAVE Endpoints

Check your REST module config (`mods-available/rest`):

- `connect_uri` is correct and reachable.
- `authorize` URL points to `/api/radius/authorize`.
- `accounting` URL points to `/api/radius/accounting`.
- Timeouts are reasonable (`connect_timeout = 4.0`, `http_timeout = 4.0`).

From the FreeRADIUS host, test API manually:

```bash
curl -i -X POST https://<caiwave-domain>/api/radius/authorize \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo","nas_ip":"192.168.88.1"}'
```

If curl cannot connect or gets TLS errors, FreeRADIUS REST will fail too.

---

## 6) Minimal Known-Good MikroTik Snippet (RouterOS 7)

```routeros
/radius
add service=hotspot address=10.10.10.5 secret="STRONG_SHARED_SECRET_HERE" authentication-port=1812 accounting-port=1813 timeout=3s

/ip hotspot profile
set [ find default=yes ] use-radius=yes radius-accounting=yes radius-interim-update=5m login-by=http-chap,http-pap
```

Optional verification:

```routeros
/radius monitor 0 once
/log print where message~"radius"
```

---

## 7) Walled Garden Requirements (Captive Portal + Payments)

Ensure unauthenticated clients can reach:

- CAIWAVE portal domain
- Payment provider endpoints (Paystack/M-Pesa)
- DNS (if using external DNS for portal/payment resolution)

Example:

```routeros
/ip hotspot walled-garden ip
add dst-host=your-caiwave-domain.com action=accept
add dst-host=*.paystack.com action=accept
add dst-host=*.paystack.co action=accept
```

If missing, users may never complete purchase/login flow even when RADIUS works.

---

## 8) Fast Symptom → Root Cause Mapping

| Symptom | Likely Cause | First Check |
|---|---|---|
| Login hangs then fails | Firewall / client IP mismatch / wrong secret | `freeradius -X` + `/radius print detail` |
| Immediate reject | Wrong credentials, expired CAIWAVE session | `/api/radius/authorize` response |
| Auth works, usage not tracked | Accounting not enabled | `radius-accounting=yes`, port 1813, accounting REST block |
| Portal opens but payment/login callbacks fail | Missing walled-garden entries | `ip hotspot walled-garden ip print` |
| Intermittent failures under load | REST timeouts / low connection pool | increase timeout/pool + backend performance |

---

## 9) Recommended Production Hardening

- Use unique long shared secrets per router/site.
- Restrict UDP 1812/1813 to known MikroTik source IPs only.
- Keep FreeRADIUS + RouterOS time synchronized (NTP).
- Keep `Acct-Interim-Interval` at 300s for better usage telemetry.
- Monitor FreeRADIUS logs and CAIWAVE `/radius/*` response latency.

---

## 10) If You Need a Clean Baseline Re-Test

1. Create one new test voucher/session in CAIWAVE.
2. Test with `radtest` from FreeRADIUS host.
3. Test hotspot login from one client device.
4. Confirm accounting `Start` and `Stop` hit CAIWAVE.
5. Only then apply advanced queues/shaping/custom scripts.

This avoids chasing multiple failures at once.
