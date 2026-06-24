def build_mikrotik_script(router: dict):
    name = router.get("name", "mikrotik-router")
    wan = router.get("wan_interface", "ether1")
    lans = router.get("lan_interfaces", ["ether2"])
    bridge = router.get("bridge_name") or "bridge-hotspot"
    hotspot_cidr = router.get("hotspot_cidr", "10.10.0.1/24")
    dhcp_pool = router.get("dhcp_pool", "dhcp_pool")
    dns_name = router.get("dns_name", "caiwave.local")
    radius_secret = router.get("radius_secret", "caiwave_secret")

    lan_ports = "\n".join(
        [f"/interface bridge port add bridge={bridge} interface={i}" for i in lans]
    )

    script = f"""
# ===== CAIWAVE AUTO PROVISIONING =====
# Router: {name}

# 1. Create Bridge
/interface bridge add name={bridge}

# 2. Add LAN ports to bridge
{lan_ports}

# 3. WAN NAT
/ip firewall nat add chain=srcnat out-interface={wan} action=masquerade

# 4. IP Addressing
/ip address add address={hotspot_cidr} interface={bridge}

# 5. DHCP Pool
/ip pool add name={dhcp_pool} ranges={hotspot_cidr}

/ip dhcp-server add name=dhcp1 interface={bridge} address-pool={dhcp_pool} disabled=no

/ip dhcp-server network add address={hotspot_cidr} gateway={hotspot_cidr.split('/')[0]} dns-server=8.8.8.8

# 6. DNS
/ip dns set servers=8.8.8.8,1.1.1.1 allow-remote-requests=yes

# 7. Hotspot Setup
/ip hotspot setup interface={bridge} address-pool={dhcp_pool} dns-name={dns_name}

# 8. RADIUS
/radius add service=hotspot address=127.0.0.1 secret={radius_secret}

/ip hotspot profile set [find default=yes] use-radius=yes

# ===== END =====
"""
    return script
