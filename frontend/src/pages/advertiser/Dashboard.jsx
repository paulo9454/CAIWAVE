import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { getUser, logout, getAuthToken } from "../../lib/auth";
import { API_URL, formatCurrency } from "../../lib/utils";
import axios from "axios";
import { toast } from "sonner";
import {
  LayoutDashboard,
  Image,
  Video,
  LogOut,
  Menu,
  Upload,
  Eye,
  MousePointer,
  Clock,
  CheckCircle,
  XCircle,
  DollarSign,
  AlertCircle,
  Trash2,
  X,
  Play,
  FileImage,
  FileVideo,
  ExternalLink,
  Package,
  MapPin,
  CreditCard,
  ChevronRight,
  Phone,
  Building2,
  Globe,
  Info,
} from "lucide-react";
import { CaiwaveLogo } from "../../components/CaiwaveLogo";

// Helper function for status badges
const getStatusBadge = (status) => {
  const badges = {
    pending_approval: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Pending Approval" },
    approved: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Approved - Ready to Pay" },
    rejected: { bg: "bg-red-500/10", text: "text-red-400", label: "Rejected" },
    paid: { bg: "bg-purple-500/10", text: "text-purple-400", label: "Paid - Awaiting Activation" },
    active: { bg: "bg-green-500/10", text: "text-green-400", label: "Active" },
    suspended: { bg: "bg-red-500/10", text: "text-red-400", label: "Suspended" },
  };
  return badges[status] || { bg: "bg-gray-500/10", text: "text-gray-400", label: status };
};

// Coverage scope icon
const getCoverageIcon = (scope) => {
  switch (scope) {
    case "constituency": return <MapPin className="w-5 h-5" />;
    case "county": return <Building2 className="w-5 h-5" />;
    case "national": return <Globe className="w-5 h-5" />;
    default: return <MapPin className="w-5 h-5" />;
  }
};

