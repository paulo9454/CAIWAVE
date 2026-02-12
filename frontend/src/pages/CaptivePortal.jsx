import { useState, useEffect } from "react";
import axios from "axios";
import { Wifi, Clock, Zap, MessageCircle, ExternalLink, Play, ChevronRight, Phone } from "lucide-react";
import { Button } from "../components/ui/button";
import { toast, Toaster } from "sonner";

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Format phone number for WhatsApp
const formatWhatsApp = (phone) => {
  if (!phone) return null;
  let cleaned = phone.replace(/\D/g, '');
  if (cleaned.startsWith('0')) cleaned = '254' + cleaned.slice(1);
  if (!cleaned.startsWith('254')) cleaned = '254' + cleaned;
  return cleaned;
};

const CaptivePortal = () => {
  const [hotspotId, setHotspotId] = useState(null);
  const [hotspot, setHotspot] = useState(null);
  const [packages, setPackages] = useState([]);
  const [ads, setAds] = useState([]);
  const [streams, setStreams] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [currentAdIndex, setCurrentAdIndex] = useState(0);

  useEffect(() => {
    // Get hotspot ID from URL params
    const params = new URLSearchParams(window.location.search);
    const hid = params.get('hotspot') || params.get('h') || params.get('id');
    setHotspotId(hid);
    
    fetchData(hid);
  }, []);

  // Rotate ads every 5 seconds
  useEffect(() => {
    if (ads.length > 1) {
      const interval = setInterval(() => {
        setCurrentAdIndex((prev) => (prev + 1) % ads.length);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [ads.length]);

  const fetchData = async (hid) => {
    try {
      // Fetch packages
      const packagesRes = await axios.get(`${API_URL}/packages/`);
      setPackages(packagesRes.data.filter(p => p.is_active));

      // Fetch active ads
      const adsRes = await axios.get(`${API_URL}/ads/public/active`);
      setAds(adsRes.data || []);

      // Fetch live streams
      const streamsRes = await axios.get(`${API_URL}/streams/live`);
      setStreams(streamsRes.data || []);

      // Fetch hotspot info if ID provided
      if (hid) {
        try {
          const hotspotRes = await axios.get(`${API_URL}/hotspots/${hid}`);
          setHotspot(hotspotRes.data);
        } catch (e) {
          console.log("Hotspot not found");
        }
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
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

      if (response.data.success && response.data.authorization_url) {
        toast.success("Redirecting to payment...");
        window.location.href = response.data.authorization_url;
      } else {
        toast.error(response.data.message || "Payment failed");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to initiate payment");
    } finally {
      setPaying(false);
    }
  };

  const currentAd = ads[currentAdIndex];
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
      
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 py-4 px-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <Wifi className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="font-bold text-lg">CAIWAVE WiFi</h1>
              {hotspot && <p className="text-blue-200 text-sm">{hotspot.name}</p>}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-4 space-y-6">
        
        {/* Featured Ad - Full Width */}
        {currentAd && (
          <div className="relative rounded-xl overflow-hidden bg-neutral-900 border border-neutral-800">
            {/* Ad Media */}
            <div className="relative w-full aspect-video bg-neutral-800">
              {currentAd.media_url ? (
                currentAd.ad_type === "video" ? (
                  <video
                    src={`${baseUrl}${currentAd.media_url}`}
                    className="w-full h-full object-cover"
                    autoPlay
                    muted
                    loop
                    playsInline
                  />
                ) : (
                  <img
                    src={`${baseUrl}${currentAd.media_url}`}
                    alt={currentAd.title}
                    className="w-full h-full object-cover"
                  />
                )
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-900 to-purple-900">
                  <span className="text-2xl font-bold">{currentAd.title}</span>
                </div>
              )}
              
              {/* Ad indicator dots */}
              {ads.length > 1 && (
                <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2">
                  {ads.map((_, i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        i === currentAdIndex ? 'bg-white' : 'bg-white/30'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>
            
            {/* Ad Info & CTA */}
            <div className="p-4">
              <h3 className="font-semibold text-lg">{currentAd.title}</h3>
              
              {/* Contact Buttons */}
              <div className="flex flex-wrap gap-3 mt-3">
                {currentAd.whatsapp_number && (
                  <a
                    href={`https://wa.me/${formatWhatsApp(currentAd.whatsapp_number)}?text=Hi, I saw your ad on CAIWAVE WiFi`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
                  >
                    <MessageCircle className="w-5 h-5" />
                    Chat on WhatsApp
                  </a>
                )}
                {currentAd.click_url && (
                  <a
                    href={currentAd.click_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                  >
                    <ExternalLink className="w-5 h-5" />
                    Visit Website
                  </a>
                )}
              </div>
            </div>
          </div>
        )}

        {/* WiFi Packages */}
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4">
          <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            Choose Your Package
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
                  </div>
                </div>
              ))}
            </div>
            
            <p className="text-neutral-500 text-sm text-center mt-3">
              Purchase a WiFi package to watch CAIWAVE TV
            </p>
          </div>
        )}

        {/* More Ads Carousel */}
        {ads.length > 1 && (
          <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4">
            <h2 className="font-semibold text-lg mb-4">More from Our Sponsors</h2>
            
            <div className="grid grid-cols-2 gap-3">
              {ads.filter((_, i) => i !== currentAdIndex).slice(0, 4).map((ad) => (
                <div key={ad.id} className="rounded-lg overflow-hidden bg-neutral-800">
                  {ad.media_url && (
                    <img
                      src={`${baseUrl}${ad.media_url}`}
                      alt={ad.title}
                      className="w-full aspect-video object-cover"
                    />
                  )}
                  <div className="p-3">
                    <div className="font-medium text-sm truncate">{ad.title}</div>
                    {ad.whatsapp_number && (
                      <a
                        href={`https://wa.me/${formatWhatsApp(ad.whatsapp_number)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 flex items-center gap-1 text-green-400 text-sm"
                      >
                        <MessageCircle className="w-4 h-4" />
                        WhatsApp
                        <ChevronRight className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-8 py-6 border-t border-neutral-800">
        <div className="max-w-4xl mx-auto px-4 text-center text-neutral-500 text-sm">
          <p>Powered by CAIWAVE WiFi © 2026. All Rights Reserved.</p>
          <p className="mt-1">www.caiwave.com</p>
        </div>
      </footer>
    </div>
  );
};

export default CaptivePortal;
