import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
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
} from "lucide-react";
import { CaiwaveLogo } from "../../components/CaiwaveLogo";

// Helper function for status badges
const getStatusBadge = (status) => {
  const badges = {
    pending_approval: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Pending Approval" },
    approved: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Approved" },
    rejected: { bg: "bg-red-500/10", text: "text-red-400", label: "Rejected" },
    payment_enabled: { bg: "bg-purple-500/10", text: "text-purple-400", label: "Payment Ready" },
    paid: { bg: "bg-green-500/10", text: "text-green-400", label: "Paid" },
    active: { bg: "bg-green-500/10", text: "text-green-400", label: "Active" },
    suspended: { bg: "bg-red-500/10", text: "text-red-400", label: "Suspended" },
  };
  return badges[status] || { bg: "bg-gray-500/10", text: "text-gray-400", label: status };
};

// Simple Ad Upload Form
const AdUploadForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    title: "",
    ad_type: "image",
    click_url: "",
  });
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(droppedFile);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      toast.error("Please select a media file");
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
    uploadData.append("click_url", formData.click_url || "");
    uploadData.append("media", file);

    try {
      const response = await axios.post(`${API_URL}/ads/upload`, uploadData, {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.success) {
        toast.success("Ad uploaded successfully! Awaiting admin approval.");
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

  return (
    <div className="dashboard-card" data-testid="ad-upload-form">
      <h2 className="text-xl font-semibold mb-6">Create New Ad</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Ad Title */}
        <div>
          <label className="block text-sm text-neutral-400 mb-2">Ad Title *</label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3"
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
                  : "bg-neutral-900 border-neutral-800 text-neutral-400 hover:border-neutral-700"
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
                  : "bg-neutral-900 border-neutral-800 text-neutral-400 hover:border-neutral-700"
              }`}
              data-testid="ad-type-video"
            >
              <Video className="w-5 h-5" />
              <span>Short Video</span>
            </button>
          </div>
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm text-neutral-400 mb-2">
            Upload {formData.ad_type === "image" ? "Image" : "Video"} *
          </label>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive 
                ? "border-blue-500 bg-blue-500/5" 
                : "border-neutral-700 hover:border-neutral-600"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
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
                  className="absolute top-2 right-2 p-1 bg-red-500 rounded-full"
                >
                  <X className="w-4 h-4" />
                </button>
                <p className="mt-2 text-sm text-neutral-400">{file?.name}</p>
              </div>
            ) : (
              <>
                <Upload className="w-10 h-10 text-neutral-500 mx-auto mb-3" />
                <p className="text-neutral-400 mb-2">
                  Drag and drop your {formData.ad_type === "image" ? "image" : "video"} here
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

        {/* Click-through URL (Optional) */}
        <div>
          <label className="block text-sm text-neutral-400 mb-2">
            Click-through URL <span className="text-neutral-500">(Optional)</span>
          </label>
          <input
            type="url"
            value={formData.click_url}
            onChange={(e) => setFormData({ ...formData, click_url: e.target.value })}
            className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3"
            placeholder="https://yourwebsite.com"
            data-testid="ad-url-input"
          />
          <p className="text-neutral-500 text-xs mt-1">
            Users will be redirected to this URL when they click your ad
          </p>
        </div>

        {/* Submit Button */}
        <Button 
          type="submit" 
          className="w-full py-3" 
          disabled={uploading}
          data-testid="ad-submit-btn"
        >
          {uploading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Submit Ad for Approval
            </>
          )}
        </Button>
      </form>

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
        <h4 className="font-medium text-blue-400 mb-2 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          What happens next?
        </h4>
        <ol className="text-sm text-neutral-400 space-y-1 list-decimal list-inside">
          <li>Your ad will be reviewed by CAIWAVE admin</li>
          <li>If approved, admin will set a price for your ad</li>
          <li>You'll receive a payment request via M-Pesa</li>
          <li>After payment, your ad goes live on WiFi hotspots</li>
        </ol>
      </div>
    </div>
  );
};

// My Ads List
const MyAdsPage = () => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [payingAdId, setPayingAdId] = useState(null);
  const [phoneNumber, setPhoneNumber] = useState("");

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAds = async () => {
    try {
      const response = await axios.get(`${API_URL}/ads/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setAds(response.data);
    } catch (error) {
      toast.error("Failed to load ads");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (adId) => {
    if (!window.confirm("Are you sure you want to delete this ad?")) return;
    try {
      await axios.delete(`${API_URL}/ads/${adId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Ad deleted");
      fetchAds();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete ad");
    }
  };

  const handlePay = async (adId) => {
    if (!phoneNumber || phoneNumber.length < 10) {
      toast.error("Please enter a valid phone number");
      return;
    }

    try {
      const response = await axios.post(
        `${API_URL}/ads/${adId}/pay`,
        { phone_number: phoneNumber },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } }
      );

      if (response.data.success) {
        toast.success(response.data.message);
        setPayingAdId(null);
        setPhoneNumber("");
        fetchAds();
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Payment failed");
    }
  };

  const pendingCount = ads.filter(a => a.status === "pending_approval").length;
  const approvedCount = ads.filter(a => ["approved", "payment_enabled"].includes(a.status)).length;
  const activeCount = ads.filter(a => a.status === "active").length;

  return (
    <div className="space-y-6" data-testid="my-ads-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">My Ads</h1>
          <p className="text-neutral-400 mt-1">Manage your advertisements</p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)} data-testid="toggle-upload-btn">
          {showUpload ? <X className="w-4 h-4 mr-2" /> : <Upload className="w-4 h-4 mr-2" />}
          {showUpload ? "Cancel" : "Create New Ad"}
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{pendingCount}</p>
              <p className="text-neutral-400 text-sm">Pending</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{approvedCount}</p>
              <p className="text-neutral-400 text-sm">Approved</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <Play className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeCount}</p>
              <p className="text-neutral-400 text-sm">Active</p>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Form */}
      {showUpload && (
        <AdUploadForm onSuccess={() => { setShowUpload(false); fetchAds(); }} />
      )}

      {/* Ads List */}
      <div className="dashboard-card">
        <h2 className="text-lg font-semibold mb-4">All Ads</h2>
        
        {loading ? (
          <div className="text-center py-8 text-neutral-400">Loading...</div>
        ) : ads.length === 0 ? (
          <div className="text-center py-12">
            <FileImage className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <p className="text-neutral-400">You haven't created any ads yet.</p>
            <Button onClick={() => setShowUpload(true)} className="mt-4">
              <Upload className="w-4 h-4 mr-2" /> Create Your First Ad
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {ads.map((ad) => {
              const statusInfo = getStatusBadge(ad.status);
              return (
                <div key={ad.id} className="bg-neutral-900 rounded-lg p-4">
                  <div className="flex items-start gap-4">
                    {/* Media Preview */}
                    <div className="w-24 h-24 bg-neutral-800 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
                      {ad.media_url ? (
                        ad.ad_type === "image" ? (
                          <img src={`${API_URL.replace('/api', '')}${ad.media_url}`} alt={ad.title} className="w-full h-full object-cover" />
                        ) : (
                          <video src={`${API_URL.replace('/api', '')}${ad.media_url}`} className="w-full h-full object-cover" />
                        )
                      ) : (
                        ad.ad_type === "image" ? <FileImage className="w-8 h-8 text-neutral-600" /> : <FileVideo className="w-8 h-8 text-neutral-600" />
                      )}
                    </div>

                    {/* Ad Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium truncate">{ad.title}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs ${statusInfo.bg} ${statusInfo.text}`}>
                          {statusInfo.label}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-neutral-400 mb-2">
                        <span className="flex items-center gap-1">
                          {ad.ad_type === "image" ? <Image className="w-3 h-3" /> : <Video className="w-3 h-3" />}
                          {ad.ad_type === "image" ? "Image" : "Video"}
                        </span>
                        {ad.click_url && (
                          <a href={ad.click_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-blue-400 hover:underline">
                            <ExternalLink className="w-3 h-3" /> Link
                          </a>
                        )}
                      </div>

                      {/* Rejection Reason */}
                      {ad.status === "rejected" && ad.rejection_reason && (
                        <div className="bg-red-500/5 border border-red-500/20 rounded p-2 mb-2">
                          <p className="text-red-400 text-sm">
                            <XCircle className="w-3 h-3 inline mr-1" />
                            Rejected: {ad.rejection_reason}
                          </p>
                        </div>
                      )}

                      {/* Price & Payment */}
                      {ad.price > 0 && (
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-green-400 font-medium">KES {ad.price}</span>
                          {ad.status === "payment_enabled" && (
                            <span className="text-yellow-400 text-sm">• Payment required</span>
                          )}
                        </div>
                      )}

                      {/* Stats for active ads */}
                      {ad.status === "active" && (
                        <div className="flex items-center gap-4 text-sm">
                          <span className="flex items-center gap-1 text-blue-400">
                            <Eye className="w-3 h-3" /> {ad.impressions || 0} views
                          </span>
                          <span className="flex items-center gap-1 text-green-400">
                            <MousePointer className="w-3 h-3" /> {ad.clicks || 0} clicks
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2">
                      {ad.status === "payment_enabled" && (
                        <Button 
                          size="sm" 
                          onClick={() => setPayingAdId(ad.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <DollarSign className="w-3 h-3 mr-1" /> Pay Now
                        </Button>
                      )}
                      {["pending_approval", "rejected"].includes(ad.status) && (
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          className="text-red-400"
                          onClick={() => handleDelete(ad.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Payment Modal */}
                  {payingAdId === ad.id && (
                    <div className="mt-4 p-4 bg-neutral-800 rounded-lg">
                      <h4 className="font-medium mb-3">Pay for Ad: {ad.title}</h4>
                      <p className="text-neutral-400 text-sm mb-3">Amount: <span className="text-green-400 font-medium">KES {ad.price}</span></p>
                      <div className="flex gap-3">
                        <input
                          type="tel"
                          value={phoneNumber}
                          onChange={(e) => setPhoneNumber(e.target.value)}
                          placeholder="M-Pesa Number (e.g., 254712345678)"
                          className="flex-1 bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-2"
                        />
                        <Button onClick={() => handlePay(ad.id)}>Pay</Button>
                        <Button variant="outline" onClick={() => { setPayingAdId(null); setPhoneNumber(""); }}>Cancel</Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

// Advertiser Overview
const AdvertiserOverview = () => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = getUser();

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAds = async () => {
    try {
      const response = await axios.get(`${API_URL}/ads/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setAds(response.data);
    } catch (error) {
      console.error("Failed to fetch ads:", error);
    } finally {
      setLoading(false);
    }
  };

  const totalImpressions = ads.reduce((sum, ad) => sum + (ad.impressions || 0), 0);
  const totalClicks = ads.reduce((sum, ad) => sum + (ad.clicks || 0), 0);
  const activeAds = ads.filter(a => a.status === "active").length;
  const pendingAds = ads.filter(a => a.status === "pending_approval").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="advertiser-overview">
      <div>
        <h1 className="text-2xl font-bold">Welcome, {user?.name || "Advertiser"}</h1>
        <p className="text-neutral-400 mt-1">Manage your CAIWAVE advertisements</p>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center">
              <Play className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeAds}</p>
              <p className="text-neutral-400 text-sm">Active Ads</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-yellow-500/10 rounded-xl flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{pendingAds}</p>
              <p className="text-neutral-400 text-sm">Pending Approval</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center">
              <Eye className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalImpressions.toLocaleString()}</p>
              <p className="text-neutral-400 text-sm">Total Views</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center">
              <MousePointer className="w-6 h-6 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalClicks.toLocaleString()}</p>
              <p className="text-neutral-400 text-sm">Total Clicks</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-card">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <Link to="/advertiser/ads" className="p-6 bg-gradient-to-r from-blue-600/10 to-purple-600/10 rounded-xl border border-blue-600/20 hover:border-blue-500/40 transition-colors">
            <Upload className="w-8 h-8 text-blue-400 mb-3" />
            <h3 className="font-semibold mb-1">Create New Ad</h3>
            <p className="text-neutral-400 text-sm">Upload an image or video ad for approval</p>
          </Link>
          <Link to="/advertiser/ads" className="p-6 bg-gradient-to-r from-green-600/10 to-emerald-600/10 rounded-xl border border-green-600/20 hover:border-green-500/40 transition-colors">
            <Eye className="w-8 h-8 text-green-400 mb-3" />
            <h3 className="font-semibold mb-1">View My Ads</h3>
            <p className="text-neutral-400 text-sm">Check status and performance of your ads</p>
          </Link>
        </div>
      </div>

      {/* How It Works */}
      <div className="dashboard-card">
        <h2 className="text-lg font-semibold mb-4">How Advertising Works</h2>
        <div className="grid md:grid-cols-4 gap-4">
          {[
            { step: 1, title: "Upload", desc: "Submit your ad with an image or video", icon: Upload },
            { step: 2, title: "Review", desc: "CAIWAVE admin reviews and sets price", icon: Eye },
            { step: 3, title: "Pay", desc: "Complete payment via M-Pesa", icon: DollarSign },
            { step: 4, title: "Go Live", desc: "Your ad displays on WiFi hotspots", icon: Play },
          ].map((item) => (
            <div key={item.step} className="text-center">
              <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                <item.icon className="w-6 h-6 text-blue-400" />
              </div>
              <div className="text-xs text-blue-400 mb-1">Step {item.step}</div>
              <h4 className="font-medium mb-1">{item.title}</h4>
              <p className="text-neutral-500 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Main Advertiser Dashboard Layout
const AdvertiserDashboard = () => {
  const location = useLocation();
  const user = getUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: "Overview", href: "/advertiser", icon: LayoutDashboard },
    { name: "My Ads", href: "/advertiser/ads", icon: Image },
  ];

  const handleLogout = () => {
    logout();
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-white flex">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-neutral-900 border-r border-neutral-800 transform transition-transform lg:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        {/* Logo */}
        <div className="h-16 flex items-center gap-2 px-6 border-b border-neutral-800">
          <CaiwaveLogo size={32} />
          <div>
            <span className="font-semibold">CAIWAVE</span>
            <span className="ml-2 text-xs px-2 py-0.5 bg-purple-600/20 text-purple-400 rounded">
              Advertiser
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || (item.href !== "/advertiser" && location.pathname.startsWith(item.href));
            return (
              <Link
                key={item.name}
                to={item.href}
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
            <span className="mx-2">|</span>
            <a href="tel:0738570630" className="text-neutral-500 hover:text-blue-400 transition-colors">Support</a>
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
