import { safeError } from "../utils/safeError";
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { API_URL } from "../lib/utils";
import { Wifi, Clock, Zap, MessageCircle, ExternalLink, Play, ChevronRight, Phone, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import PortalHeader from "../components/portal/PortalHeader";
import QuickActions from "../components/portal/QuickActions";
import CampaignHero from "../components/portal/CampaignHero";
import FeaturedAdvertisement from "../components/portal/FeaturedAdvertisement";
import PackagePurchasePanel from "../components/portal/PackagePurchasePanel";
import VoucherPanel from "../components/portal/VoucherPanel";
import TVPanel from "../components/portal/TVPanel";
import MarketplacePanel from "../components/portal/MarketplacePanel";
import PortalLoadingScreen from "../components/portal/PortalLoadingScreen";
import PortalNotificationPopup from "../components/portal/PortalNotificationPopup";
import WebPushEnrollment from "../components/portal/WebPushEnrollment";
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
  const [marketplaceProducts, setMarketplaceProducts] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [voucherCode, setVoucherCode] = useState("");
  const [redeemingVoucher, setRedeemingVoucher] = useState(false);
  const [currentAdIndex, setCurrentAdIndex] = useState(0);
  const activeSessionRestoreKeyRef = useRef("");

  const imageAds = useMemo(
    () => ads.filter((ad) => ad.ad_type !== "video"),
    [ads]
  );

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

  // Keep the featured advert position valid when eligible images change.
  useEffect(() => {
    setCurrentAdIndex((current) => {
      if (imageAds.length === 0) return 0;
      return Math.min(current, imageAds.length - 1);
    });
  }, [imageAds.length]);

  // Featured adverts are image-only and rotate automatically.
  useEffect(() => {
    if (imageAds.length <= 1) return undefined;

    const timeout = window.setTimeout(() => {
      setCurrentAdIndex((current) => (current + 1) % imageAds.length);
    }, 6000);

    return () => window.clearTimeout(timeout);
  }, [imageAds.length, currentAdIndex]);

  const showPreviousAd = () => {
    if (imageAds.length <= 1) return;

    setCurrentAdIndex((current) =>
      current === 0 ? imageAds.length - 1 : current - 1
    );
  };

  const showNextAd = () => {
    if (imageAds.length <= 1) return;

    setCurrentAdIndex((current) => (current + 1) % imageAds.length);
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

      try {
        const marketplaceRes = await axios.get(
          `${API_URL}/marketplace/`
        );
        setMarketplaceProducts(
          Array.isArray(marketplaceRes.data)
            ? marketplaceRes.data
            : []
        );
      } catch (marketplaceError) {
        console.error(
          "Failed to load CAIMART products:",
          marketplaceError
        );
        setMarketplaceProducts([]);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const submitCredentialsToMikrotik = useCallback((credentials) => {
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
  }, [mikrotikLoginUrl, originalDestination]);

  // Restore an existing unexpired WiFi entitlement when a client reconnects.
  // This deliberately reuses the same MikroTik login flow used by payments,
  // vouchers and sponsored free sessions.
  useEffect(() => {
    if (!hotspotId || !clientMac || !mikrotikLoginUrl) {
      return undefined;
    }

    const restoreKey = `${hotspotId}|${clientMac}|${mikrotikLoginUrl}`;

    if (activeSessionRestoreKeyRef.current === restoreKey) {
      return undefined;
    }

    activeSessionRestoreKeyRef.current = restoreKey;
    let cancelled = false;

    const restoreActiveSession = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/portal/active-session`,
          {
            params: {
              hotspot_id: hotspotId,
              user_mac: clientMac,
            },
          }
        );

        if (cancelled) {
          return;
        }

        const session = response.data || {};
        const credentials =
          session.wifi_credentials ||
          (
            session.username && session.password
              ? {
                  username: session.username,
                  password: session.password,
                }
              : null
          );

        if (!credentials) {
          return;
        }

        toast.success("Active WiFi session found. Reconnecting…");
        submitCredentialsToMikrotik(credentials);
      } catch (error) {
        if (cancelled) {
          return;
        }

        const status = error?.response?.status;

        // No active session is a normal portal state. Keep showing the
        // purchase and voucher options without alarming the customer.
        if (status !== 404) {
          console.warn("Could not restore active WiFi session:", error);
        }
      }
    };

    restoreActiveSession();

    return () => {
      cancelled = true;
    };
  }, [
    hotspotId,
    clientMac,
    mikrotikLoginUrl,
    submitCredentialsToMikrotik,
  ]);

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

  const scrollToFeaturedAd = () => {
    const advertisement = document.getElementById(
      "featured-advertisement"
    );

    if (!advertisement) {
      toast.error("The featured advert could not be opened.");
      return;
    }

    advertisement.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleViewAnotherAdvert = () => {
    setFreeSession(null);

    window.requestAnimationFrame(() => {
      scrollToFeaturedAd();
    });
  };

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

  const currentAd = imageAds[currentAdIndex] || fallbackAd;
  const hasRealAd = imageAds.length > 0;

  const featuredCampaign = campaigns[0] || null;
  const baseUrl = API_URL.replace('/api', '');

  if (loading) {
    return <PortalLoadingScreen />;
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#050914] text-white">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute left-1/2 top-[-16rem] h-[34rem] w-[34rem] -translate-x-1/2 rounded-full bg-blue-600/15 blur-[120px]" />
        <div className="absolute bottom-[-14rem] right-[-12rem] h-[30rem] w-[30rem] rounded-full bg-cyan-500/10 blur-[110px]" />
      </div>

      <div className="relative">
        <Toaster
          theme="dark"
          richColors
          position="top-center"
          toastOptions={{
            className: "border-white/10 bg-neutral-950/95 text-white",
          }}
        />

        <PortalNotificationPopup
          hotspotId={hotspotId}
        />

        <PortalHeader hotspot={hotspot} />

        <QuickActions />

        <main className="mx-auto max-w-4xl space-y-5 px-4 pb-8 pt-5 sm:space-y-6 sm:px-6 sm:pb-10">

        <CampaignHero
          campaign={featuredCampaign}
          baseUrl={baseUrl}
        />

        <PackagePurchasePanel
          packages={packages}
          selectedPackage={selectedPackage}
          setSelectedPackage={setSelectedPackage}
          phone={phone}
          setPhone={setPhone}
          email={email}
          setEmail={setEmail}
          paying={paying}
          handlePurchase={handlePurchase}
          freeSession={freeSession}
          paymentOpen={paymentOpen}
          setPaymentOpen={setPaymentOpen}
        />

        <VoucherPanel
          voucherCode={voucherCode}
          setVoucherCode={setVoucherCode}
          redeemingVoucher={redeemingVoucher}
          handleVoucherRedemption={handleVoucherRedemption}
        />

        <WebPushEnrollment
          hotspotId={hotspotId}
          clientMac={clientMac}
          clientIp={clientIp}
          onRewardGranted={submitCredentialsToMikrotik}
        />

        {/* Free WiFi Section - After watching ad */}
        {!freeSession && (
          <div
            id="free-wifi"
            className={`scroll-mt-5 rounded-xl border p-5 ${
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
                      View the featured advert at the bottom, then return here for free internet •
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
                      You've watched 2 ads today. Choose one of the packages above to continue browsing!
                    </p>
                  </>
                )}
              </div>
              {freeSessionStatus.can_get_free ? (
                <Button
                  onClick={scrollToFeaturedAd}
                  disabled={gettingFreeWifi || !hasRealAd}
                  className="w-full sm:w-auto bg-green-600 hover:bg-green-700 text-white px-6 py-3"
                >
                  {gettingFreeWifi ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Play className="w-5 h-5 mr-2" />
                      {hasRealAd
                        ? `View Advert & Continue (${freeSessionStatus.free_sessions_remaining} left)`
                        : "Free WiFi Coming Soon"}
                    </>
                  )}
                </Button>
              ) : (
                <div className="text-center">
                  <p className="text-orange-400 text-sm font-medium">👆 Choose a package above</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Free Session Credentials - Show after getting free WiFi */}
        {freeSession && (
          <div
            id="free-wifi"
            className="scroll-mt-5 bg-gradient-to-r from-blue-900/50 to-indigo-900/50 rounded-xl border border-blue-700/50 p-6"
          >
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
                    Want more time? View another advert below ({freeSessionStatus.free_sessions_remaining} left) or choose a package above!
                  </p>
                  <Button
                    onClick={handleViewAnotherAdvert}
                    variant="outline"
                    className="mt-2"
                  >
                    View Another Advert
                  </Button>
                </>
              ) : (
                <p className="text-sm text-orange-400">
                  You've used all free advert sessions. Choose a package above for more time!
                </p>
              )}
            </div>
          </div>
        )}

        <TVPanel streams={streams} />

        <MarketplacePanel
          products={marketplaceProducts}
          baseUrl={baseUrl}
        />

        <FeaturedAdvertisement
          currentAd={currentAd}
          ads={imageAds}
          baseUrl={baseUrl}
          currentAdIndex={currentAdIndex}
          setCurrentAdIndex={setCurrentAdIndex}
          showPreviousAd={showPreviousAd}
          showNextAd={showNextAd}
          hasRealAd={hasRealAd}
          formatWhatsApp={formatWhatsApp}
          onClaimFreeWifi={handleGetFreeWifi}
          claimingFreeWifi={gettingFreeWifi}
          canClaimFreeWifi={
            !freeSession && freeSessionStatus.can_get_free
          }
        />

</main>

      {/* Footer & Support */}
      <footer
        id="support"
        className="scroll-mt-5 mt-8 py-8 border-t border-neutral-800 bg-neutral-950"
      >
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
    </div>
  );
};

export default CaptivePortal;
