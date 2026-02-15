import { useState } from "react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { toast } from "sonner";
import {
  Copy,
  CheckCircle,
  Server,
  Wifi,
  Shield,
  ArrowRight,
  Terminal,
  FileText,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const SetupWizard = () => {
  const [step, setStep] = useState(1);
  const [copied, setCopied] = useState({});
  const [config, setConfig] = useState({
    // CAIWAVE Config (pre-filled)
    caiwave_domain: "www.caiwave.com",
    caiwave_api: "https://www.caiwave.com/api",
    
    // FreeRADIUS Server Config
    radius_server_ip: "",
    radius_secret: generateSecret(),
    radius_auth_port: "1812",
    radius_acct_port: "1813",
    
    // MikroTik Config
    mikrotik_ip: "",
    hotspot_interface: "wlan1",
    hotspot_pool: "192.168.88.10-192.168.88.254",
    hotspot_gateway: "192.168.88.1",
    hotspot_ssid: "CAIWAVE_WiFi",
    
    // Hotspot ID (for portal redirect)
    hotspot_id: "",
  });
  
  const [expandedSections, setExpandedSections] = useState({
    freeradius: true,
    mikrotik: true,
  });

  function generateSecret() {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 32; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied({ ...copied, [key]: true });
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied({ ...copied, [key]: false }), 2000);
  };

  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section]
    });
  };

  // Generate FreeRADIUS REST module config
  const getFreeRadiusRestConfig = () => `# ============================================================
# CAIWAVE FreeRADIUS REST Module Configuration
# Generated: ${new Date().toISOString().split('T')[0]}
# ============================================================
# File: /etc/freeradius/3.0/mods-available/rest

rest {
    # CAIWAVE API endpoint
    connect_uri = "${config.caiwave_api}"
    
    # Connection settings
    connect_timeout = 4.0
    http_timeout = 4.0
    
    # TLS settings (for HTTPS)
    tls {
        verify_cert = no
        verify_cert_cn = no
    }
    
    # ========================================
    # AUTHORIZATION - Check if user can login
    # ========================================
    authorize {
        uri = "\${..connect_uri}/radius/authorize"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "password": "%{User-Password}", "nas_ip": "%{NAS-IP-Address}", "called_station": "%{Called-Station-Id}"}'
        tls = \${..tls}
    }
    
    # ========================================
    # ACCOUNTING - Track session start/stop
    # ========================================
    accounting {
        uri = "\${..connect_uri}/radius/accounting"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "session_id": "%{Acct-Session-Id}", "status_type": "%{Acct-Status-Type}", "nas_ip": "%{NAS-IP-Address}", "session_time": "%{Acct-Session-Time}", "input_octets": "%{Acct-Input-Octets}", "output_octets": "%{Acct-Output-Octets}"}'
        tls = \${..tls}
    }
    
    # ========================================
    # POST-AUTH - Log authentication results
    # ========================================
    post-auth {
        uri = "\${..connect_uri}/radius/post-auth"
        method = 'post'
        body = 'json'
        data = '{"username": "%{User-Name}", "nas_ip": "%{NAS-IP-Address}", "result": "%{reply:Packet-Type}"}'
        tls = \${..tls}
    }
}`;

  // Generate FreeRADIUS clients.conf entry
  const getFreeRadiusClientsConfig = () => `# ============================================================
# CAIWAVE MikroTik Client Configuration
# Add this to: /etc/freeradius/3.0/clients.conf
# ============================================================

client mikrotik_caiwave {
    ipaddr = ${config.mikrotik_ip || "YOUR_MIKROTIK_IP"}
    secret = ${config.radius_secret}
    nastype = mikrotik
    shortname = caiwave_hotspot
}`;

  // Generate FreeRADIUS site config
  const getFreeRadiusSiteConfig = () => `# ============================================================
# CAIWAVE FreeRADIUS Default Site Configuration
# File: /etc/freeradius/3.0/sites-available/default
# ============================================================
# Find and modify these sections in the default site:

# In the 'authorize' section:
authorize {
    rest
    if (ok) {
        update control {
            Auth-Type := rest
        }
    }
}

# In the 'authenticate' section:
authenticate {
    Auth-Type rest {
        rest
    }
}

# In the 'accounting' section:
accounting {
    rest
}

# In the 'post-auth' section:
post-auth {
    rest
}`;

  // Generate FreeRADIUS install script
  const getFreeRadiusInstallScript = () => `#!/bin/bash
# ============================================================
# CAIWAVE FreeRADIUS Auto-Install Script
# Run this on your Ubuntu/Debian FreeRADIUS server
# ============================================================

echo "=========================================="
echo "CAIWAVE FreeRADIUS Setup Script"
echo "=========================================="

# Update system
echo "[1/6] Updating system..."
sudo apt update

# Install FreeRADIUS with REST module
echo "[2/6] Installing FreeRADIUS..."
sudo apt install -y freeradius freeradius-rest freeradius-utils

# Backup original configs
echo "[3/6] Backing up original configs..."
sudo cp /etc/freeradius/3.0/mods-available/rest /etc/freeradius/3.0/mods-available/rest.backup
sudo cp /etc/freeradius/3.0/sites-available/default /etc/freeradius/3.0/sites-available/default.backup
sudo cp /etc/freeradius/3.0/clients.conf /etc/freeradius/3.0/clients.conf.backup

# Create REST module config
echo "[4/6] Configuring REST module..."
sudo tee /etc/freeradius/3.0/mods-available/rest > /dev/null << 'RESTEOF'
${getFreeRadiusRestConfig()}
RESTEOF

# Enable REST module
cd /etc/freeradius/3.0/mods-enabled/
sudo ln -sf ../mods-available/rest rest

# Add MikroTik client
echo "[5/6] Adding MikroTik client..."
sudo tee -a /etc/freeradius/3.0/clients.conf > /dev/null << 'CLIENTEOF'

${getFreeRadiusClientsConfig()}
CLIENTEOF

# Update default site
echo "[6/6] Updating default site..."
# Note: This requires manual editing - see instructions below

echo ""
echo "=========================================="
echo "INSTALLATION COMPLETE!"
echo "=========================================="
echo ""
echo "IMPORTANT: You need to manually edit the default site:"
echo "  sudo nano /etc/freeradius/3.0/sites-available/default"
echo ""
echo "Replace the authorize, authenticate, accounting, and post-auth"
echo "sections as shown in the documentation."
echo ""
echo "Then restart FreeRADIUS:"
echo "  sudo systemctl restart freeradius"
echo ""
echo "To test in debug mode:"
echo "  sudo systemctl stop freeradius"
echo "  sudo freeradius -X"
echo ""
echo "RADIUS Secret: ${config.radius_secret}"
echo "=========================================="`;

  // Generate MikroTik script
  const getMikroTikScript = () => `# ============================================================
# CAIWAVE MikroTik Hotspot Configuration Script
# Generated: ${new Date().toISOString().split('T')[0]}
# ============================================================
# Paste this entire script into MikroTik terminal (WinBox > New Terminal)
# ============================================================

:log info "Starting CAIWAVE Hotspot Configuration..."

# ==========================================
# STEP 1: Configure Wireless Interface
# ==========================================
/interface wireless
set ${config.hotspot_interface} mode=ap-bridge ssid="${config.hotspot_ssid}" \\
    disabled=no band=2ghz-b/g/n channel-width=20/40mhz-Ce

:log info "Wireless interface configured"

# ==========================================
# STEP 2: Configure IP Address
# ==========================================
/ip address
:foreach addr in=[find interface=${config.hotspot_interface}] do={
    remove $addr
}
add address=${config.hotspot_gateway}/24 interface=${config.hotspot_interface}

:log info "IP address configured"

# ==========================================
# STEP 3: Configure DHCP Server
# ==========================================
# Create IP Pool
/ip pool
:foreach pool in=[find name="hotspot-pool"] do={
    remove $pool
}
add name=hotspot-pool ranges=${config.hotspot_pool}

# Create DHCP Server
/ip dhcp-server
:foreach dhcp in=[find interface=${config.hotspot_interface}] do={
    remove $dhcp
}
add name=hotspot-dhcp interface=${config.hotspot_interface} address-pool=hotspot-pool disabled=no

# DHCP Network
/ip dhcp-server network
:foreach net in=[find gateway=${config.hotspot_gateway}] do={
    remove $net
}
add address=${config.hotspot_gateway.split('.').slice(0,3).join('.')}.0/24 gateway=${config.hotspot_gateway} dns-server=8.8.8.8,8.8.4.4

:log info "DHCP server configured"

# ==========================================
# STEP 4: Configure RADIUS Server
# ==========================================
/radius
:foreach r in=[find comment~"CAIWAVE"] do={
    remove $r
}
add address=${config.radius_server_ip || "YOUR_RADIUS_SERVER_IP"} secret="${config.radius_secret}" \\
    service=hotspot authentication-port=${config.radius_auth_port} accounting-port=${config.radius_acct_port} \\
    timeout=3s comment="CAIWAVE RADIUS Server"

/radius incoming
set accept=yes port=3799

:log info "RADIUS server configured"

# ==========================================
# STEP 5: Configure Hotspot Profile
# ==========================================
/ip hotspot profile
:foreach prof in=[find name="caiwave-profile"] do={
    remove $prof
}
add name=caiwave-profile \\
    hotspot-address=${config.hotspot_gateway} \\
    dns-name="hotspot.caiwave.com" \\
    html-directory=hotspot \\
    http-cookie-lifetime=1d \\
    login-by=http-chap,http-pap \\
    use-radius=yes \\
    radius-accounting=yes \\
    radius-interim-update=5m

:log info "Hotspot profile configured"

# ==========================================
# STEP 6: Configure Hotspot Server
# ==========================================
/ip hotspot
:foreach hs in=[find interface=${config.hotspot_interface}] do={
    remove $hs
}
add name=caiwave-hotspot interface=${config.hotspot_interface} \\
    address-pool=hotspot-pool profile=caiwave-profile disabled=no

:log info "Hotspot server configured"

# ==========================================
# STEP 7: Configure Walled Garden
# ==========================================
# Allow access to CAIWAVE and payment services without login
/ip hotspot walled-garden ip
:foreach wg in=[find comment~"CAIWAVE"] do={
    remove $wg
}
add dst-host=${config.caiwave_domain} action=accept comment="CAIWAVE Portal"
add dst-host=*.${config.caiwave_domain} action=accept comment="CAIWAVE Subdomains"
add dst-host=*.paystack.com action=accept comment="CAIWAVE Paystack"
add dst-host=*.paystack.co action=accept comment="CAIWAVE Paystack CO"
add dst-host=*.safaricom.co.ke action=accept comment="CAIWAVE M-Pesa"

:log info "Walled garden configured"

# ==========================================
# STEP 8: Configure NAT (Masquerade)
# ==========================================
/ip firewall nat
:foreach nat in=[find comment~"CAIWAVE"] do={
    remove $nat
}
add chain=srcnat out-interface=ether1 action=masquerade comment="CAIWAVE NAT"

:log info "NAT configured"

# ==========================================
# STEP 9: Create Redirect Login Page
# ==========================================
# This creates a simple redirect to CAIWAVE portal
/file
:if ([:len [find name="hotspot/login.html"]] > 0) do={
    remove [find name="hotspot/login.html"]
}

:log info "Creating login redirect page..."

# Create the redirect HTML
:local loginhtml "<!DOCTYPE html>\\r\\n<html>\\r\\n<head>\\r\\n<meta http-equiv=\\"refresh\\" content=\\"0;url=https://${config.caiwave_domain}/portal/${config.hotspot_id || 'YOUR_HOTSPOT_ID'}\\">\\r\\n<title>Redirecting...</title>\\r\\n</head>\\r\\n<body>\\r\\n<p>Redirecting to WiFi Portal...</p>\\r\\n</body>\\r\\n</html>"

# Note: You may need to manually create the login.html file
# Download from: https://${config.caiwave_domain}/hotspot-templates/login.html

:log info "=========================================="
:log info "CAIWAVE HOTSPOT CONFIGURATION COMPLETE!"
:log info "=========================================="
:log info "RADIUS Server: ${config.radius_server_ip || 'YOUR_RADIUS_SERVER_IP'}"
:log info "RADIUS Secret: ${config.radius_secret}"
:log info "Hotspot SSID: ${config.hotspot_ssid}"
:log info "Portal URL: https://${config.caiwave_domain}/portal/${config.hotspot_id || 'YOUR_HOTSPOT_ID'}"
:log info "=========================================="

:put ""
:put "=========================================="
:put "CAIWAVE HOTSPOT CONFIGURATION COMPLETE!"
:put "=========================================="
:put "Next steps:"
:put "1. Verify RADIUS connection: /radius monitor 0"
:put "2. Test hotspot by connecting a device"
:put "3. Check logs: /log print where topics~\\"hotspot\\""
:put "=========================================="`;

  // Generate quick test commands
  const getTestCommands = () => `# ============================================================
# CAIWAVE Setup Verification Commands
# ============================================================

# ========== On FreeRADIUS Server ==========

# 1. Test FreeRADIUS is running
sudo systemctl status freeradius

# 2. Run in debug mode (stop service first)
sudo systemctl stop freeradius
sudo freeradius -X

# 3. Test CAIWAVE API connectivity
curl -X POST "${config.caiwave_api}/radius/authorize" \\
  -H "Content-Type: application/json" \\
  -d '{"username": "test", "password": "test", "nas_ip": "${config.mikrotik_ip || '192.168.1.1'}"}'

# Expected response: {"reply": "Access-Reject", "reply-message": "Invalid credentials..."}
# This confirms the API is reachable!

# ========== On MikroTik Router ==========

# 1. Check RADIUS connection
/radius monitor 0

# 2. Check hotspot status
/ip hotspot print

# 3. View hotspot users
/ip hotspot active print

# 4. Check logs
/log print where topics~"hotspot"
/log print where topics~"radius"

# 5. Test DNS resolution
/tool dns-lookup ${config.caiwave_domain}`;

  const downloadFile = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${filename}`);
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-white p-6" data-testid="setup-wizard">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">CAIWAVE Setup Wizard</h1>
          <p className="text-neutral-400">
            One-time setup for MikroTik + FreeRADIUS + CAIWAVE integration
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8 gap-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  step >= s ? "bg-blue-600" : "bg-neutral-800"
                }`}
              >
                {step > s ? <CheckCircle className="w-5 h-5" /> : s}
              </div>
              {s < 3 && (
                <div className={`w-16 h-1 mx-2 ${step > s ? "bg-blue-600" : "bg-neutral-800"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Labels */}
        <div className="flex justify-center mb-8 gap-8 text-sm">
          <span className={step >= 1 ? "text-blue-400" : "text-neutral-500"}>Configuration</span>
          <span className={step >= 2 ? "text-blue-400" : "text-neutral-500"}>FreeRADIUS Setup</span>
          <span className={step >= 3 ? "text-blue-400" : "text-neutral-500"}>MikroTik Setup</span>
        </div>

        {/* Step 1: Configuration */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="bg-neutral-900 rounded-xl p-6 border border-neutral-800">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Server className="w-5 h-5 text-blue-400" />
                Server Configuration
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">FreeRADIUS Server IP *</label>
                  <Input
                    value={config.radius_server_ip}
                    onChange={(e) => setConfig({...config, radius_server_ip: e.target.value})}
                    placeholder="e.g., 192.168.1.100"
                    data-testid="radius-ip-input"
                  />
                  <p className="text-xs text-neutral-500 mt-1">IP address of your FreeRADIUS server</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">RADIUS Secret</label>
                  <div className="flex gap-2">
                    <Input
                      value={config.radius_secret}
                      onChange={(e) => setConfig({...config, radius_secret: e.target.value})}
                      className="font-mono text-sm"
                      data-testid="radius-secret-input"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setConfig({...config, radius_secret: generateSecret()})}
                    >
                      New
                    </Button>
                  </div>
                  <p className="text-xs text-neutral-500 mt-1">Shared secret (auto-generated)</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">MikroTik Router IP *</label>
                  <Input
                    value={config.mikrotik_ip}
                    onChange={(e) => setConfig({...config, mikrotik_ip: e.target.value})}
                    placeholder="e.g., 192.168.1.1"
                    data-testid="mikrotik-ip-input"
                  />
                  <p className="text-xs text-neutral-500 mt-1">IP address of your MikroTik router</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Hotspot ID</label>
                  <Input
                    value={config.hotspot_id}
                    onChange={(e) => setConfig({...config, hotspot_id: e.target.value})}
                    placeholder="From your CAIWAVE dashboard"
                    data-testid="hotspot-id-input"
                  />
                  <p className="text-xs text-neutral-500 mt-1">Your hotspot ID from CAIWAVE</p>
                </div>
              </div>
            </div>

            <div className="bg-neutral-900 rounded-xl p-6 border border-neutral-800">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Wifi className="w-5 h-5 text-green-400" />
                Hotspot Configuration
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">WiFi Interface</label>
                  <Input
                    value={config.hotspot_interface}
                    onChange={(e) => setConfig({...config, hotspot_interface: e.target.value})}
                    placeholder="wlan1"
                    data-testid="interface-input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">WiFi SSID</label>
                  <Input
                    value={config.hotspot_ssid}
                    onChange={(e) => setConfig({...config, hotspot_ssid: e.target.value})}
                    placeholder="CAIWAVE_WiFi"
                    data-testid="ssid-input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">Hotspot Gateway</label>
                  <Input
                    value={config.hotspot_gateway}
                    onChange={(e) => setConfig({...config, hotspot_gateway: e.target.value})}
                    placeholder="192.168.88.1"
                    data-testid="gateway-input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-1">DHCP Pool Range</label>
                  <Input
                    value={config.hotspot_pool}
                    onChange={(e) => setConfig({...config, hotspot_pool: e.target.value})}
                    placeholder="192.168.88.10-192.168.88.254"
                    data-testid="pool-input"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setStep(2)} data-testid="next-step-btn">
                Next: FreeRADIUS Setup
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: FreeRADIUS Setup */}
        {step === 2 && (
          <div className="space-y-6">
            {/* Quick Install Option */}
            <div className="bg-blue-900/20 rounded-xl p-6 border border-blue-500/30">
              <h2 className="text-xl font-bold mb-2 flex items-center gap-2">
                <Terminal className="w-5 h-5 text-blue-400" />
                Quick Install (Recommended)
              </h2>
              <p className="text-neutral-400 mb-4">
                Download and run this script on your Ubuntu/Debian server to automatically install and configure FreeRADIUS.
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={() => downloadFile(getFreeRadiusInstallScript(), 'caiwave-freeradius-setup.sh')}
                  data-testid="download-script-btn"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Install Script
                </Button>
                <Button
                  variant="outline"
                  onClick={() => copyToClipboard(getFreeRadiusInstallScript(), 'install-script')}
                >
                  {copied['install-script'] ? <CheckCircle className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                  Copy Script
                </Button>
              </div>
            </div>

            {/* Manual Configuration */}
            <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden">
              <button
                className="w-full p-4 flex items-center justify-between hover:bg-neutral-800/50"
                onClick={() => toggleSection('freeradius')}
              >
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <FileText className="w-5 h-5 text-yellow-400" />
                  Manual Configuration Files
                </h2>
                {expandedSections.freeradius ? <ChevronUp /> : <ChevronDown />}
              </button>
              
              {expandedSections.freeradius && (
                <div className="p-4 pt-0 space-y-4">
                  {/* REST Module Config */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">1. REST Module (/etc/freeradius/3.0/mods-available/rest)</h3>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(getFreeRadiusRestConfig(), 'rest-config')}
                      >
                        {copied['rest-config'] ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </div>
                    <pre className="bg-neutral-950 p-4 rounded-lg text-xs overflow-x-auto max-h-60">
                      {getFreeRadiusRestConfig()}
                    </pre>
                  </div>

                  {/* Clients Config */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">2. Clients Config (/etc/freeradius/3.0/clients.conf)</h3>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(getFreeRadiusClientsConfig(), 'clients-config')}
                      >
                        {copied['clients-config'] ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </div>
                    <pre className="bg-neutral-950 p-4 rounded-lg text-xs overflow-x-auto">
                      {getFreeRadiusClientsConfig()}
                    </pre>
                  </div>

                  {/* Site Config */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">3. Default Site Modifications</h3>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(getFreeRadiusSiteConfig(), 'site-config')}
                      >
                        {copied['site-config'] ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </Button>
                    </div>
                    <pre className="bg-neutral-950 p-4 rounded-lg text-xs overflow-x-auto max-h-60">
                      {getFreeRadiusSiteConfig()}
                    </pre>
                  </div>
                </div>
              )}
            </div>

            {/* Commands */}
            <div className="bg-neutral-900 rounded-xl p-6 border border-neutral-800">
              <h3 className="font-bold mb-3">After Configuration - Run These Commands:</h3>
              <div className="space-y-2 font-mono text-sm">
                <div className="flex items-center gap-2">
                  <code className="bg-neutral-950 px-3 py-1 rounded flex-1">
                    cd /etc/freeradius/3.0/mods-enabled/ && sudo ln -sf ../mods-available/rest rest
                  </code>
                  <Button size="sm" variant="ghost" onClick={() => copyToClipboard('cd /etc/freeradius/3.0/mods-enabled/ && sudo ln -sf ../mods-available/rest rest', 'cmd1')}>
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <code className="bg-neutral-950 px-3 py-1 rounded flex-1">
                    sudo systemctl restart freeradius
                  </code>
                  <Button size="sm" variant="ghost" onClick={() => copyToClipboard('sudo systemctl restart freeradius', 'cmd2')}>
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button onClick={() => setStep(3)} data-testid="next-mikrotik-btn">
                Next: MikroTik Setup
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: MikroTik Setup */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="bg-green-900/20 rounded-xl p-6 border border-green-500/30">
              <h2 className="text-xl font-bold mb-2 flex items-center gap-2">
                <Wifi className="w-5 h-5 text-green-400" />
                MikroTik Configuration Script
              </h2>
              <p className="text-neutral-400 mb-4">
                Copy this script and paste it into your MikroTik terminal (WinBox → New Terminal).
                The script will automatically configure your hotspot.
              </p>
              <div className="flex gap-2 mb-4">
                <Button
                  onClick={() => downloadFile(getMikroTikScript(), 'caiwave-mikrotik-config.rsc')}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Script
                </Button>
                <Button
                  variant="outline"
                  onClick={() => copyToClipboard(getMikroTikScript(), 'mikrotik-script')}
                >
                  {copied['mikrotik-script'] ? <CheckCircle className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                  Copy Script
                </Button>
              </div>
            </div>

            {/* MikroTik Script */}
            <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden">
              <button
                className="w-full p-4 flex items-center justify-between hover:bg-neutral-800/50"
                onClick={() => toggleSection('mikrotik')}
              >
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-green-400" />
                  View Full MikroTik Script
                </h2>
                {expandedSections.mikrotik ? <ChevronUp /> : <ChevronDown />}
              </button>
              
              {expandedSections.mikrotik && (
                <div className="p-4 pt-0">
                  <pre className="bg-neutral-950 p-4 rounded-lg text-xs overflow-x-auto max-h-96">
                    {getMikroTikScript()}
                  </pre>
                </div>
              )}
            </div>

            {/* Test Commands */}
            <div className="bg-neutral-900 rounded-xl p-6 border border-neutral-800">
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <Shield className="w-5 h-5 text-yellow-400" />
                Verification Commands
              </h3>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-neutral-400">Commands to verify your setup is working</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(getTestCommands(), 'test-commands')}
                >
                  {copied['test-commands'] ? <CheckCircle className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                  Copy All
                </Button>
              </div>
              <pre className="bg-neutral-950 p-4 rounded-lg text-xs overflow-x-auto max-h-60">
                {getTestCommands()}
              </pre>
            </div>

            {/* Summary */}
            <div className="bg-blue-900/20 rounded-xl p-6 border border-blue-500/30">
              <h3 className="font-bold mb-3">Configuration Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-neutral-400">CAIWAVE Domain:</span>
                  <p className="font-mono">{config.caiwave_domain}</p>
                </div>
                <div>
                  <span className="text-neutral-400">RADIUS Server:</span>
                  <p className="font-mono">{config.radius_server_ip || "Not set"}</p>
                </div>
                <div>
                  <span className="text-neutral-400">RADIUS Secret:</span>
                  <p className="font-mono text-xs">{config.radius_secret}</p>
                </div>
                <div>
                  <span className="text-neutral-400">MikroTik IP:</span>
                  <p className="font-mono">{config.mikrotik_ip || "Not set"}</p>
                </div>
                <div>
                  <span className="text-neutral-400">Hotspot SSID:</span>
                  <p className="font-mono">{config.hotspot_ssid}</p>
                </div>
                <div>
                  <span className="text-neutral-400">Portal URL:</span>
                  <p className="font-mono text-xs">https://{config.caiwave_domain}/portal/{config.hotspot_id || "ID"}</p>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>
                Back
              </Button>
              <Button
                onClick={() => {
                  toast.success("Setup complete! Follow the instructions to configure your devices.");
                }}
                data-testid="finish-setup-btn"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Finish Setup
              </Button>
            </div>
          </div>
        )}

        {/* Help Links */}
        <div className="mt-8 text-center text-sm text-neutral-500">
          <p>Need help? Check out our documentation or contact support.</p>
          <div className="flex justify-center gap-4 mt-2">
            <a href="https://wiki.mikrotik.com/wiki/Manual:IP/Hotspot" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline flex items-center gap-1">
              MikroTik Docs <ExternalLink className="w-3 h-3" />
            </a>
            <a href="https://wiki.freeradius.org/guide/Getting-Started" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline flex items-center gap-1">
              FreeRADIUS Docs <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
