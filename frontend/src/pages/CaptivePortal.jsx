import { safeError } from "../utils/safeError";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { API_URL } from "../lib/utils";
import { Wifi, Clock, Zap, MessageCircle, ExternalLink, Play, ChevronRight, Phone, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import PortalHeader from "../components/portal/PortalHeader";
import QuickActions from "../components/portal/QuickActions";
import CampaignHero from "../components/portal/CampaignHero";
import FeaturedAdvertisement from "../components/portal/FeaturedAdvertisement";
import { toast, Toaster } from "sonner";


// Format phone number for WhatsApp
const formatWhatsApp = (phone) => {
  if (!phone) return null;
  let cleaned = phone.replace(/\D/g, '');
  if (cleaned.startsWith('0')) cleaned = '254' + cleaned.slice(1);
  if (!cleaned.startsWith('254')) cleaned = '254' + cleaned;
  return cleaned;
};

const CaptivePortal = () => {
  const { hotspotId: routeHotspotId } = useParams();
  const [hotspotId, setHotspotId] = useState(null);
  const [clientMac, setClientMac] = useState("");
  const [clientIp, setClientIp] = useState("");
  const [mikrotikLoginUrl, setMikrotikLoginUrl] = useState("");
  const [originalDestination, setOriginalDestination] = useState("");
  const [hotspot, setHotspot] = useState(null);
  const [packages, setPackages] = useState([]);
  const [ads, setAds] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [streams, setStreams] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [voucherCode, setVoucherCode] = useState("");
  const [redeemingVoucher, setRedeemingVoucher] = useState(false);
  const [currentAdIndex, setCurrentAdIndex] = useState(0);
  const [videoReady, setVideoReady] = useState(false);

  useEffect(() => {
  // Get hotspot ID and client info from route params or MikroTik query params
    const params = new URLSearchParams(window.location.search);
    const hid = routeHotspotId || params.get("hotspot") || params.get("h") || params.get("id");
    const mac = params.get("mac") || params.get("user_mac") || "";
    const ip = params.get("ip") || params.get("user_ip") || "";
    const loginUrl =
      params.get("login_url") ||
      params.get("link-login-only") ||
      params.get("link_login") ||
      "";
    const destination =
      params.get("dst") ||
      params.get("link-orig") ||
      "http://neverssl.com/";

    setHotspotId(hid);
    setClientMac(mac);
    setClientIp(ip);
    setMikrotikLoginUrl(loginUrl);
    setOriginalDestination(destination);

    fetchData(hid);
}, [routeHotspotId]);

  // Rotate image campaigns automatically.
  // Video campaigns advance only after the complete video has played.
  useEffect(() => {
    if (ads.length <= 1) return undefined;

    const activeAd = ads[currentAdIndex];

    if (!activeAd || activeAd.ad_type === "video") {
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      setCurrentAdIndex((current) => (current + 1) % ads.length);
    }, 6000);

    return () => window.clearTimeout(timeout);
  }, [ads, currentAdIndex]);

  useEffect(() => {
    setVideoReady(false);
  }, [currentAdIndex]);

  const showPreviousAd = () => {
    if (ads.length <= 1) return;

    setCurrentAdIndex((current) =>
      current === 0 ? ads.length - 1 : current - 1
    );
  };

  const showNextAd = () => {
    if (ads.length <= 1) return;

    setCurrentAdIndex((current) => (current + 1) % ads.length);
  };

  const fetchData = async (hid) => {
    try {
      if (hid) {
        try {
          const portalRes = await axios.get(`${API_URL}/portal/${hid}`);
          setHotspot(portalRes.data.hotspot);
          setPackages((portalRes.data.packages || []).filter((p) => p.is_active));
          setAds(portalRes.data.ads || []);
          setCampaigns(portalRes.data.campaigns || []);
        } catch (e) {
          console.log("Portal hotspot data not found, falling back to public packages/ads");

          const packagesRes = await axios.get(`${API_URL}/packages/`);
          setPackages(packagesRes.data.filter((p) => p.is_active));

          const adsRes = await axios.get(`${API_URL}/ads/active`);
          setAds(adsRes.data || []);
        }
      } else {
        const packagesRes = await axios.get(`${API_URL}/packages/`);
        setPackages(packagesRes.data.filter((p) => p.is_active));

        const adsRes = await axios.get(`${API_URL}/ads/active`);
        setAds(adsRes.data || []);
      }

      const streamsRes = await axios.get(`${API_URL}/streams/live`);
      setStreams(streamsRes.data || []);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const submitCredentialsToMikrotik = (credentials) => {
    const username = credentials?.username;
    const password = credentials?.password;

    if (!username || !password) {
      toast.error("WiFi credentials were not returned.");
      return false;
    }

    if (!mikrotikLoginUrl) {
      toast.error(
        "Payment completed, but the router login link is missing. Reconnect to the hotspot and try again."
      );
      return false;
    }

    const form = document.createElement("form");
    form.method = "POST";
    form.action = mikrotikLoginUrl;
    form.style.display = "none";

    const fields = {
      username,
      password,
      dst: originalDestination || "http://neverssl.com/",
      popup: "true"
    };

    Object.entries(fields).forEach(([name, value]) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
    return true;
  };

  const verifyPaymentUntilComplete = async (reference) => {
    const maximumAttempts = 24;
    const intervalMilliseconds = 3000;

    for (let attempt = 1; attempt <= maximumAttempts; attempt += 1) {
      await new Promise((resolve) =>
        window.setTimeout(resolve, intervalMilliseconds)
      );

      try {
        const verification = await axios.post(
          `${API_URL}/paystack/verify/${encodeURIComponent(reference)}`
        );

        if (
          verification.data?.status === "completed" &&
          verification.data?.wifi_credentials
        ) {
          return verification.data;
        }

        if (verification.data?.status === "failed") {
          throw new Error(
            verification.data?.message || "Payment verification failed"
          );
        }
      } catch (error) {
        const status = error?.response?.status;

        if (status && status >= 400 && status < 500 && status !== 408) {
          throw error;
        }
      }
    }

    throw new Error(
      "Payment confirmation is taking longer than expected. Do not pay again; reconnect and check the same transaction."
    );
  };

  const handlePurchase = async () => {
    if (!selectedPackage) {
      toast.error("Please select a package");
      return;
    }
    if (!phone || phone.length < 9) {
      toast.error("Please enter a valid phone number");
      return;
    }

    setPaying(true);
    try {
      const response = await axios.post(`${API_URL}/paystack/client/pay-wifi`, {
        hotspot_id: hotspotId || "default",
        package_id: selectedPackage.id,
        phone_number: `254${phone}`,
        email: email || `254${phone}@caiwave.com`
      });

      if (response.data.success) {
        toast.success(response.data.message || "STK Push sent! Check your phone.");

        const reference = response.data.reference;
        if (!reference) {
          throw new Error("Payment reference was not returned.");
        }

        const completedPayment = await verifyPaymentUntilComplete(reference);
        toast.success("Payment confirmed. Connecting you to WiFi…");

        submitCredentialsToMikrotik(
          completedPayment.wifi_credentials
        );
      } else {
        toast.error(response.data.message || "Payment failed");
      }
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setPaying(false);
    }
  };

  const handleVoucherRedemption = async () => {
    const normalizedCode = voucherCode.trim().toUpperCase();

    if (!normalizedCode) {
      toast.error("Please enter your voucher code.");
      return;
    }

    if (!hotspotId) {
      toast.error(
        "This hotspot could not be identified. Reconnect to the WiFi and open the portal again."
      );
      return;
    }

    if (!mikrotikLoginUrl) {
      toast.error(
        "The router login link is missing. Reconnect to the hotspot before redeeming your voucher."
      );
      return;
    }

    setRedeemingVoucher(true);

    try {
      const response = await axios.post(
        `${API_URL}/vouchers/redeem/${encodeURIComponent(normalizedCode)}`,
        null,
        {
          params: {
            hotspot_id: hotspotId,
            user_mac: clientMac || undefined,
            user_ip: clientIp || undefined,
          },
        }
      );

      const credentials = response.data?.wifi_credentials;

      if (
        response.data?.status !== "completed" ||
        !credentials
      ) {
        throw new Error(
          response.data?.message ||
            "The voucher was accepted, but WiFi credentials were not returned."
        );
      }

      toast.success("Voucher accepted. Connecting you to WiFi…");
      setVoucherCode("");

      submitCredentialsToMikrotik(credentials);
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setRedeemingVoucher(false);
    }
  };

  // Handle "Watch Ad for Free WiFi" - gives 15 minutes free (MAX 2 per day)
  const [gettingFreeWifi, setGettingFreeWifi] = useState(false);
  const [freeSession, setFreeSession] = useState(null);
  const [freeSessionStatus, setFreeSessionStatus] = useState({ free_sessions_remaining: 2, can_get_free: true });

  // Check free session status on load
  useEffect(() => {
    const checkFreeStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/portal/free-session-status`, {
          params: {
            hotspot_id: hotspotId || "demo",
            user_mac: clientMac ,
            user_ip: clientIp
          }
        });
        setFreeSessionStatus(response.data);
      } catch (error) {
        console.log("Could not check free session status");
      }
    };
    if (hotspotId || true) checkFreeStatus();
  }, [hotspotId, clientMac, clientIp]);

  const handleGetFreeWifi = async () => {
    if (!hasRealAd) {
      toast.error("No sponsor advert is active yet. Free WiFi activation will be connected after ads are configured.");
      return;
    }

    if (!freeSessionStatus.can_get_free) {
      toast.error("You've used all your free ad sessions. Please purchase a package.");
      return;
    }

    setGettingFreeWifi(true);
    try {
      const response = await axios.post(`${API_URL}/portal/free-session`, null, {
        params: {
          hotspot_id: hotspotId || "demo",
          ad_id: currentAd.id,
          user_mac: clientMac ,
          user_ip: clientIp
        }
      });

      if (response.data.session_id) {
        setFreeSession(response.data);
        setFreeSessionStatus({
          free_sessions_used: response.data.free_sessions_used,
          free_sessions_remaining: response.data.free_sessions_remaining,
          can_get_free: response.data.free_sessions_remaining > 0
        });
        toast.success(`🎉 You got ${response.data.duration_minutes} minutes free WiFi!`);

        // Track ad click before handing the browser back to MikroTik.
        await axios.post(`${API_URL}/ads/${currentAd.id}/click`).catch(() => {});

        const submitted = submitCredentialsToMikrotik(response.data);

        if (!submitted) {
          throw new Error(
            "Free WiFi was activated, but the router login could not be completed."
          );
        }
      }
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setGettingFreeWifi(false);
    }
  };

  const fallbackAd = {
    id: "caiwave-placeholder-ad",
    title: "Advertise Here on CAIWAVE WiFi",
    ad_type: "image",
    media_url: null,
    whatsapp_number: "",
    click_url: ""
  };

  const currentAd = ads[currentAdIndex] || fallbackAd;
  const hasRealAd = ads.length > 0;

  const sponsorPlaceholders = [
    {
      id: "sponsor-placeholder-1",
      title: "Local Business Promotion",
      description: "Promote offers to nearby CAIWAVE WiFi customers.",
      symbol: "🏪"
    },
    {
      id: "sponsor-placeholder-2",
      title: "Shop & Service Offers",
      description: "Show products, services and special discounts.",
      symbol: "🛍️"
    },
    {
      id: "sponsor-placeholder-3",
      title: "Events & Announcements",
      description: "Reach your local audience directly.",
      symbol: "📣"
    },
    {
      id: "sponsor-placeholder-4",
      title: "Your Business Here",
      description: "Reserve a sponsored campaign placement.",
      symbol: "⭐"
    }
  ];

  const secondaryAds = ads
    .filter((_, index) => index !== currentAdIndex)
    .slice(0, 4);

  const sponsorCards =
    secondaryAds.length > 0 ? secondaryAds : sponsorPlaceholders;
  const featuredCampaign = campaigns[0] || null;
  const baseUrl = API_URL.replace('/api', '');

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-neutral-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Toaster theme="dark" richColors />

      <PortalHeader hotspot={hotspot} />

      <QuickActions />

      <main className="max-w-4xl mx-auto p-4 space-y-6">

        <CampaignHero
          campaign={featuredCampaign}
          baseUrl={baseUrl}
        />

        <FeaturedAdvertisement
          currentAd={currentAd}
          ads={ads}
          baseUrl={baseUrl}
          videoReady={videoReady}
          setVideoReady={setVideoReady}
          currentAdIndex={currentAdIndex}
          setCurrentAdIndex={setCurrentAdIndex}
          showPreviousAd={showPreviousAd}
          showNextAd={showNextAd}
          hasRealAd={hasRealAd}
          formatWhatsApp={formatWhatsApp}
        />

        {/* WiFi Packages */}
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4">
          <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            {freeSession ? "Need More Time? Upgrade!" : "Choose Your Package"}
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {packages.map((pkg) => (
              <button
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  selectedPackage?.id === pkg.id
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-neutral-700 bg-neutral-800 hover:border-neutral-600'
                }`}
              >
                <div className="font-bold text-xl text-green-400">
                  KES {pkg.price}
                </div>
                <div className="text-white font-medium">{pkg.name}</div>
                <div className="text-neutral-400 text-sm flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3" />
                  {pkg.duration_minutes >= 60
                    ? `${Math.floor(pkg.duration_minutes / 60)}h ${pkg.duration_minutes % 60}m`
                    : `${pkg.duration_minutes} min`
                  }
                </div>
                {pkg.speed_mbps && (
                  <div className="text-neutral-500 text-xs mt-1">
                    Up to {pkg.speed_mbps} Mbps
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Phone Input */}
          {selectedPackage && (
            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">M-Pesa Phone Number</label>
                <div className="flex items-center bg-neutral-800 border border-neutral-700 rounded-lg">
                  <span className="px-3 text-neutral-500">+254</span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 9))}
                    className="flex-1 bg-transparent px-2 py-3 focus:outline-none"
                    placeholder="7XXXXXXXX"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-neutral-400 mb-1">Email (optional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="your@email.com"
                />
              </div>

              <Button
                onClick={handlePurchase}
                disabled={paying || !phone}
                className="w-full py-6 text-lg bg-green-600 hover:bg-green-700"
              >
                {paying ? (
                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Phone className="w-5 h-5 mr-2" />
                    Pay KES {selectedPackage.price} via M-Pesa
                  </>
                )}
              </Button>

              <p className="text-center text-neutral-500 text-sm">
                You'll receive a payment prompt on your phone
              </p>
            </div>
          )}
        </div>

        {/* Free WiFi Section - After watching ad */}
        {!freeSession && (
          <div className={`rounded-xl border p-5 ${
            freeSessionStatus.can_get_free
              ? "bg-gradient-to-br from-green-950/80 to-emerald-900/50 border-green-700/50"
              : "bg-gradient-to-br from-orange-950/80 to-red-900/50 border-orange-700/50"
          }`}>
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex-1">
                {freeSessionStatus.can_get_free ? (
                  <>
                    <h3 className="font-semibold text-lg text-green-400 flex items-center gap-2">
                      <Wifi className="w-5 h-5" />
                      Get 15 Minutes FREE WiFi!
                    </h3>
                    <p className="text-green-300/70 text-sm mt-1">
                      Watch the ad above and tap to get free internet •
                      <span className="text-yellow-400 font-medium ml-1">
                        {freeSessionStatus.free_sessions_remaining} free {freeSessionStatus.free_sessions_remaining === 1 ? 'session' : 'sessions'} remaining
                      </span>
                    </p>
                  </>
                ) : (
                  <>
                    <h3 className="font-semibold text-lg text-orange-400 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Free Sessions Used Up
                    </h3>
                    <p className="text-orange-300/70 text-sm mt-1">
                      You've watched 2 ads today. Purchase a package below to continue browsing!
                    </p>
                  </>
                )}
              </div>
              {freeSessionStatus.can_get_free ? (
                <Button
                  onClick={handleGetFreeWifi}
                  disabled={gettingFreeWifi || !hasRealAd}
                  className="w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white px-6 py-3"
                >
                  {gettingFreeWifi ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Play className="w-5 h-5 mr-2" />
                      {hasRealAd ? `Get Free WiFi (${freeSessionStatus.free_sessions_remaining} left)` : "Free WiFi Coming Soon"}
                    </>
                  )}
                </Button>
              ) : (
                <div className="text-center">
                  <p className="text-orange-400 text-sm font-medium">👇 Choose a package below</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Free Session Credentials - Show after getting free WiFi */}
        {freeSession && (
          <div className="bg-gradient-to-r from-blue-900/50 to-indigo-900/50 rounded-xl border border-blue-700/50 p-6">
            <div className="text-center mb-4">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Wifi className="w-8 h-8 text-green-400" />
              </div>
              <h3 className="font-bold text-xl text-green-400">🎉 You're Connected!</h3>
              <p className="text-neutral-300 mt-1">Enjoy {freeSession.duration_minutes} minutes of free WiFi</p>
            </div>

            <div className="bg-neutral-900/50 rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-neutral-400">Username:</span>
                <code className="bg-neutral-800 px-3 py-1 rounded text-green-400 font-mono">
                  {freeSession.username}
                </code>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-neutral-400">Password:</span>
                <code className="bg-neutral-800 px-3 py-1 rounded text-green-400 font-mono">
                  {freeSession.password}
                </code>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-neutral-400">Expires:</span>
                <span className="text-yellow-400">
                  {new Date(freeSession.expires_at).toLocaleTimeString()}
                </span>
              </div>
            </div>

            <div className="mt-4 text-center">
              {freeSessionStatus.can_get_free ? (
                <>
                  <p className="text-sm text-neutral-400">
                    Want more time? Watch another ad ({freeSessionStatus.free_sessions_remaining} left) or purchase a package!
                  </p>
                  <Button
                    onClick={() => setFreeSession(null)}
                    variant="outline"
                    className="mt-2"
                  >
                    Watch Another Ad
                  </Button>
                </>
              ) : (
                <p className="text-sm text-orange-400">
                  You've used all free ad sessions. Purchase a package below for more time!
                </p>
              )}
            </div>
          </div>
        )}

        {/* Voucher Access */}
        <div className="rounded-xl border border-blue-700/50 bg-gradient-to-br from-blue-950/80 to-indigo-950/60 p-5">
          <div className="mb-4">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-blue-300">
              <Wifi className="h-5 w-5" />
              Have a Voucher?
            </h2>
            <p className="mt-1 text-sm text-neutral-400">
              Enter your CAIWAVE voucher code to connect without making a payment.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={voucherCode}
              onChange={(event) =>
                setVoucherCode(
                  event.target.value
                    .toUpperCase()
                    .replace(/[^A-Z0-9-]/g, "")
                    .slice(0, 32)
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !redeemingVoucher
                ) {
                  handleVoucherRedemption();
                }
              }}
              autoComplete="off"
              spellCheck={false}
              placeholder="Enter voucher code"
              className="min-w-0 flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-3 font-mono uppercase tracking-wider text-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30"
            />

            <Button
              type="button"
              onClick={handleVoucherRedemption}
              disabled={
                redeemingVoucher ||
                !voucherCode.trim()
              }
              className="bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 sm:w-auto"
            >
              {redeemingVoucher ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  <Wifi className="mr-2 h-5 w-5" />
                  Redeem Voucher
                </>
              )}
            </Button>
          </div>

          <p className="mt-3 text-xs text-neutral-500">
            Each voucher can only be redeemed once and is valid for its assigned hotspot.
          </p>
        </div>

        {/* Live Streams Preview */}
        {streams.length > 0 && (
          <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4">
            <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Play className="w-5 h-5 text-red-500" />
              CAIWAVE TV - Live Now
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {streams.slice(0, 3).map((stream) => (
                <div key={stream.id} className="relative rounded-lg overflow-hidden bg-neutral-800">
                  {stream.thumbnail_url ? (
                    <img
                      src={stream.thumbnail_url}
                      alt={stream.name}
                      className="w-full aspect-video object-cover"
                    />
                  ) : (
                    <div className="w-full aspect-video bg-gradient-to-br from-red-900 to-purple-900 flex items-center justify-center">
                      <Play className="w-8 h-8" />
                    </div>
                  )}
                  <div className="absolute top-2 left-2 px-2 py-0.5 bg-red-600 text-white text-xs font-bold rounded">
                    LIVE
                  </div>
                  <div className="p-2">
                    <div className="font-medium text-sm truncate">{stream.name}</div>
                    <div
                      className={`mt-1 text-xs font-semibold ${
                        stream.access_type === "free"
                          ? "text-green-400"
                          : "text-yellow-400"
                      }`}
                    >
                      {stream.access_type === "free"
                        ? "Free to watch"
                        : `KES ${stream.price || 0} access`}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-sm">
              {streams.some((stream) => stream.access_type === "free") && (
                <span className="rounded-full border border-green-500/30 bg-green-500/10 px-3 py-1 font-medium text-green-300">
                  Free streams are free to watch
                </span>
              )}

              {streams.some((stream) => stream.access_type === "paid") && (
                <span className="rounded-full border border-yellow-500/30 bg-yellow-500/10 px-3 py-1 font-medium text-yellow-300">
                  Paid streams show their access price
                </span>
              )}
            </div>
          </div>
        )}

        {/* Sponsored Campaigns Carousel */}
        <section className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-purple-400">
                Advertising Marketplace
              </p>

              <h2 className="mt-1 text-lg font-semibold text-white">
                Sponsored Campaigns
              </h2>

              <p className="mt-1 text-sm text-neutral-400">
                Discover offers, services and promotions from local businesses.
              </p>
            </div>

            <span className="shrink-0 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-medium text-purple-300">
              Swipe
            </span>
          </div>

          <div
            className="-mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            style={{ msOverflowStyle: "none" }}
          >
            {sponsorCards.map((ad, index) => {
              const isPlaceholder =
                ad.id?.startsWith("sponsor-placeholder");

              return (
                <article
                  key={ad.id || index}
                  className="min-w-[78%] snap-start overflow-hidden rounded-xl border border-neutral-700 bg-neutral-800 sm:min-w-[46%] md:min-w-[31%]"
                >
                  <div className="relative aspect-video overflow-hidden bg-gradient-to-br from-purple-950 via-indigo-900 to-blue-900">
                    {!isPlaceholder && ad.media_url ? (
                      <img
                        src={`${baseUrl}${ad.media_url}`}
                        alt={ad.title}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center p-6 text-center">
                        <div>
                          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl border border-white/20 bg-white/10">
                            <span className="text-2xl" aria-hidden="true">
                              {ad.symbol || "⭐"}
                            </span>
                          </div>

                          <p className="text-sm font-semibold text-white">
                            Sponsored Placement
                          </p>
                        </div>
                      </div>
                    )}

                    <span className="absolute left-2 top-2 rounded-full border border-white/10 bg-black/50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
                      Sponsor
                    </span>
                  </div>

                  <div className="p-3">
                    <h3 className="truncate font-semibold text-white">
                      {ad.title}
                    </h3>

                    <p className="mt-1 text-sm text-neutral-400">
                      {ad.description ||
                        "View this sponsored campaign on CAIWAVE WiFi."}
                    </p>

                    {!isPlaceholder && (
                      <div className="mt-3 flex flex-wrap gap-3">
                        {ad.whatsapp_number && (
                          <a
                            href={`https://wa.me/${formatWhatsApp(ad.whatsapp_number)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-sm font-medium text-green-400"
                          >
                            <MessageCircle className="h-4 w-4" />
                            WhatsApp
                          </a>
                        )}

                        {ad.click_url && (
                          <a
                            href={ad.click_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-sm font-medium text-blue-400"
                          >
                            <ExternalLink className="h-4 w-4" />
                            View offer
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </article>
              );
            })}
          </div>

          <div className="flex items-center justify-center gap-2 pt-2">
            {sponsorCards.map((ad, index) => (
              <span
                key={`sponsor-indicator-${ad.id || index}`}
                className={`h-1.5 rounded-full transition-all ${
                  index === 0
                    ? "w-6 bg-purple-400"
                    : "w-1.5 bg-neutral-600"
                }`}
              />
            ))}
          </div>

          <p className="pt-2 text-center text-xs text-neutral-500">
            Swipe horizontally to explore sponsored campaigns.
          </p>
        </section>
      </main>

      {/* Footer & Support */}
      <footer className="mt-8 py-8 border-t border-neutral-800 bg-neutral-950">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="mb-5">
            <h3 className="text-lg font-semibold text-white">
              Need Help?
            </h3>

            <p className="text-neutral-400 mt-2">
              Contact CAIWAVE Support any time for WiFi assistance,
              vouchers or downtime compensation.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row justify-center gap-3">
            <a
              href="https://wa.me/25414302592?text=Hello%20CAIWAVE%20Support%2C%20I%20need%20help%20with%20the%20WiFi."
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 px-5 py-3 rounded-lg font-medium text-white transition-colors"
            >
              <MessageCircle className="w-5 h-5" />
              WhatsApp Support
            </a>

            <a
              href="tel:+25414302592"
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 px-5 py-3 rounded-lg font-medium text-white transition-colors"
            >
              <Phone className="w-5 h-5" />
              Call Support
            </a>
          </div>

          <div className="mt-6 text-neutral-500 text-sm">
            <p>Powered by CAIWAVE WiFi © 2026</p>
            <p className="mt-1">Reliable • Fast • Affordable</p>
            <p className="mt-1">www.caiwave.com</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default CaptivePortal;
