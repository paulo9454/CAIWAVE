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
  AlertCircle,
} from "lucide-react";

const CaptivePortal = () => {
  const { hotspotId } = useParams();
  const [loading, setLoading] = useState(true);
  const [hotspot, setHotspot] = useState(null);
  const [packages, setPackages] = useState([]);
  const [ads, setAds] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [step, setStep] = useState("select"); // select, payment, watching, success, error
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [adProgress, setAdProgress] = useState(0);
  const [sessionInfo, setSessionInfo] = useState(null);
  const [paymentId, setPaymentId] = useState(null);
  const [mpesaEnabled, setMpesaEnabled] = useState(false);

  useEffect(() => {
    fetchPortalData();
  }, [hotspotId]);

  const fetchPortalData = async () => {
    try {
      const response = await axios.get(`${API_URL}/portal/${hotspotId}`);
      setHotspot(response.data.hotspot);
      setPackages(response.data.packages);
      setAds(response.data.ads);
      setMpesaEnabled(response.data.mpesa_enabled);
    } catch (error) {
      toast.error("Failed to load portal data");
      // Set demo fallback data
      setHotspot({
        id: hotspotId,
        name: "CAITECH Hotspot",
        ssid: "Cainet_FREE WIFI",
        location_name: "Location",
      });
      setPackages([
        { id: "1", name: "30 Minutes", price: 5, duration_minutes: 30 },
        { id: "2", name: "4 Hours", price: 15, duration_minutes: 240 },
        { id: "3", name: "8 Hours", price: 25, duration_minutes: 480 },
        { id: "4", name: "12 Hours", price: 30, duration_minutes: 720 },
        { id: "5", name: "24 Hours", price: 35, duration_minutes: 1440 },
        { id: "6", name: "1 Week", price: 200, duration_minutes: 10080 },
        { id: "7", name: "1 Month", price: 600, duration_minutes: 43200 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatDurationDisplay = (minutes) => {
    if (minutes < 60) return `${minutes} min`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)} hours`;
    if (minutes < 10080) return `${Math.floor(minutes / 1440)} day${Math.floor(minutes / 1440) > 1 ? 's' : ''}`;
    if (minutes < 43200) return `${Math.floor(minutes / 10080)} week${Math.floor(minutes / 10080) > 1 ? 's' : ''}`;
    return `${Math.floor(minutes / 43200)} month${Math.floor(minutes / 43200) > 1 ? 's' : ''}`;
  };

  const handlePayment = async () => {
    if (!selectedPackage) {
      toast.error("Please select a package");
      return;
    }

    if (!phoneNumber || phoneNumber.length < 10) {
      toast.error("Please enter a valid M-Pesa phone number");
      return;
    }

    setPaymentLoading(true);
    setStep("payment");

    try {
      // Initiate payment via real M-Pesa
      const response = await axios.post(`${API_URL}/payments/initiate`, {
        amount: selectedPackage.price,
        phone_number: phoneNumber,
        hotspot_id: hotspotId === "demo" ? "demo" : hotspotId,
        package_id: selectedPackage.id,
        method: "mpesa"
      });

      setPaymentId(response.data.payment_id);

      if (response.data.status === "processing") {
        // STK Push sent - wait for callback
        toast.info("Check your phone for M-Pesa prompt");
        
        // Poll for payment status
        pollPaymentStatus(response.data.payment_id);
      } else {
        throw new Error(response.data.message || "Payment failed");
      }
    } catch (error) {
      const message = error.response?.data?.detail || error.message || "Payment failed";
      toast.error("Payment failed", { description: message });
      setStep("error");
      setPaymentLoading(false);
    }
  };

  const pollPaymentStatus = async (paymentId) => {
    let attempts = 0;
    const maxAttempts = 60; // 2 minutes max
    
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/payments/${paymentId}`);
        
        if (response.data.status === "completed") {
          // Payment successful
          const sessionResponse = await axios.get(`${API_URL}/sessions/${response.data.session_id}`);
          setSessionInfo({
            session_id: response.data.session_id,
            username: sessionResponse.data.username,
            password: sessionResponse.data.password,
            expires_at: sessionResponse.data.expires_at
          });
          setStep("success");
          setPaymentLoading(false);
          toast.success("Payment successful!", {
            description: `Your ${formatDurationDisplay(selectedPackage.duration_minutes)} session is active`,
          });
          return;
        } else if (response.data.status === "failed") {
          throw new Error("Payment was declined");
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 2000);
        } else {
          throw new Error("Payment timeout - please check your M-Pesa messages");
        }
      } catch (error) {
        toast.error("Payment failed", { description: error.message });
        setStep("error");
        setPaymentLoading(false);
      }
    };
    
    checkStatus();
  };

  const handleWatchAd = () => {
    if (ads.length === 0) {
      toast.error("No ads available");
      return;
    }
    
    setStep("watching");
    setAdProgress(0);

    const ad = ads[0];
    const duration = ad?.duration_seconds || 10;
    const interval = setInterval(() => {
      setAdProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          handleFreeSession(ad.id);
          return 100;
        }
        return prev + 100 / (duration * 10);
      });
    }, 100);
  };

  const handleFreeSession = async (adId) => {
    try {
      const response = await axios.post(`${API_URL}/portal/free-session`, null, {
        params: {
          hotspot_id: hotspotId === "demo" ? "demo" : hotspotId,
          ad_id: adId,
        },
      });

      setSessionInfo(response.data);
      setStep("success");
      toast.success("Free session activated!", {
        description: "Enjoy 30 minutes of free WiFi",
      });
    } catch (error) {
      toast.error("Failed to activate free session");
      setStep("select");
    }
  };

  const retryPayment = () => {
    setStep("select");
    setPaymentLoading(false);
    setPaymentId(null);
  };

  if (loading) {
    return (
      <div className="portal-container flex items-center justify-center" style={{ backgroundColor: '#050505', minHeight: '100vh' }}>
        <div className="text-center">
          <Loader2 className="w-10 h-10 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-neutral-400">Loading portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col text-white" style={{ backgroundColor: '#050505' }} data-testid="captive-portal">
      {/* Header */}
      <div className="p-6 text-center" style={{ background: 'radial-gradient(ellipse at top, rgba(37,99,235,0.15), transparent 70%)' }}>
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

              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {packages.map((pkg) => (
                  <button
                    key={pkg.id}
                    onClick={() => setSelectedPackage(pkg)}
                    className={`w-full p-4 rounded-xl border transition-all ${
                      selectedPackage?.id === pkg.id
                        ? "border-blue-500 bg-blue-500/10"
                        : "border-neutral-800 hover:border-neutral-700"
                    }`}
                    style={{ backgroundColor: selectedPackage?.id === pkg.id ? 'rgba(37,99,235,0.1)' : 'rgba(24,24,27,0.5)' }}
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
                            {formatDurationDisplay(pkg.duration_minutes)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-lg">
                          KES {pkg.price}
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
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white h-12"
                    disabled={paymentLoading || !mpesaEnabled}
                    data-testid="pay-btn"
                  >
                    <CreditCard className="w-5 h-5 mr-2" strokeWidth={1.5} />
                    Pay KES {selectedPackage.price} via M-Pesa
                  </Button>

                  {!mpesaEnabled && (
                    <p className="text-yellow-500 text-xs text-center flex items-center justify-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      M-Pesa is being configured. Please try again later.
                    </p>
                  )}
                </div>
              )}

              {/* Free WiFi Option */}
              {ads.length > 0 && (
                <div className="pt-6 border-t border-neutral-800">
                  <button
                    onClick={handleWatchAd}
                    className="w-full p-4 rounded-xl border border-purple-500/30 hover:bg-purple-500/10 transition-all"
                    style={{ backgroundColor: 'rgba(124,58,237,0.05)' }}
                    data-testid="watch-ad-btn"
                  >
                    <div className="flex items-center justify-center gap-3">
                      <Play className="w-5 h-5 text-purple-400" strokeWidth={1.5} />
                      <span className="text-purple-300">
                        Watch Ad for 30 min Free WiFi
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
                <p className="text-neutral-500 text-sm mt-2">
                  Enter your M-Pesa PIN to complete payment
                </p>
              </div>
              <div className="rounded-lg p-4" style={{ backgroundColor: 'rgba(24,24,27,0.5)' }}>
                <p className="text-sm text-neutral-400 mb-1">Amount</p>
                <p className="text-2xl font-bold">
                  KES {selectedPackage?.price}
                </p>
              </div>
            </div>
          )}

          {/* Error Step */}
          {step === "error" && (
            <div className="text-center space-y-6 animate-fade-in">
              <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto">
                <AlertCircle className="w-10 h-10 text-red-500" />
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">Payment Failed</h2>
                <p className="text-neutral-400">
                  The payment could not be completed. Please try again.
                </p>
              </div>
              <Button
                onClick={retryPayment}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                Try Again
              </Button>
            </div>
          )}

          {/* Watching Ad Step */}
          {step === "watching" && (
            <div className="space-y-6 animate-fade-in">
              <div className="rounded-xl p-6 border border-neutral-800" style={{ backgroundColor: 'rgba(10,10,10,0.8)' }}>
                <div className="text-center space-y-4">
                  <div className="w-16 h-16 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto">
                    <Zap className="w-8 h-8 text-purple-400" strokeWidth={1.5} />
                  </div>
                  <h3 className="text-lg font-semibold">{ads[0]?.title}</h3>
                  <p className="text-neutral-300">{ads[0]?.text_content}</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="h-1 rounded-full" style={{ backgroundColor: '#18181b' }}>
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ 
                      width: `${adProgress}%`,
                      background: 'linear-gradient(90deg, #2563eb, #7c3aed)'
                    }}
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

              <div className="rounded-xl p-6 space-y-4" style={{ backgroundColor: 'rgba(24,24,27,0.5)' }}>
                <div className="flex justify-between items-center py-2 border-b border-neutral-800">
                  <span className="text-neutral-400">Status</span>
                  <span className="text-green-400 font-medium flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    Active
                  </span>
                </div>
                
                {sessionInfo?.username && (
                  <>
                    <div className="flex justify-between items-center py-2 border-b border-neutral-800">
                      <span className="text-neutral-400">Username</span>
                      <span className="font-mono">{sessionInfo.username}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-neutral-800">
                      <span className="text-neutral-400">Password</span>
                      <span className="font-mono">{sessionInfo.password}</span>
                    </div>
                  </>
                )}
                
                {sessionInfo?.expires_at && (
                  <div className="flex justify-between items-center py-2">
                    <span className="text-neutral-400">Expires</span>
                    <span>
                      {new Date(sessionInfo.expires_at).toLocaleString()}
                    </span>
                  </div>
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

      {/* Mandatory Footer */}
      <div className="p-4 text-center border-t border-neutral-800">
        <p className="text-neutral-500 text-xs">
          Powered by <span className="text-blue-400 font-medium">CAITECH</span> © 2026. All Rights Reserved.
        </p>
      </div>
    </div>
  );
};

export default CaptivePortal;
