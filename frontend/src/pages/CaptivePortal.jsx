import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { API_URL, formatCurrency, formatDuration } from "../lib/utils";
import { toast } from "sonner";
import axios from "axios";
import {
  Wifi,
  Clock,
  CreditCard,
  Play,
  Check,
  Loader2,
  Zap,
  ArrowRight,
} from "lucide-react";

const CaptivePortal = () => {
  const { hotspotId } = useParams();
  const [loading, setLoading] = useState(true);
  const [hotspot, setHotspot] = useState(null);
  const [packages, setPackages] = useState([]);
  const [ads, setAds] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [step, setStep] = useState("select"); // select, payment, watching, success
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [adProgress, setAdProgress] = useState(0);
  const [sessionInfo, setSessionInfo] = useState(null);

  useEffect(() => {
    fetchPortalData();
  }, [hotspotId]);

  const fetchPortalData = async () => {
    try {
      // For demo, create mock data if hotspotId is "demo"
      if (hotspotId === "demo") {
        setHotspot({
          id: "demo",
          name: "CAITECH Demo Hotspot",
          ssid: "cainet-demo_FREE WIFI",
          location_name: "Demo Location",
        });
        setPackages([
          { id: "1", name: "Quick Access", price: 5, duration_minutes: 15 },
          { id: "2", name: "Half Hour", price: 10, duration_minutes: 30 },
          { id: "3", name: "One Hour", price: 20, duration_minutes: 60 },
          { id: "4", name: "Half Day", price: 50, duration_minutes: 360 },
          { id: "5", name: "Full Day", price: 100, duration_minutes: 1440 },
        ]);
        setAds([
          {
            id: "ad1",
            title: "Welcome to CAITECH",
            ad_type: "text",
            text_content: "Experience fast, reliable internet anywhere!",
            duration_seconds: 10,
          },
        ]);
        setLoading(false);
        return;
      }

      const response = await axios.get(`${API_URL}/portal/${hotspotId}`);
      setHotspot(response.data.hotspot);
      setPackages(response.data.packages);
      setAds(response.data.ads);
    } catch (error) {
      toast.error("Failed to load portal data");
      // Set demo data as fallback
      setHotspot({
        id: hotspotId,
        name: "WiFi Hotspot",
        ssid: "WiFi",
        location_name: "Unknown",
      });
      setPackages([
        { id: "1", name: "Quick Access", price: 5, duration_minutes: 15 },
        { id: "2", name: "Half Hour", price: 10, duration_minutes: 30 },
        { id: "3", name: "One Hour", price: 20, duration_minutes: 60 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!selectedPackage) {
      toast.error("Please select a package");
      return;
    }

    if (!phoneNumber || phoneNumber.length < 10) {
      toast.error("Please enter a valid phone number");
      return;
    }

    setPaymentLoading(true);
    setStep("payment");

    try {
      // Initiate payment
      const paymentResponse = await axios.post(`${API_URL}/payments/initiate`, {
        amount: selectedPackage.price,
        phone_number: phoneNumber,
        hotspot_id: hotspotId === "demo" ? "demo" : hotspotId,
        package_id: selectedPackage.id,
      });

      // Simulate M-Pesa STK push delay
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Confirm payment (mock)
      const confirmResponse = await axios.post(
        `${API_URL}/payments/confirm/${paymentResponse.data.id}`
      );

      setSessionInfo(confirmResponse.data);
      setStep("success");
      toast.success("Payment successful!", {
        description: `Session active for ${formatDuration(selectedPackage.duration_minutes)}`,
      });
    } catch (error) {
      toast.error("Payment failed", {
        description: "Please try again or contact support",
      });
      setStep("select");
    } finally {
      setPaymentLoading(false);
    }
  };

  const handleWatchAd = () => {
    setStep("watching");
    setAdProgress(0);

    const ad = ads[0];
    const duration = ad?.duration_seconds || 10;
    const interval = setInterval(() => {
      setAdProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          handleFreeSession();
          return 100;
        }
        return prev + 100 / (duration * 10);
      });
    }, 100);
  };

  const handleFreeSession = async () => {
    try {
      const response = await axios.post(`${API_URL}/portal/free-session`, null, {
        params: {
          hotspot_id: hotspotId === "demo" ? "demo" : hotspotId,
          ad_id: ads[0]?.id || "demo-ad",
        },
      });

      setSessionInfo(response.data);
      setStep("success");
      toast.success("Free session activated!", {
        description: "Enjoy 15 minutes of free WiFi",
      });
    } catch (error) {
      toast.error("Failed to activate free session");
      setStep("select");
    }
  };

  if (loading) {
    return (
      <div className="portal-container flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-neutral-400">Loading portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="portal-container min-h-screen flex flex-col" data-testid="captive-portal">
      {/* Header */}
      <div className="p-6 text-center">
        <div className="inline-flex items-center gap-2 mb-2">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <Wifi className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          <span className="font-semibold text-xl">CAITECH</span>
        </div>
        <h1 className="text-lg font-semibold">{hotspot?.name}</h1>
        <p className="text-neutral-400 text-sm">{hotspot?.location_name}</p>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 pb-8">
        <div className="w-full max-w-md">
          {/* Package Selection Step */}
          {step === "select" && (
            <div className="space-y-6 animate-fade-in">
              <div className="text-center mb-8">
                <h2 className="text-xl font-semibold mb-2">Choose Your Plan</h2>
                <p className="text-neutral-400 text-sm">
                  Select a package to get connected
                </p>
              </div>

              <div className="space-y-3">
                {packages.map((pkg) => (
                  <button
                    key={pkg.id}
                    onClick={() => setSelectedPackage(pkg)}
                    className={`w-full p-4 rounded-xl border transition-all ${
                      selectedPackage?.id === pkg.id
                        ? "border-blue-500 bg-blue-500/10"
                        : "border-neutral-800 bg-neutral-900/50 hover:border-neutral-700"
                    }`}
                    data-testid={`package-option-${pkg.id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            selectedPackage?.id === pkg.id
                              ? "bg-blue-500/20"
                              : "bg-neutral-800"
                          }`}
                        >
                          <Clock
                            className={`w-5 h-5 ${
                              selectedPackage?.id === pkg.id
                                ? "text-blue-400"
                                : "text-neutral-400"
                            }`}
                            strokeWidth={1.5}
                          />
                        </div>
                        <div className="text-left">
                          <div className="font-medium">{pkg.name}</div>
                          <div className="text-neutral-400 text-sm">
                            {formatDuration(pkg.duration_minutes)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-lg">
                          {formatCurrency(pkg.price)}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {selectedPackage && (
                <div className="space-y-4 pt-4 animate-fade-in">
                  <div className="space-y-2">
                    <label className="text-sm text-neutral-400">
                      M-Pesa Phone Number
                    </label>
                    <Input
                      type="tel"
                      placeholder="07XX XXX XXX"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="bg-neutral-900 border-neutral-800 text-center text-lg tracking-wider"
                      data-testid="phone-input"
                    />
                  </div>

                  <Button
                    onClick={handlePayment}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white btn-glow h-12"
                    disabled={paymentLoading}
                    data-testid="pay-btn"
                  >
                    <CreditCard className="w-5 h-5 mr-2" strokeWidth={1.5} />
                    Pay {formatCurrency(selectedPackage.price)} via M-Pesa
                  </Button>
                </div>
              )}

              {/* Free WiFi Option */}
              {ads.length > 0 && (
                <div className="pt-6 border-t border-neutral-800">
                  <button
                    onClick={handleWatchAd}
                    className="w-full p-4 rounded-xl border border-purple-500/30 bg-purple-500/10 hover:bg-purple-500/20 transition-all"
                    data-testid="watch-ad-btn"
                  >
                    <div className="flex items-center justify-center gap-3">
                      <Play className="w-5 h-5 text-purple-400" strokeWidth={1.5} />
                      <span className="text-purple-300">
                        Watch Ad for 15 min Free WiFi
                      </span>
                    </div>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Payment Processing Step */}
          {step === "payment" && (
            <div className="text-center space-y-6 animate-fade-in">
              <div className="w-20 h-20 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">Processing Payment</h2>
                <p className="text-neutral-400">
                  Please check your phone for the M-Pesa prompt
                </p>
              </div>
              <div className="bg-neutral-900/50 rounded-lg p-4">
                <p className="text-sm text-neutral-400 mb-1">Amount</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(selectedPackage?.price)}
                </p>
              </div>
            </div>
          )}

          {/* Watching Ad Step */}
          {step === "watching" && (
            <div className="space-y-6 animate-fade-in">
              <div className="ad-container p-6">
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto">
                    <Zap className="w-8 h-8 text-purple-400" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-lg font-semibold">{ads[0]?.title}</h3>
                  <p className="text-neutral-300">{ads[0]?.text_content}</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="ad-progress">
                  <div
                    className="ad-progress-bar"
                    style={{ width: `${adProgress}%` }}
                  />
                </div>
                <p className="text-center text-sm text-neutral-400">
                  {Math.ceil((100 - adProgress) / 10)}s remaining
                </p>
              </div>
            </div>
          )}

          {/* Success Step */}
          {step === "success" && (
            <div className="text-center space-y-6 animate-fade-in">
              <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
                <Check className="w-10 h-10 text-green-500" />
              </div>
              
              <div>
                <h2 className="text-xl font-semibold mb-2">You're Connected!</h2>
                <p className="text-neutral-400">Enjoy your internet session</p>
              </div>

              <div className="bg-neutral-900/50 rounded-xl p-6 space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-neutral-800">
                  <span className="text-neutral-400">Status</span>
                  <span className="text-green-400 font-medium flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    Active
                  </span>
                </div>
                
                {sessionInfo && (
                  <>
                    <div className="flex justify-between items-center py-2 border-b border-neutral-800">
                      <span className="text-neutral-400">Session ID</span>
                      <span className="font-mono text-sm">
                        {sessionInfo.session_id?.slice(0, 8)}...
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-neutral-400">Expires</span>
                      <span>
                        {new Date(sessionInfo.expires_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </>
                )}
              </div>

              <Button
                onClick={() => window.location.reload()}
                variant="outline"
                className="border-neutral-700 text-neutral-300"
              >
                Buy More Time
                <ArrowRight className="w-4 h-4 ml-2" strokeWidth={1.5} />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 text-center border-t border-neutral-800">
        <p className="text-neutral-500 text-xs">
          Powered by CAITECH • Need help? Contact support
        </p>
      </div>
    </div>
  );
};

export default CaptivePortal;