// Package Selection Component
const PackageSelector = ({ packages, selectedPackage, onSelect }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {packages.map((pkg) => (
        <div
          key={pkg.id}
          onClick={() => onSelect(pkg)}
          className={`cursor-pointer p-6 rounded-xl border-2 transition-all ${
            selectedPackage?.id === pkg.id
              ? "border-blue-500 bg-blue-500/10"
              : "border-neutral-700 hover:border-neutral-600 bg-neutral-900"
          }`}
          data-testid={`package-${pkg.name.toLowerCase().replace(/\s/g, '-')}`}
        >
          <div className="flex items-center gap-3 mb-3">
            <div className={`p-2 rounded-lg ${selectedPackage?.id === pkg.id ? 'bg-blue-500/20' : 'bg-neutral-800'}`}>
              {getCoverageIcon(pkg.coverage_scope)}
            </div>
            <h3 className="text-lg font-semibold">{pkg.name}</h3>
          </div>
          
          <div className="text-3xl font-bold text-blue-400 mb-2">
            KES {pkg.price.toLocaleString()}
          </div>
          
          <div className="text-sm text-neutral-400 mb-3">
            {pkg.duration_days} days duration
          </div>
          
          <p className="text-sm text-neutral-500">
            {pkg.description}
          </p>
          
          {selectedPackage?.id === pkg.id && (
            <div className="mt-4 flex items-center gap-2 text-blue-400">
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">Selected</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// Coverage Selection Component
const CoverageSelector = ({ package: pkg, counties, selectedCounty, constituencies, selectedConstituencies, onCountyChange, onConstituencyToggle }) => {
  if (!pkg) return null;
  
  if (pkg.coverage_scope === "national") {
    return (
      <div className="p-6 bg-neutral-900 rounded-xl border border-neutral-800">
        <div className="flex items-center gap-3 text-green-400">
          <Globe className="w-6 h-6" />
          <div>
            <h3 className="font-semibold">National Coverage</h3>
            <p className="text-sm text-neutral-400">Your ad will be displayed across all CAIWAVE hotspots nationwide.</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* County Selection */}
      <div>
        <label className="block text-sm text-neutral-400 mb-2">Select County</label>
        <select
          value={selectedCounty}
          onChange={(e) => onCountyChange(e.target.value)}
          className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          data-testid="county-select"
        >
          <option value="">Choose a county...</option>
          {counties.map((county) => (
            <option key={county} value={county}>{county}</option>
          ))}
        </select>
      </div>
      
      {/* Constituency Selection (for Small Area only) */}
      {pkg.coverage_scope === "constituency" && selectedCounty && constituencies.length > 0 && (
        <div>
          <label className="block text-sm text-neutral-400 mb-2">
            Select Constituencies <span className="text-blue-400">(select one or more)</span>
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto p-2">
            {constituencies.map((const_) => (
              <label
                key={const_}
                className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedConstituencies.includes(const_)
                    ? "bg-blue-500/20 border border-blue-500"
                    : "bg-neutral-800 border border-neutral-700 hover:border-neutral-600"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedConstituencies.includes(const_)}
                  onChange={() => onConstituencyToggle(const_)}
                  className="w-4 h-4 rounded border-neutral-600 bg-neutral-800 text-blue-500 focus:ring-blue-500"
                />
                <span className="text-sm">{const_}</span>
              </label>
            ))}
          </div>
        </div>
      )}
      
      {/* County-level info for Large Area */}
      {pkg.coverage_scope === "county" && selectedCounty && (
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center gap-2 text-green-400">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">All hotspots in {selectedCounty} County will display your ad</span>
          </div>
        </div>
      )}
    </div>
  );
};

// Ad Upload Form with Package Selection
const AdUploadForm = ({ onSuccess }) => {
  const [step, setStep] = useState(1);
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [counties, setCounties] = useState([]);
  const [selectedCounty, setSelectedCounty] = useState("");
  const [constituencies, setConstituencies] = useState([]);
  const [selectedConstituencies, setSelectedConstituencies] = useState([]);
  const [formData, setFormData] = useState({
    title: "",
    ad_type: "image",
    click_url: "",
  });
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPackagesAndLocations();
  }, []);

  useEffect(() => {
    if (selectedCounty) {
      fetchConstituencies(selectedCounty);
    } else {
      setConstituencies([]);
      setSelectedConstituencies([]);
    }
  }, [selectedCounty]);

  const fetchPackagesAndLocations = async () => {
    try {
      const [pkgRes, countiesRes] = await Promise.all([
        axios.get(`${API_URL}/ad-packages/`),
        axios.get(`${API_URL}/locations/counties`)
      ]);
      setPackages(pkgRes.data);
      setCounties(countiesRes.data.counties);
    } catch (error) {
      toast.error("Failed to load packages");
    } finally {
      setLoading(false);
    }
  };

  const fetchConstituencies = async (county) => {
    try {
      const res = await axios.get(`${API_URL}/locations/constituencies?county=${county}`);
      setConstituencies(res.data.constituencies);
    } catch (error) {
      toast.error("Failed to load constituencies");
    }
  };

  const handleConstituencyToggle = (constituency) => {
    setSelectedConstituencies(prev => 
      prev.includes(constituency)
        ? prev.filter(c => c !== constituency)
        : [...prev, constituency]
    );
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedPackage) {
      toast.error("Please select a package");
      return;
    }
    
    if (!file) {
      toast.error("Please upload media");
      return;
    }

    // Validate coverage selection
    if (selectedPackage.coverage_scope === "constituency" && selectedConstituencies.length === 0) {
      toast.error("Please select at least one constituency");
      return;
    }
    
    if (selectedPackage.coverage_scope === "county" && !selectedCounty) {
      toast.error("Please select a county");
      return;
    }

    // Validate file
    const isImage = formData.ad_type === "image";
    const maxSize = isImage ? 5 * 1024 * 1024 : 20 * 1024 * 1024;
    const allowedTypes = isImage 
      ? ["image/jpeg", "image/png", "image/webp"]
      : ["video/mp4", "video/webm"];

    if (file.size > maxSize) {
      toast.error(`File too large. Maximum: ${isImage ? "5MB" : "20MB"}`);
      return;
    }

    if (!allowedTypes.includes(file.type)) {
      toast.error(`Invalid file type. Allowed: ${isImage ? "JPG, PNG, WEBP" : "MP4, WEBM"}`);
      return;
    }

    setUploading(true);

    const uploadData = new FormData();
    uploadData.append("title", formData.title);
    uploadData.append("ad_type", formData.ad_type);
    uploadData.append("package_id", selectedPackage.id);
    uploadData.append("click_url", formData.click_url || "");
    uploadData.append("media", file);
    
    // Add coverage data
    if (selectedPackage.coverage_scope === "constituency") {
      uploadData.append("constituencies", JSON.stringify(selectedConstituencies));
    } else if (selectedPackage.coverage_scope === "county") {
      uploadData.append("counties", JSON.stringify([selectedCounty]));
    }

    try {
      const response = await axios.post(`${API_URL}/ads/upload`, uploadData, {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.success) {
        toast.success(`Ad submitted! Package: ${response.data.package} - KES ${response.data.price}`);
        // Reset form
        setStep(1);
        setSelectedPackage(null);
        setSelectedCounty("");
        setSelectedConstituencies([]);
        setFormData({ title: "", ad_type: "image", click_url: "" });
        setFile(null);
        setPreview(null);
        if (onSuccess) onSuccess();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to upload ad");
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-card flex items-center justify-center py-12">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="dashboard-card" data-testid="ad-upload-form">
      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
              step >= s ? "bg-blue-600 text-white" : "bg-neutral-800 text-neutral-500"
            }`}>
              {s}
            </div>
            <span className={`ml-2 hidden sm:inline ${step >= s ? "text-white" : "text-neutral-500"}`}>
              {s === 1 ? "Select Package" : s === 2 ? "Choose Coverage" : "Upload Media"}
            </span>
            {s < 3 && <ChevronRight className="w-5 h-5 mx-4 text-neutral-600" />}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Package Selection */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Choose Your Advertising Package</h2>
              <p className="text-neutral-400">Select the coverage area that best fits your campaign goals.</p>
            </div>
            
            <PackageSelector 
              packages={packages} 
              selectedPackage={selectedPackage} 
              onSelect={setSelectedPackage} 
            />
            
            <div className="flex justify-end">
              <Button
                type="button"
                onClick={() => setStep(2)}
                disabled={!selectedPackage}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="next-step-1"
              >
                Continue <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Coverage Selection */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Select Coverage Area</h2>
              <p className="text-neutral-400">
                {selectedPackage?.coverage_scope === "national" 
                  ? "Your ad will reach all CAIWAVE hotspots across Kenya."
                  : "Choose where your ad should be displayed."}
              </p>
            </div>
            
            <CoverageSelector
              package={selectedPackage}
              counties={counties}
              selectedCounty={selectedCounty}
              constituencies={constituencies}
              selectedConstituencies={selectedConstituencies}
              onCountyChange={setSelectedCounty}
              onConstituencyToggle={handleConstituencyToggle}
            />
            
            <div className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(1)}
                className="border-neutral-700"
              >
                Back
              </Button>
              <Button
                type="button"
                onClick={() => setStep(3)}
                disabled={
                  (selectedPackage?.coverage_scope === "constituency" && selectedConstituencies.length === 0) ||
                  (selectedPackage?.coverage_scope === "county" && !selectedCounty)
                }
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="next-step-2"
              >
                Continue <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Media Upload */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Upload Your Ad</h2>
              <p className="text-neutral-400">Add your ad creative and details.</p>
            </div>
            
            {/* Summary Card */}
            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-neutral-400">Package:</span>
                  <span className="ml-2 font-semibold text-blue-400">{selectedPackage?.name}</span>
                </div>
                <div className="text-right">
                  <span className="text-neutral-400">Price:</span>
                  <span className="ml-2 font-bold text-xl text-green-400">KES {selectedPackage?.price.toLocaleString()}</span>
                </div>
              </div>
              <div className="mt-2 text-sm text-neutral-400">
                Duration: {selectedPackage?.duration_days} days
                {selectedPackage?.coverage_scope === "national" 
                  ? " • National coverage"
                  : selectedPackage?.coverage_scope === "county"
                    ? ` • ${selectedCounty} County`
                    : ` • ${selectedConstituencies.length} constituencies`}
              </div>
            </div>

            {/* Ad Title */}
            <div>
              <label className="block text-sm text-neutral-400 mb-2">Ad Title *</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
                placeholder="Enter a name for your ad"
                required
                data-testid="ad-title-input"
              />
            </div>

            {/* Ad Type */}
            <div>
              <label className="block text-sm text-neutral-400 mb-2">Ad Type *</label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, ad_type: "image" })}
                  className={`flex items-center justify-center gap-3 p-4 rounded-lg border transition-colors ${
                    formData.ad_type === "image"
                      ? "bg-blue-600/20 border-blue-500 text-blue-400"
                      : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-600"
                  }`}
                  data-testid="ad-type-image"
                >
                  <Image className="w-5 h-5" />
                  <span>Image Banner</span>
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, ad_type: "video" })}
                  className={`flex items-center justify-center gap-3 p-4 rounded-lg border transition-colors ${
                    formData.ad_type === "video"
                      ? "bg-blue-600/20 border-blue-500 text-blue-400"
                      : "bg-neutral-900 border-neutral-700 text-neutral-400 hover:border-neutral-600"
                  }`}
                  data-testid="ad-type-video"
                >
                  <Video className="w-5 h-5" />
                  <span>Short Video (10-15s)</span>
                </button>
              </div>
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-sm text-neutral-400 mb-2">
                Upload {formData.ad_type === "image" ? "Image" : "Video"} *
              </label>
              <div className="border-2 border-dashed border-neutral-700 rounded-lg p-8 text-center hover:border-neutral-600 transition-colors">
                {preview ? (
                  <div className="relative">
                    {formData.ad_type === "image" ? (
                      <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-lg" />
                    ) : (
                      <video src={preview} className="max-h-48 mx-auto rounded-lg" controls />
                    )}
                    <button
                      type="button"
                      onClick={() => { setFile(null); setPreview(null); }}
                      className="absolute top-2 right-2 p-1 bg-red-500 rounded-full hover:bg-red-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <p className="mt-2 text-sm text-neutral-400">{file?.name}</p>
                  </div>
                ) : (
                  <>
                    <Upload className="w-10 h-10 text-neutral-500 mx-auto mb-3" />
                    <p className="text-neutral-400 mb-2">
                      Click to upload your {formData.ad_type === "image" ? "image" : "video"}
                    </p>
                    <p className="text-neutral-500 text-sm mb-4">
                      {formData.ad_type === "image" 
                        ? "JPG, PNG, WEBP • Max 5MB" 
                        : "MP4, WEBM • Max 20MB • 10-15 seconds"}
                    </p>
                    <label className="cursor-pointer">
                      <span className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 rounded-lg text-sm transition-colors">
                        Browse Files
                      </span>
                      <input
                        type="file"
                        className="hidden"
                        accept={formData.ad_type === "image" ? "image/jpeg,image/png,image/webp" : "video/mp4,video/webm"}
                        onChange={handleFileChange}
                        data-testid="ad-file-input"
                      />
                    </label>
                  </>
                )}
              </div>
            </div>

            {/* Optional Click URL */}
            <div>
              <label className="block text-sm text-neutral-400 mb-2">Click-through URL (optional)</label>
              <input
                type="url"
                value={formData.click_url}
                onChange={(e) => setFormData({ ...formData, click_url: e.target.value })}
                className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
                placeholder="https://your-website.com"
                data-testid="ad-url-input"
              />
            </div>

            <div className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(2)}
                className="border-neutral-700"
              >
                Back
              </Button>
              <Button
                type="submit"
                disabled={uploading || !file || !formData.title}
                className="bg-blue-600 hover:bg-blue-700"
                data-testid="submit-ad"
              >
                {uploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Submit Ad for Review
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

// Ad Card Component
const AdCard = ({ ad, onPayClick, onDelete }) => {
  const badge = getStatusBadge(ad.status);
  
  return (
    <div className="dashboard-card" data-testid={`ad-card-${ad.id}`}>
      <div className="flex flex-col md:flex-row gap-4">
        {/* Media Preview */}
        <div className="w-full md:w-48 h-32 bg-neutral-800 rounded-lg overflow-hidden flex-shrink-0">
          {ad.media_url ? (
            ad.ad_type === "image" ? (
              <img 
                src={`${API_URL}${ad.media_url}`} 
                alt={ad.title} 
                className="w-full h-full object-cover"
              />
            ) : (
              <video 
                src={`${API_URL}${ad.media_url}`} 
                className="w-full h-full object-cover"
              />
            )
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              {ad.ad_type === "image" ? <FileImage className="w-8 h-8 text-neutral-600" /> : <FileVideo className="w-8 h-8 text-neutral-600" />}
            </div>
          )}
        </div>
        
        {/* Ad Info */}
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-lg">{ad.title}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-1 rounded-full text-xs ${badge.bg} ${badge.text}`}>
                  {badge.label}
                </span>
                {ad.package_name && (
                  <span className="px-2 py-1 rounded-full text-xs bg-purple-500/10 text-purple-400">
                    {ad.package_name}
                  </span>
                )}
              </div>
            </div>
            <div className="text-right">
              <div className="text-xl font-bold text-green-400">
                KES {(ad.package_price || 0).toLocaleString()}
              </div>
            </div>
          </div>
          
          {/* Stats */}
          <div className="flex flex-wrap gap-4 mt-4 text-sm">
            <div className="flex items-center gap-1 text-neutral-400">
              <Eye className="w-4 h-4" />
              <span>{ad.impressions || 0} views</span>
            </div>
            <div className="flex items-center gap-1 text-neutral-400">
              <MousePointer className="w-4 h-4" />
              <span>{ad.clicks || 0} clicks</span>
            </div>
            {ad.expires_at && (
              <div className="flex items-center gap-1 text-neutral-400">
                <Clock className="w-4 h-4" />
                <span>Expires: {new Date(ad.expires_at).toLocaleDateString()}</span>
              </div>
            )}
          </div>
          
          {/* Rejection Reason */}
          {ad.status === "rejected" && ad.rejection_reason && (
            <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-center gap-2 text-red-400">
                <AlertCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Rejection Reason:</span>
              </div>
              <p className="text-sm text-neutral-300 mt-1">{ad.rejection_reason}</p>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex gap-2 mt-4">
            {ad.status === "approved" && (
              <Button
                size="sm"
                onClick={() => onPayClick(ad)}
                className="bg-green-600 hover:bg-green-700"
                data-testid={`pay-btn-${ad.id}`}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Pay Now
              </Button>
            )}
            {ad.status === "pending_approval" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onDelete(ad.id)}
                className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                data-testid={`delete-btn-${ad.id}`}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            )}
            {ad.click_url && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => window.open(ad.click_url, '_blank')}
                className="border-neutral-700"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View Link
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Payment Modal
const PaymentModal = ({ ad, onClose, onSuccess }) => {
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePay = async () => {
    if (!phone || phone.length < 9) {
      toast.error("Please enter a valid phone number");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/ads/${ad.id}/pay`,
        { phone_number: phone },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } }
      );
      
      if (response.data.success) {
        toast.success(response.data.message);
        onSuccess();
        onClose();
      } else {
        toast.error(response.data.message || "Payment failed");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Payment failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-neutral-900 rounded-xl max-w-md w-full p-6 border border-neutral-800">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Complete Payment</h2>
          <button onClick={onClose} className="p-2 hover:bg-neutral-800 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 bg-neutral-800 rounded-lg mb-6">
          <div className="flex justify-between items-center">
            <span className="text-neutral-400">Ad:</span>
            <span className="font-medium">{ad.title}</span>
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-neutral-400">Package:</span>
            <span className="font-medium text-purple-400">{ad.package_name}</span>
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-neutral-400">Amount:</span>
            <span className="font-bold text-2xl text-green-400">KES {(ad.package_price || 0).toLocaleString()}</span>
          </div>
        </div>
        
        <div className="mb-6">
          <label className="block text-sm text-neutral-400 mb-2">M-Pesa Phone Number</label>
          <div className="flex items-center bg-neutral-800 border border-neutral-700 rounded-lg">
            <span className="px-4 text-neutral-500">+254</span>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 9))}
              className="flex-1 bg-transparent px-2 py-3 focus:outline-none"
              placeholder="712345678"
              data-testid="payment-phone-input"
            />
          </div>
          <p className="text-xs text-neutral-500 mt-2">
            An STK Push will be sent to this number. Confirm payment on your phone.
          </p>
        </div>
        
        <div className="flex gap-3">
          <Button variant="outline" onClick={onClose} className="flex-1 border-neutral-700">
            Cancel
          </Button>
          <Button 
            onClick={handlePay} 
            disabled={loading || !phone} 
            className="flex-1 bg-green-600 hover:bg-green-700"
            data-testid="confirm-payment-btn"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Phone className="w-4 h-4 mr-2" />
                Pay via M-Pesa
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

// My Ads Page
const MyAdsPage = () => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [payingAd, setPayingAd] = useState(null);

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAds = async () => {
    try {
      const response = await axios.get(`${API_URL}/ads/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      setAds(response.data);
    } catch (error) {
      toast.error("Failed to load ads");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (adId) => {
    if (!window.confirm("Are you sure you want to cancel this ad?")) return;
    
    try {
      await axios.delete(`${API_URL}/ads/${adId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      toast.success("Ad cancelled");
      fetchAds();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to cancel ad");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Ads</h1>
          <p className="text-neutral-400">Manage your advertising campaigns</p>
        </div>
        <Button 
          onClick={() => setShowUploadForm(!showUploadForm)}
          className="bg-blue-600 hover:bg-blue-700"
          data-testid="create-ad-btn"
        >
          <Upload className="w-4 h-4 mr-2" />
          {showUploadForm ? "Hide Form" : "Create New Ad"}
        </Button>
      </div>

      {showUploadForm && (
        <AdUploadForm onSuccess={() => { setShowUploadForm(false); fetchAds(); }} />
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      ) : ads.length === 0 ? (
        <div className="dashboard-card text-center py-12">
          <Package className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Ads Yet</h3>
          <p className="text-neutral-400 mb-4">Create your first ad campaign to get started.</p>
          <Button 
            onClick={() => setShowUploadForm(true)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Upload className="w-4 h-4 mr-2" />
            Create Ad
          </Button>
        </div>
      ) : (
        <div className="space-y-4" data-testid="ads-list">
          {ads.map(ad => (
            <AdCard 
              key={ad.id} 
              ad={ad} 
              onPayClick={setPayingAd}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {payingAd && (
        <PaymentModal 
          ad={payingAd} 
          onClose={() => setPayingAd(null)} 
          onSuccess={fetchAds}
        />
      )}
    </div>
  );
};

// Advertiser Overview Page
const AdvertiserOverview = () => {
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    pending: 0,
    impressions: 0
  });
  const [packages, setPackages] = useState([]);
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      const [adsRes, pkgRes] = await Promise.all([
        axios.get(`${API_URL}/ads/`, { headers: { Authorization: `Bearer ${getAuthToken()}` } }),
        axios.get(`${API_URL}/ad-packages/`)
      ]);
      
      const ads = adsRes.data;
      setStats({
        total: ads.length,
        active: ads.filter(a => a.status === "active").length,
        pending: ads.filter(a => a.status === "pending_approval").length,
        impressions: ads.reduce((sum, a) => sum + (a.impressions || 0), 0)
      });
      setPackages(pkgRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Welcome to CAIWAVE Ads</h1>
        <p className="text-neutral-400">Reach thousands of Wi-Fi users across Kenya</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Package className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Total Ads</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-500/10 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Active</p>
              <p className="text-2xl font-bold">{stats.active}</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-500/10 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Pending</p>
              <p className="text-2xl font-bold">{stats.pending}</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-500/10 rounded-lg">
              <Eye className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-neutral-400">Impressions</p>
              <p className="text-2xl font-bold">{stats.impressions.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Available Packages */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Advertising Packages</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {packages.map(pkg => (
            <div key={pkg.id} className="dashboard-card">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                  {getCoverageIcon(pkg.coverage_scope)}
                </div>
                <h3 className="font-semibold">{pkg.name}</h3>
              </div>
              <div className="text-2xl font-bold text-blue-400 mb-2">
                KES {pkg.price.toLocaleString()}
              </div>
              <p className="text-sm text-neutral-500 mb-4">{pkg.description}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">{pkg.duration_days} days</span>
                <Button 
                  size="sm" 
                  onClick={() => navigate('/advertiser/ads')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Get Started
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Main Advertiser Dashboard
const AdvertiserDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = getUser();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { name: "Overview", path: "/advertiser", icon: LayoutDashboard },
    { name: "My Ads", path: "/advertiser/ads", icon: Package },
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-white flex" data-testid="advertiser-dashboard">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 w-64 bg-neutral-900 border-r border-neutral-800 z-50 transform transition-transform lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        {/* Logo */}
        <div className="h-16 border-b border-neutral-800 flex items-center px-6">
          <Link to="/advertiser" className="flex items-center gap-2">
            <CaiwaveLogo size={32} />
            <span className="font-bold text-lg">CAIWAVE</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || 
              (item.path !== "/advertiser" && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-blue-600/10 text-blue-400 border-l-2 border-blue-500"
                    : "text-neutral-400 hover:bg-neutral-800 hover:text-white"
                }`}
              >
                <item.icon className="w-5 h-5" strokeWidth={1.5} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* User & Logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-neutral-800">
          <div className="px-4 py-2 mb-2">
            <p className="font-medium truncate">{user?.name}</p>
            <p className="text-neutral-500 text-sm truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-neutral-400 hover:bg-neutral-800 hover:text-white transition-colors"
          >
            <LogOut className="w-5 h-5" strokeWidth={1.5} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 lg:ml-64">
        {/* Top Bar */}
        <header className="h-16 bg-neutral-900 border-b border-neutral-800 flex items-center px-6 lg:hidden">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 rounded-lg hover:bg-neutral-800">
            <Menu className="w-6 h-6" />
          </button>
          <div className="ml-4 flex items-center gap-2">
            <CaiwaveLogo size={24} />
            <span className="font-semibold">CAIWAVE</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          <Routes>
            <Route index element={<AdvertiserOverview />} />
            <Route path="ads" element={<MyAdsPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="p-4 text-center border-t border-neutral-800">
          <p className="text-neutral-500 text-xs">
            Powered by <span className="text-blue-400 font-medium">CAIWAVE WiFi</span> © 2026. All Rights Reserved.
          </p>
        </footer>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  );
};

export default AdvertiserDashboard;
