import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { getUser, logout, getAuthToken } from "../../lib/auth";
import { API_URL, formatCurrency } from "../../lib/utils";
import axios from "axios";
import { toast } from "sonner";
import {
  LayoutDashboard,
  Radio,
  Users,
  Package,
  Megaphone,
  Settings,
  LogOut,
  Menu,
  TrendingUp,
  DollarSign,
  Activity,
  Plus,
  Edit,
  Trash2,
  BarChart3,
  Target,
  Globe,
  Check,
  X,
  Clock,
  Eye,
  AlertCircle,
  ShoppingBag,
  Sliders,
  Bell,
  Tv,
  Calendar,
  Zap,
  Play,
  Pause,
  Video,
  Image,
  MousePointer,
  FileText,
  CreditCard,
  CheckCircle,
  Ban,
  RefreshCw,
  StopCircle,
} from "lucide-react";
import { CaiwaveLogo } from "../../components/CaiwaveLogo";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// Admin Overview Component
const AdminOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/analytics/dashboard`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const revenueData = [
    { name: "Mon", revenue: 4500, sessions: 120 },
    { name: "Tue", revenue: 5200, sessions: 145 },
    { name: "Wed", revenue: 6800, sessions: 178 },
    { name: "Thu", revenue: 5900, sessions: 162 },
    { name: "Fri", revenue: 8200, sessions: 210 },
    { name: "Sat", revenue: 9500, sessions: 245 },
    { name: "Sun", revenue: 7800, sessions: 198 },
  ];

  const packageData = [
    { name: "KES 5", value: 25, color: "#2563eb" },
    { name: "KES 15", value: 22, color: "#7c3aed" },
    { name: "KES 25", value: 20, color: "#10b981" },
    { name: "KES 30", value: 12, color: "#f59e0b" },
    { name: "KES 35", value: 15, color: "#ef4444" },
    { name: "KES 200", value: 4, color: "#06b6d4" },
    { name: "KES 600", value: 2, color: "#ec4899" },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="admin-dashboard">
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="text-neutral-400 mt-1">Platform-wide overview and management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card stat-card-success">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Total Revenue</p>
              <p className="text-2xl font-bold mt-1">
                {formatCurrency(stats?.total_revenue || 0)}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-green-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-green-400 text-sm mt-3 flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            Partner: 30-50% | CAIWAVE: 50-70%
          </p>
        </div>

        <div className="stat-card stat-card-primary">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Total Hotspots</p>
              <p className="text-2xl font-bold mt-1">{stats?.total_hotspots || 0}</p>
            </div>
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Radio className="w-6 h-6 text-blue-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-neutral-400 text-sm mt-3">
            {stats?.active_hotspots || 0} active
          </p>
        </div>

        <div className="stat-card stat-card-warning">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Pending Ads</p>
              <p className="text-2xl font-bold mt-1">{stats?.pending_ads || 0}</p>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-500" strokeWidth={1.5} />
            </div>
          </div>
          <Link to="/admin/ads" className="text-yellow-400 text-sm mt-3 flex items-center gap-1 hover:underline">
            Review pending ads →
          </Link>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Active Ads</p>
              <p className="text-2xl font-bold mt-1">{stats?.active_ads || 0}</p>
            </div>
            <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
              <Megaphone className="w-6 h-6 text-purple-500" strokeWidth={1.5} />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <div className="lg:col-span-2 dashboard-card p-6">
          <h2 className="font-semibold mb-6">Weekly Revenue</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueData}>
                <defs>
                  <linearGradient id="adminRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    border: "1px solid #27272a",
                    borderRadius: "8px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#2563eb"
                  fillOpacity={1}
                  fill="url(#adminRevenue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Package Distribution */}
        <div className="dashboard-card p-6">
          <h2 className="font-semibold mb-6">Package Distribution</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={packageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  dataKey="value"
                >
                  {packageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    border: "1px solid #27272a",
                    borderRadius: "8px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {packageData.slice(0, 4).map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-neutral-400">
                  {item.name} ({item.value}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to determine ad's live status based on dates
const getAdLiveStatus = (ad) => {
  if (ad.status !== "active") return null;
  
  const now = new Date();
  const startsAt = ad.starts_at ? new Date(ad.starts_at) : null;
  const expiresAt = ad.expires_at ? new Date(ad.expires_at) : null;
  
  if (!startsAt || !expiresAt) return { status: "live", label: "Live", color: "green" };
  
  if (now < startsAt) {
    return { status: "scheduled", label: "Scheduled", color: "blue" };
  } else if (now > expiresAt) {
    return { status: "ended", label: "Ended", color: "gray" };
  } else {
    return { status: "live", label: "Live", color: "green" };
  }
};

// Helper to check if date is today or yesterday
const getDateCategory = (dateStr) => {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  const isToday = date.toDateString() === today.toDateString();
  const isYesterday = date.toDateString() === yesterday.toDateString();
  
  if (isToday) return "today";
  if (isYesterday) return "yesterday";
  return "older";
};

// Format date for display
const formatAdDate = (dateStr) => {
  if (!dateStr) return "Not set";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", { 
    day: "2-digit", 
    month: "short", 
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

// Ad Approval Page - CRITICAL FOR CAIWAVE ADMIN
const AdApprovalPage = () => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("pending");
  const [selectedAd, setSelectedAd] = useState(null);
  const [approvalData, setApprovalData] = useState({ admin_notes: "", rejection_reason: "" });

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

  const handleApprove = async (adId) => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/approve`, {
        approved: true,
        admin_notes: approvalData.admin_notes || null,
      }, { headers: { Authorization: `Bearer ${getAuthToken()}` } });
      toast.success("Ad approved! Advertiser can now pay.");
      setSelectedAd(null);
      setApprovalData({ admin_notes: "", rejection_reason: "" });
      fetchAds();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to approve ad");
    }
  };

  const handleReject = async (adId) => {
    if (!approvalData.rejection_reason) {
      toast.error("Please provide a rejection reason");
      return;
    }
    try {
      await axios.post(`${API_URL}/ads/${adId}/approve`, {
        approved: false,
        rejection_reason: approvalData.rejection_reason,
      }, { headers: { Authorization: `Bearer ${getAuthToken()}` } });
      toast.success("Ad rejected");
      setSelectedAd(null);
      setApprovalData({ admin_notes: "", rejection_reason: "" });
      fetchAds();
    } catch (error) {
      toast.error("Failed to reject ad");
    }
  };

  const handleActivate = async (adId) => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/activate`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Ad is now LIVE!");
      fetchAds();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to activate ad");
    }
  };

  const handleSuspend = async (adId) => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/suspend`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Ad suspended");
      fetchAds();
    } catch (error) {
      toast.error("Failed to suspend ad");
    }
  };

  const handleReactivate = async (adId) => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/reactivate`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Ad reactivated");
      fetchAds();
    } catch (error) {
      toast.error("Failed to reactivate ad");
    }
  };

  const getStatusBadge = (ad) => {
    const status = ad.status;
    const liveStatus = getAdLiveStatus(ad);
    
    // For active ads, show live status
    if (status === "active" && liveStatus) {
      const badges = {
        live: { bg: "bg-green-500/20", text: "text-green-400", label: "🟢 Live", border: "border-green-500/30" },
        scheduled: { bg: "bg-blue-500/20", text: "text-blue-400", label: "📅 Scheduled", border: "border-blue-500/30" },
        ended: { bg: "bg-gray-500/20", text: "text-gray-400", label: "⏹️ Ended", border: "border-gray-500/30" },
      };
      return badges[liveStatus.status] || badges.live;
    }
    
    const badges = {
      pending_approval: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "⏳ Pending", border: "border-yellow-500/30" },
      approved: { bg: "bg-blue-500/20", text: "text-blue-400", label: "✓ Approved", border: "border-blue-500/30" },
      rejected: { bg: "bg-red-500/20", text: "text-red-400", label: "✗ Rejected", border: "border-red-500/30" },
      paid: { bg: "bg-purple-500/20", text: "text-purple-400", label: "💳 Paid", border: "border-purple-500/30" },
      active: { bg: "bg-green-500/20", text: "text-green-400", label: "🟢 Live", border: "border-green-500/30" },
      suspended: { bg: "bg-red-500/20", text: "text-red-400", label: "⛔ Suspended", border: "border-red-500/30" },
    };
    return badges[status] || { bg: "bg-gray-500/20", text: "text-gray-400", label: status, border: "border-gray-500/30" };
  };

  // Filter ads and categorize
  const pendingAds = ads.filter(a => a.status === "pending_approval");
  const approvedAds = ads.filter(a => a.status === "approved");
  const paidAds = ads.filter(a => a.status === "paid");
  const activeAds = ads.filter(a => a.status === "active");
  const otherAds = ads.filter(a => ["rejected", "suspended"].includes(a.status));
  
  // Separate live vs ended active ads
  const liveAds = activeAds.filter(a => {
    const status = getAdLiveStatus(a);
    return status?.status === "live" || status?.status === "scheduled";
  });
  const endedAds = activeAds.filter(a => {
    const status = getAdLiveStatus(a);
    return status?.status === "ended";
  });
  
  // Today's and Yesterday's ads for quick filtering
  const todayAds = ads.filter(a => getDateCategory(a.starts_at) === "today");
  const yesterdayAds = ads.filter(a => getDateCategory(a.starts_at) === "yesterday");

  const getFilteredAds = () => {
    switch (activeTab) {
      case "pending": return pendingAds;
      case "approved": return approvedAds;
      case "paid": return paidAds;
      case "live": return liveAds;
      case "ended": return endedAds;
      case "today": return todayAds;
      case "yesterday": return yesterdayAds;
      case "other": return otherAds;
      default: return ads;
    }
  };

  return (
    <div className="space-y-6" data-testid="ad-approval-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Ad Management</h1>
          <p className="text-neutral-400 mt-1">Review, approve, and manage advertiser submissions</p>
        </div>
        {pendingAds.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <AlertCircle className="w-5 h-5 text-yellow-500" />
            <span className="text-yellow-400 text-sm font-medium">
              {pendingAds.length} pending review
            </span>
          </div>
        )}
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="dashboard-card bg-green-500/5 border-green-500/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <Play className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-400">{liveAds.length}</p>
              <p className="text-xs text-neutral-400">Live Now</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card bg-yellow-500/5 border-yellow-500/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-500/10">
              <Clock className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-400">{pendingAds.length}</p>
              <p className="text-xs text-neutral-400">Pending</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card bg-blue-500/5 border-blue-500/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Calendar className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400">{todayAds.length}</p>
              <p className="text-xs text-neutral-400">Today</p>
            </div>
          </div>
        </div>
        <div className="dashboard-card bg-gray-500/5 border-gray-500/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-500/10">
              <Ban className="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-400">{endedAds.length}</p>
              <p className="text-xs text-neutral-400">Ended</p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Flow Info */}
      <div className="dashboard-card bg-blue-500/5 border-blue-500/20">
        <h3 className="font-medium text-blue-400 mb-2">Package-Based Ad Flow</h3>
        <div className="flex items-center gap-2 text-sm text-neutral-400 flex-wrap">
          <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 rounded">⏳ Pending</span>
          <span>→</span>
          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded">✓ Approved</span>
          <span>→</span>
          <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded">💳 Paid</span>
          <span>→</span>
          <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded">🟢 Live</span>
          <span>→</span>
          <span className="px-2 py-1 bg-gray-500/10 text-gray-400 rounded">⏹️ Ended</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-neutral-800 pb-2 overflow-x-auto">
        {[
          { id: "pending", label: "Pending", count: pendingAds.length, color: "yellow" },
          { id: "approved", label: "Approved", count: approvedAds.length, color: "blue" },
          { id: "paid", label: "Paid", count: paidAds.length, color: "purple" },
          { id: "live", label: "🟢 Live", count: liveAds.length, color: "green" },
          { id: "ended", label: "Ended", count: endedAds.length, color: "gray" },
          { id: "today", label: "📅 Today", count: todayAds.length, color: "cyan" },
          { id: "yesterday", label: "Yesterday", count: yesterdayAds.length, color: "slate" },
          { id: "other", label: "Rejected", count: otherAds.length, color: "red" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? `bg-${tab.color}-500/20 text-${tab.color}-400 border border-${tab.color}-500/30`
                : "text-neutral-400 hover:text-white hover:bg-neutral-800"
            }`}
            data-testid={`tab-${tab.id}`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Ads List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : getFilteredAds().length === 0 ? (
          <div className="dashboard-card p-12 text-center">
            <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No ads in this category</h3>
            <p className="text-neutral-400 text-sm">
              {activeTab === "pending" ? "All caught up! No ads pending review." : "No ads found."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {getFilteredAds().map((ad) => {
              const statusInfo = getStatusBadge(ad);
              const mediaUrl = ad.media_url ? `${API_URL.replace('/api', '')}${ad.media_url}` : null;
              const liveStatus = getAdLiveStatus(ad);
              
              return (
                <div key={ad.id} className="dashboard-card overflow-hidden hover:border-neutral-600 transition-colors">
                  {/* Image Thumbnail */}
                  <div className="relative w-full h-48 bg-neutral-900 -mx-6 -mt-6 mb-4">
                    {mediaUrl && ad.ad_type === "image" ? (
                      <img 
                        src={mediaUrl} 
                        alt={ad.title} 
                        className="w-full h-full object-cover"
                      />
                    ) : mediaUrl && ad.ad_type === "video" ? (
                      <video 
                        src={mediaUrl} 
                        className="w-full h-full object-cover" 
                        muted
                        onMouseEnter={(e) => e.target.play()}
                        onMouseLeave={(e) => { e.target.pause(); e.target.currentTime = 0; }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-neutral-800 to-neutral-900">
                        <Image className="w-16 h-16 text-neutral-600" />
                      </div>
                    )}
                    
                    {/* Status Badge Overlay */}
                    <div className="absolute top-3 left-3">
                      <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${statusInfo.bg} ${statusInfo.text} border ${statusInfo.border} backdrop-blur-sm`}>
                        {statusInfo.label}
                      </span>
                    </div>
                    
                    {/* Price Badge */}
                    {(ad.package_price > 0 || ad.price > 0) && (
                      <div className="absolute top-3 right-3">
                        <span className="px-3 py-1.5 rounded-full text-sm font-bold bg-black/70 text-green-400 backdrop-blur-sm">
                          KES {(ad.package_price || ad.price || 0).toLocaleString()}
                        </span>
                      </div>
                    )}
                    
                    {/* Video indicator */}
                    {ad.ad_type === "video" && (
                      <div className="absolute bottom-3 left-3 flex items-center gap-1 px-2 py-1 bg-black/70 rounded text-xs">
                        <Video className="w-3 h-3 text-blue-400" />
                        <span className="text-white">{ad.duration_seconds || 0}s</span>
                      </div>
                    )}
                  </div>

                  {/* Ad Content */}
                  <div className="space-y-3">
                    {/* Title & Type */}
                    <div>
                      {ad.click_url ? (
                        <a 
                          href={ad.click_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="font-semibold text-lg hover:text-blue-400 transition-colors flex items-center gap-2"
                        >
                          {ad.title}
                          <Globe className="w-4 h-4 text-blue-400" />
                        </a>
                      ) : (
                        <h3 className="font-semibold text-lg">{ad.title}</h3>
                      )}
                      <p className="text-neutral-500 text-sm">
                        {ad.ad_type === "image" ? "📷 Image Banner" : "🎬 Video Ad"} • 
                        {ad.media_size_bytes ? ` ${(ad.media_size_bytes / 1024 / 1024).toFixed(1)}MB` : ""}
                      </p>
                      {ad.click_url && (
                        <p className="text-blue-400 text-xs mt-1 truncate" title={ad.click_url}>
                          🔗 {ad.click_url}
                        </p>
                      )}
                    </div>

                    {/* Date Tracking Info */}
                    <div className="grid grid-cols-2 gap-3 p-3 bg-neutral-900/50 rounded-lg">
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">Go-Live Date</p>
                        <p className="text-sm text-green-400 font-medium">
                          {ad.starts_at ? formatAdDate(ad.starts_at) : "Not started"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-neutral-500 mb-1">End Date</p>
                        <p className="text-sm text-red-400 font-medium">
                          {ad.expires_at ? formatAdDate(ad.expires_at) : "Not set"}
                        </p>
                      </div>
                    </div>

                    {/* Package & Coverage Info */}
                    {ad.package_name && (
                      <div className="flex flex-wrap gap-2">
                        <span className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-full">
                          📦 {ad.package_name}
                        </span>
                        {ad.targeting?.is_national && (
                          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-full">
                            🌍 National
                          </span>
                        )}
                        {ad.targeting?.counties?.length > 0 && (
                          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-full">
                            🏛️ {ad.targeting.counties.join(", ")}
                          </span>
                        )}
                        {ad.targeting?.constituencies?.length > 0 && (
                          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-full">
                            📍 {ad.targeting.constituencies.length} areas
                          </span>
                        )}
                      </div>
                    )}

                    {/* Stats for active/ended ads */}
                    {(ad.status === "active" || liveStatus?.status === "ended") && (
                      <div className="flex gap-4 py-2 border-t border-neutral-800">
                        <div className="flex items-center gap-2">
                          <Eye className="w-4 h-4 text-blue-400" />
                          <span className="text-blue-400 font-medium">{ad.impressions || 0}</span>
                          <span className="text-neutral-500 text-xs">views</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <MousePointer className="w-4 h-4 text-green-400" />
                          <span className="text-green-400 font-medium">{ad.clicks || 0}</span>
                          <span className="text-neutral-500 text-xs">clicks</span>
                        </div>
                      </div>
                    )}

                    {/* Rejection reason */}
                    {ad.status === "rejected" && ad.rejection_reason && (
                      <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3">
                        <p className="text-red-400 text-sm">❌ {ad.rejection_reason}</p>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-2 border-t border-neutral-800">
                      {ad.status === "pending_approval" && (
                        <Button
                          onClick={() => setSelectedAd(selectedAd?.id === ad.id ? null : ad)}
                          className="bg-blue-600 hover:bg-blue-700 flex-1"
                        >
                          Review Ad
                        </Button>
                      )}
                      
                      {ad.status === "approved" && (
                        <span className="text-blue-400 text-sm py-2">⏳ Awaiting payment...</span>
                      )}
                      
                      {ad.status === "paid" && (
                        <Button onClick={() => handleActivate(ad.id)} className="bg-green-600 hover:bg-green-700 flex-1">
                          <Play className="w-4 h-4 mr-2" /> Go Live
                        </Button>
                      )}
                      
                      {ad.status === "active" && liveStatus?.status === "live" && (
                        <Button onClick={() => handleSuspend(ad.id)} variant="outline" className="border-red-600 text-red-400 flex-1">
                          <Pause className="w-4 h-4 mr-2" /> Suspend
                        </Button>
                      )}
                      
                      {ad.status === "suspended" && (
                        <Button onClick={() => handleReactivate(ad.id)} className="bg-green-600 hover:bg-green-700 flex-1">
                          <RefreshCw className="w-4 h-4 mr-2" /> Reactivate
                        </Button>
                      )}
                    </div>

                    {/* Approval Form */}
                    {selectedAd?.id === ad.id && ad.status === "pending_approval" && (
                      <div className="mt-4 p-4 bg-neutral-900 rounded-lg space-y-4 border border-neutral-700">
                        <h4 className="font-medium">Review: {ad.title}</h4>
                        
                        <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-neutral-400">Package:</span>
                            <span className="font-semibold text-purple-400">{ad.package_name}</span>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-neutral-400">Price:</span>
                            <span className="font-bold text-green-400">KES {(ad.package_price || 0).toLocaleString()}</span>
                          </div>
                        </div>
                        
                        <div>
                          <label className="block text-sm text-neutral-400 mb-1">Admin Notes (optional)</label>
                          <input
                            type="text"
                            value={approvalData.admin_notes}
                            onChange={(e) => setApprovalData({ ...approvalData, admin_notes: e.target.value })}
                            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2"
                            placeholder="Notes about coverage validation..."
                          />
                        </div>

                        <div className="flex gap-3">
                          <Button onClick={() => handleApprove(ad.id)} className="bg-green-600 hover:bg-green-700">
                            <Check className="w-4 h-4 mr-2" /> Approve
                          </Button>
                          <Button variant="outline" onClick={() => setSelectedAd(null)}>Cancel</Button>
                        </div>

                        <div className="border-t border-neutral-800 pt-4">
                          <label className="block text-sm text-neutral-400 mb-1">Or Reject with Reason</label>
                          <input
                            type="text"
                            value={approvalData.rejection_reason}
                            onChange={(e) => setApprovalData({ ...approvalData, rejection_reason: e.target.value })}
                            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2 mb-2"
                            placeholder="Reason for rejection..."
                          />
                          <Button onClick={() => handleReject(ad.id)} variant="outline" className="border-red-600 text-red-400">
                            <X className="w-4 h-4 mr-2" /> Reject
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

// Packages Management Component - Updated with new pricing
const PackagesPage = () => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const response = await axios.get(`${API_URL}/packages?active_only=false`);
      setPackages(response.data);
    } catch (error) {
      console.error("Failed to fetch packages:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="packages-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Internet Packages</h1>
          <p className="text-neutral-400 mt-1">Predefined pricing tiers (Partners select from dropdown)</p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-blue-400 mt-0.5" />
        <div>
          <p className="text-blue-400 font-medium">Fixed Package Pricing</p>
          <p className="text-neutral-400 text-sm mt-1">
            Packages are predefined by CAIWAVE. Hotspot owners can only enable/disable packages for their locations - they cannot modify pricing or create new packages.
          </p>
        </div>
      </div>

      {/* Packages Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          packages.map((pkg) => (
            <div key={pkg.id} className="dashboard-card p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-semibold">{pkg.name}</h3>
                  <p className="text-sm text-neutral-400">{pkg.description}</p>
                </div>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    pkg.is_active ? "badge-active" : "badge-inactive"
                  }`}
                >
                  {pkg.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-neutral-400">Price</span>
                  <span className="font-bold text-xl">{formatCurrency(pkg.price)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">Duration</span>
                  <span>{pkg.duration_minutes} min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">Speed</span>
                  <span>{pkg.speed_mbps} Mbps</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Seed Button */}
      <div className="dashboard-card p-6">
        <h3 className="font-semibold mb-2">Reset to Default Packages</h3>
        <p className="text-neutral-400 text-sm mb-4">
          Reset packages to: KES 5 (30min), KES 15 (4hr), KES 25 (8hr), KES 30 (12hr), KES 35 (24hr), KES 200 (1wk), KES 600 (1mo)
        </p>
        <Button
          onClick={async () => {
            try {
              await axios.post(`${API_URL}/seed`);
              toast.success("Packages reset to defaults");
              fetchPackages();
            } catch (error) {
              toast.error("Failed to reset packages");
            }
          }}
          variant="outline"
          className="border-neutral-700"
        >
          <Package className="w-4 h-4 mr-2" />
          Reset Default Packages
        </Button>
      </div>
    </div>
  );
};

// Revenue Settings Page
const RevenueSettingsPage = () => {
  const [config, setConfig] = useState({
    base_owner_percentage: 30,
    coverage_bonus_per_100sqm: 0.5,
    client_bonus_per_10: 0.5,
    ad_impression_bonus_per_1000: 1.0,
    uptime_bonus_threshold: 99,
    uptime_bonus_percentage: 2.0,
    max_owner_percentage: 50,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/settings/revenue-config`);
      setConfig(response.data);
    } catch (error) {
      console.error("Failed to fetch config:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API_URL}/settings/revenue-config`, config);
      toast.success("Revenue configuration saved");
    } catch (error) {
      toast.error("Failed to save configuration");
    } finally {
      setSaving(false);
    }
  };

  // Calculate example with new values
  const calculateExample = () => {
    const base = config.base_owner_percentage;
    const coverage = Math.min((200 / 100) * config.coverage_bonus_per_100sqm, 5);
    const clients = Math.min((50 / 10) * config.client_bonus_per_10, 5);
    const ads = Math.min((5000 / 1000) * config.ad_impression_bonus_per_1000, 5);
    const uptime = config.uptime_bonus_percentage;
    const total = base + coverage + clients + ads + uptime;
    const capped = total > config.max_owner_percentage;
    return {
      base,
      coverage: coverage.toFixed(1),
      clients: clients.toFixed(1),
      ads: ads.toFixed(1),
      uptime,
      total: Math.min(total, config.max_owner_percentage).toFixed(1),
      capped
    };
  };

  const example = calculateExample();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="revenue-settings">
      <div>
        <h1 className="text-2xl font-bold">Dynamic Revenue Sharing</h1>
        <p className="text-neutral-400 mt-1">Configure how revenue is split between CAIWAVE and partners</p>
      </div>

      {/* Info Banner */}
      <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg flex items-start gap-3">
        <Sliders className="w-5 h-5 text-purple-400 mt-0.5" />
        <div>
          <p className="text-purple-400 font-medium">Dynamic Revenue Formula</p>
          <p className="text-neutral-400 text-sm mt-1">
            Partner % = Base ({config.base_owner_percentage}%) + Coverage Bonus + Client Bonus + Ad Bonus + Uptime Bonus
          </p>
          <p className="text-yellow-400 text-sm mt-1">
            ⚠️ Total partner share is capped at {config.max_owner_percentage}% maximum
          </p>
        </div>
      </div>

      <div className="dashboard-card p-6 space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-neutral-400">Base Partner Percentage</label>
            <input
              type="number"
              value={config.base_owner_percentage}
              onChange={(e) => setConfig({ ...config, base_owner_percentage: parseFloat(e.target.value) })}
              className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              min="0"
              max="100"
            />
            <p className="text-xs text-neutral-500 mt-1">Starting percentage for all partners (default: 30%)</p>
          </div>

          <div>
            <label className="text-sm text-neutral-400">Max Partner Percentage (Cap)</label>
            <input
              type="number"
              value={config.max_owner_percentage}
              onChange={(e) => setConfig({ ...config, max_owner_percentage: parseFloat(e.target.value) })}
              className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              min="0"
              max="100"
            />
            <p className="text-xs text-neutral-500 mt-1">Maximum cap regardless of bonuses (default: 50%)</p>
          </div>

          <div>
            <label className="text-sm text-neutral-400">Coverage Bonus (per 100 sqm)</label>
            <input
              type="number"
              value={config.coverage_bonus_per_100sqm}
              onChange={(e) => setConfig({ ...config, coverage_bonus_per_100sqm: parseFloat(e.target.value) })}
              className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              step="0.1"
            />
            <p className="text-xs text-neutral-500 mt-1">Bonus % per 100 sqm coverage area (max +5%)</p>
          </div>

          <div>
            <label className="text-sm text-neutral-400">Client Bonus (per 10 daily clients)</label>
            <input
              type="number"
              value={config.client_bonus_per_10}
              onChange={(e) => setConfig({ ...config, client_bonus_per_10: parseFloat(e.target.value) })}
              className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              step="0.1"
            />
            <p className="text-xs text-neutral-500 mt-1">Bonus % per 10 average daily clients (max +5%)</p>
          </div>

          <div>
            <label className="text-sm text-neutral-400">Ad Impression Bonus (per 1000 impressions)</label>
            <input
              type="number"
              value={config.ad_impression_bonus_per_1000}
              onChange={(e) => setConfig({ ...config, ad_impression_bonus_per_1000: parseFloat(e.target.value) })}
              className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              step="0.1"
            />
            <p className="text-xs text-neutral-500 mt-1">Bonus % per 1000 ad impressions delivered (max +5%)</p>
          </div>

          <div>
            <label className="text-sm text-neutral-400">Uptime Bonus Percentage</label>
            <input
              type="number"
              value={config.uptime_bonus_percentage}
              onChange={(e) => setConfig({ ...config, uptime_bonus_percentage: parseFloat(e.target.value) })}
              className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              step="0.1"
            />
            <p className="text-xs text-neutral-500 mt-1">
              Bonus when uptime ≥ {config.uptime_bonus_threshold}%
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-neutral-800">
          <Button
            onClick={handleSave}
            className="bg-blue-600 hover:bg-blue-700"
            disabled={saving}
          >
            {saving ? "Saving..." : "Save Configuration"}
          </Button>
        </div>
      </div>

      {/* Example Calculation */}
      <div className="dashboard-card p-6">
        <h3 className="font-semibold mb-4">Example Calculation</h3>
        <div className="space-y-2 text-sm">
          <p className="text-neutral-400">For a hotspot with 200sqm coverage, 50 daily clients, 5000 ad impressions, 99.5% uptime:</p>
          <div className="bg-neutral-900 rounded-lg p-4 font-mono text-xs">
            <p>Base: {example.base}%</p>
            <p>+ Coverage (200/100 × {config.coverage_bonus_per_100sqm}): {example.coverage}%</p>
            <p>+ Clients (50/10 × {config.client_bonus_per_10}): {example.clients}%</p>
            <p>+ Ad Impressions (5000/1000 × {config.ad_impression_bonus_per_1000}): {example.ads}%</p>
            <p>+ Uptime Bonus: {example.uptime}%</p>
            <p className="border-t border-neutral-700 pt-2 mt-2 text-green-400">
              Total: {example.total}% {example.capped && <span className="text-yellow-400">(capped at {config.max_owner_percentage}%)</span>}
            </p>
            <p className="text-blue-400 mt-2">
              CAIWAVE receives: {(100 - parseFloat(example.total)).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Revenue Split Summary */}
      <div className="dashboard-card p-6">
        <h3 className="font-semibold mb-4">Revenue Split Summary</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <p className="text-green-400 text-sm">Partner Share</p>
            <p className="text-2xl font-bold text-green-400">{config.base_owner_percentage}% - {config.max_owner_percentage}%</p>
            <p className="text-neutral-500 text-xs mt-1">Base + bonuses (capped)</p>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
            <p className="text-blue-400 text-sm">CAIWAVE Share</p>
            <p className="text-2xl font-bold text-blue-400">{100 - config.max_owner_percentage}% - {100 - config.base_owner_percentage}%</p>
            <p className="text-neutral-500 text-xs mt-1">Platform revenue</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Integration Settings Page
const IntegrationSettingsPage = () => {
  const [activeTab, setActiveTab] = useState("mpesa");
  const [mpesaStatus, setMpesaStatus] = useState(null);
  const [radiusConfig, setRadiusConfig] = useState(null);
  const [nasClients, setNasClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddNAS, setShowAddNAS] = useState(false);
  const [editingNAS, setEditingNAS] = useState(null);
  const [nasForm, setNasForm] = useState({
    name: "",
    ip_address: "",
    secret: "",
    nastype: "mikrotik",
    location: "",
    description: "",
  });
  const [generatedConfig, setGeneratedConfig] = useState(null);

  useEffect(() => {
    fetchAllConfigs();
  }, []);

  const fetchAllConfigs = async () => {
    try {
      const [mpesa, radius, nas] = await Promise.all([
        axios.get(`${API_URL}/mpesa/config-status`, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }).catch(() => ({ data: { configured: false } })),
        axios.get(`${API_URL}/radius/config`, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }).catch(() => ({ data: { enabled: false } })),
        axios.get(`${API_URL}/radius/nas-clients`, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }).catch(() => ({ data: [] })),
      ]);
      setMpesaStatus(mpesa.data);
      setRadiusConfig(radius.data);
      setNasClients(nas.data);
    } catch (error) {
      console.error("Failed to fetch configs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNAS = async (e) => {
    e.preventDefault();
    try {
      if (editingNAS) {
        await axios.put(`${API_URL}/radius/nas-clients/${editingNAS.id}`, nasForm, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("NAS client updated");
      } else {
        await axios.post(`${API_URL}/radius/nas-clients`, nasForm, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("NAS client added");
      }
      setShowAddNAS(false);
      setEditingNAS(null);
      setNasForm({ name: "", ip_address: "", secret: "", nastype: "mikrotik", location: "", description: "" });
      fetchAllConfigs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save NAS client");
    }
  };

  const handleDeleteNAS = async (clientId) => {
    if (!window.confirm("Delete this NAS client?")) return;
    try {
      await axios.delete(`${API_URL}/radius/nas-clients/${clientId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("NAS client deleted");
      fetchAllConfigs();
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  const handleToggleNAS = async (clientId) => {
    try {
      await axios.post(`${API_URL}/radius/nas-clients/${clientId}/toggle`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Status updated");
      fetchAllConfigs();
    } catch (error) {
      toast.error("Failed to toggle");
    }
  };

  const handleGenerateConfig = async (clientId) => {
    try {
      const response = await axios.get(`${API_URL}/radius/generate-config/${clientId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setGeneratedConfig(response.data);
    } catch (error) {
      toast.error("Failed to generate config");
    }
  };

  const openEditNAS = (client) => {
    setEditingNAS(client);
    setNasForm({
      name: client.name,
      ip_address: client.ip_address,
      secret: client.secret,
      nastype: client.nastype || "mikrotik",
      location: client.location || "",
      description: client.description || "",
    });
    setShowAddNAS(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="integration-settings">
      <div>
        <h1 className="text-2xl font-bold">Integration Settings</h1>
        <p className="text-neutral-400 mt-1">Configure payments, RADIUS, and notifications</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-neutral-800 pb-2">
        {[
          { id: "mpesa", label: "M-Pesa Daraja", icon: DollarSign },
          { id: "radius", label: "MikroTik / RADIUS", icon: Radio },
          { id: "sms", label: "SMS Gateway", icon: Bell },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "text-neutral-400 hover:bg-neutral-800"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* M-Pesa Tab */}
      {activeTab === "mpesa" && (
        <div className="space-y-6">
          <div className="dashboard-card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-green-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">M-Pesa Daraja API</h3>
                  <p className="text-neutral-400 text-sm">Safaricom STK Push for mobile payments</p>
                </div>
              </div>
              <span className={`px-4 py-2 rounded-lg text-sm font-medium ${
                mpesaStatus?.configured 
                  ? "bg-green-500/10 text-green-400 border border-green-500/30" 
                  : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30"
              }`}>
                {mpesaStatus?.configured ? "✓ Configured" : "⚠ Not Configured"}
              </span>
            </div>

            {mpesaStatus?.configured ? (
              <div className="bg-neutral-900 rounded-lg p-4 space-y-3">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-neutral-500 text-sm">Environment</span>
                    <p className="font-medium">{mpesaStatus.environment || "sandbox"}</p>
                  </div>
                  <div>
                    <span className="text-neutral-500 text-sm">Shortcode</span>
                    <p className="font-medium">{mpesaStatus.shortcode || "Not set"}</p>
                  </div>
                </div>
                <div className="pt-2 border-t border-neutral-800">
                  <span className="text-green-400 text-sm">✓ Ready to accept payments</span>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4">
                  <h4 className="font-medium text-blue-400 mb-2">Setup Instructions</h4>
                  <ol className="text-sm text-neutral-400 space-y-2 list-decimal list-inside">
                    <li>Go to <a href="https://developer.safaricom.co.ke" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Safaricom Daraja Portal</a></li>
                    <li>Create an app to get Consumer Key & Secret</li>
                    <li>Get Lipa Na M-Pesa credentials (Shortcode & Passkey)</li>
                    <li>Add credentials to <code className="bg-neutral-800 px-1 rounded">backend/.env</code></li>
                  </ol>
                </div>

                <div className="bg-neutral-900 rounded-lg p-4">
                  <p className="text-neutral-400 text-sm mb-2">Required environment variables:</p>
                  <pre className="text-xs text-green-400 font-mono bg-neutral-950 p-3 rounded overflow-x-auto">
{`# M-Pesa Daraja Configuration
MPESA_ENV=sandbox
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-domain.com/api/mpesa/callback`}
                  </pre>
                </div>

                <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-4">
                  <p className="text-yellow-400 text-sm">
                    <strong>Note:</strong> For testing, use ngrok to create a public HTTPS callback URL:
                    <code className="ml-2 bg-neutral-800 px-2 py-0.5 rounded">ngrok http 8001</code>
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* RADIUS / MikroTik Tab */}
      {activeTab === "radius" && (
        <div className="space-y-6">
          {/* RADIUS Status */}
          <div className="dashboard-card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-purple-500/10 rounded-xl flex items-center justify-center">
                  <Radio className="w-6 h-6 text-purple-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">FreeRADIUS Server</h3>
                  <p className="text-neutral-400 text-sm">Authentication & session management</p>
                </div>
              </div>
              <span className={`px-4 py-2 rounded-lg text-sm font-medium ${
                radiusConfig?.enabled 
                  ? "bg-green-500/10 text-green-400 border border-green-500/30" 
                  : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30"
              }`}>
                {radiusConfig?.enabled ? "✓ Enabled" : "⚠ Not Enabled"}
              </span>
            </div>

            {radiusConfig?.enabled ? (
              <div className="bg-neutral-900 rounded-lg p-4 space-y-3">
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-neutral-500 text-sm">Server Host</span>
                    <p className="font-medium">{radiusConfig.host}</p>
                  </div>
                  <div>
                    <span className="text-neutral-500 text-sm">Auth Port</span>
                    <p className="font-medium">{radiusConfig.auth_port}</p>
                  </div>
                  <div>
                    <span className="text-neutral-500 text-sm">Acct Port</span>
                    <p className="font-medium">{radiusConfig.acct_port}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-neutral-900 rounded-lg p-4">
                <p className="text-neutral-400 text-sm mb-2">Configure in <code className="bg-neutral-800 px-1 rounded">backend/.env</code>:</p>
                <pre className="text-xs text-green-400 font-mono bg-neutral-950 p-3 rounded">
{`RADIUS_ENABLED=true
RADIUS_HOST=your_freeradius_server_ip
RADIUS_SECRET=your_shared_secret
RADIUS_AUTH_PORT=1812
RADIUS_ACCT_PORT=1813`}
                </pre>
              </div>
            )}
          </div>

          {/* NAS Clients */}
          <div className="dashboard-card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg">MikroTik NAS Clients</h3>
                <p className="text-neutral-400 text-sm">Registered routers that can authenticate with RADIUS</p>
              </div>
              <Button onClick={() => { setShowAddNAS(true); setEditingNAS(null); setNasForm({ name: "", ip_address: "", secret: "", nastype: "mikrotik", location: "", description: "" }); }} data-testid="add-nas-btn">
                <Plus className="w-4 h-4 mr-2" /> Add Router
              </Button>
            </div>

            {showAddNAS && (
              <div className="bg-neutral-900 rounded-lg p-4 mb-4">
                <h4 className="font-medium mb-4">{editingNAS ? "Edit NAS Client" : "Add New MikroTik Router"}</h4>
                <form onSubmit={handleAddNAS} className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-neutral-400 mb-1">Router Name*</label>
                      <input type="text" value={nasForm.name} onChange={(e) => setNasForm({ ...nasForm, name: e.target.value })} className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2" required placeholder="Office Router" />
                    </div>
                    <div>
                      <label className="block text-sm text-neutral-400 mb-1">IP Address*</label>
                      <input type="text" value={nasForm.ip_address} onChange={(e) => setNasForm({ ...nasForm, ip_address: e.target.value })} className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2" required placeholder="192.168.88.1" />
                    </div>
                    <div>
                      <label className="block text-sm text-neutral-400 mb-1">RADIUS Secret*</label>
                      <input type="text" value={nasForm.secret} onChange={(e) => setNasForm({ ...nasForm, secret: e.target.value })} className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2" required placeholder="shared_secret" />
                    </div>
                    <div>
                      <label className="block text-sm text-neutral-400 mb-1">Location</label>
                      <input type="text" value={nasForm.location} onChange={(e) => setNasForm({ ...nasForm, location: e.target.value })} className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-2" placeholder="Nairobi CBD" />
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <Button type="submit">{editingNAS ? "Update" : "Add Router"}</Button>
                    <Button type="button" variant="outline" onClick={() => { setShowAddNAS(false); setEditingNAS(null); }}>Cancel</Button>
                  </div>
                </form>
              </div>
            )}

            {nasClients.length === 0 ? (
              <div className="text-center py-8">
                <Radio className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                <p className="text-neutral-400">No MikroTik routers registered yet.</p>
                <p className="text-neutral-500 text-sm mt-1">Add routers to enable RADIUS authentication.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {nasClients.map((client) => (
                  <div key={client.id} className="bg-neutral-900 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-3 h-3 rounded-full ${client.is_active ? "bg-green-500" : "bg-neutral-500"}`} />
                        <div>
                          <h4 className="font-medium">{client.name}</h4>
                          <p className="text-neutral-400 text-sm">{client.ip_address} • {client.location || "No location"}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handleGenerateConfig(client.id)} className="text-blue-400 border-blue-400/30">
                          Generate Config
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleToggleNAS(client.id)} className={client.is_active ? "text-yellow-400 border-yellow-400/30" : "text-green-400 border-green-400/30"}>
                          {client.is_active ? "Disable" : "Enable"}
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => openEditNAS(client)}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDeleteNAS(client.id)}>
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Generated Config Modal */}
          {generatedConfig && (
            <div className="dashboard-card border-blue-500/30">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">MikroTik Configuration for: {generatedConfig.client_name}</h3>
                <Button size="sm" variant="ghost" onClick={() => setGeneratedConfig(null)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <div className="bg-neutral-950 rounded-lg p-4">
                <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap overflow-x-auto">
                  {generatedConfig.config}
                </pre>
              </div>
              <div className="mt-4 flex gap-3">
                <Button
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(generatedConfig.config);
                    toast.success("Config copied to clipboard!");
                  }}
                >
                  Copy to Clipboard
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SMS Tab */}
      {activeTab === "sms" && (
        <div className="space-y-6">
          <div className="dashboard-card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center">
                  <Bell className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">SMS Gateway</h3>
                  <p className="text-neutral-400 text-sm">Africa&apos;s Talking or Centipid</p>
                </div>
              </div>
              <span className="px-4 py-2 rounded-lg text-sm font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/30">
                ⚠ Not Configured
              </span>
            </div>

            <div className="space-y-4">
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4">
                <h4 className="font-medium text-blue-400 mb-2">Supported Providers</h4>
                <ul className="text-sm text-neutral-400 space-y-1">
                  <li>• <strong>Africa&apos;s Talking</strong> - <a href="https://africastalking.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">africastalking.com</a></li>
                  <li>• <strong>Centipid</strong> - Alternative Kenya SMS provider</li>
                </ul>
              </div>

              <div className="bg-neutral-900 rounded-lg p-4">
                <p className="text-neutral-400 text-sm mb-2">Configure in <code className="bg-neutral-800 px-1 rounded">backend/.env</code>:</p>
                <pre className="text-xs text-green-400 font-mono bg-neutral-950 p-3 rounded">
{`# SMS Provider (africas_talking or centipid)
SMS_PROVIDER=africas_talking
AT_API_KEY=your_api_key
AT_USERNAME=your_username
AT_SENDER_ID=CAIWAVE`}
                </pre>
              </div>
            </div>
          </div>

          {/* WhatsApp */}
          <div className="dashboard-card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center">
                  <Bell className="w-6 h-6 text-green-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">WhatsApp Business (Twilio)</h3>
                  <p className="text-neutral-400 text-sm">WhatsApp notifications via Twilio</p>
                </div>
              </div>
              <span className="px-4 py-2 rounded-lg text-sm font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/30">
                ⚠ Not Configured
              </span>
            </div>

            <div className="bg-neutral-900 rounded-lg p-4">
              <p className="text-neutral-400 text-sm mb-2">Configure in <code className="bg-neutral-800 px-1 rounded">backend/.env</code>:</p>
              <pre className="text-xs text-green-400 font-mono bg-neutral-950 p-3 rounded">
{`TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886`}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// All Hotspots Component
const AllHotspotsPage = () => {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHotspots();
  }, []);

  const fetchHotspots = async () => {
    try {
      const response = await axios.get(`${API_URL}/hotspots`);
      setHotspots(response.data);
    } catch (error) {
      console.error("Failed to fetch hotspots:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (hotspotId, status) => {
    try {
      await axios.put(`${API_URL}/hotspots/${hotspotId}/status?status=${status}`);
      toast.success(`Hotspot ${status}`);
      fetchHotspots();
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  return (
    <div className="space-y-6" data-testid="all-hotspots-page">
      <div>
        <h1 className="text-2xl font-bold">All Hotspots</h1>
        <p className="text-neutral-400 mt-1">Platform-wide hotspot management</p>
      </div>

      <div className="dashboard-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : hotspots.length === 0 ? (
          <div className="p-8 text-center">
            <Radio className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No hotspots registered</h3>
            <p className="text-neutral-400 text-sm">
              Hotspots will appear here when owners register them
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>SSID</th>
                <th>Location</th>
                <th>Status</th>
                <th>Revenue</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {hotspots.map((hotspot) => (
                <tr key={hotspot.id}>
                  <td className="font-medium">{hotspot.name}</td>
                  <td className="font-mono text-sm text-neutral-400">{hotspot.ssid}</td>
                  <td>{hotspot.location_name}</td>
                  <td>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                        hotspot.status === "active" ? "badge-active" :
                        hotspot.status === "suspended" ? "bg-red-500/10 text-red-400 border border-red-500/30" :
                        "badge-pending"
                      }`}
                    >
                      {hotspot.status}
                    </span>
                  </td>
                  <td className="font-medium">
                    {formatCurrency(hotspot.total_revenue || 0)}
                  </td>
                  <td>
                    {hotspot.status === "active" ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-red-700 text-red-400"
                        onClick={() => handleStatusChange(hotspot.id, "suspended")}
                      >
                        Suspend
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-green-700 text-green-400"
                        onClick={() => handleStatusChange(hotspot.id, "active")}
                      >
                        Activate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Users Management Component
const UsersPage = () => {
  const [users] = useState([
    { id: "1", name: "CAIWAVE Admin", email: "admin@caiwave.com", role: "super_admin", is_active: true },
  ]);
  const [loading] = useState(false);

  return (
    <div className="space-y-6" data-testid="users-page">
      <div>
        <h1 className="text-2xl font-bold">User Management</h1>
        <p className="text-neutral-400 mt-1">Manage platform users and permissions</p>
      </div>

      <div className="dashboard-card overflow-hidden">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td className="font-medium">{user.name}</td>
                <td className="text-neutral-400">{user.email}</td>
                <td>
                  <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded-md text-xs">
                    {user.role.replace("_", " ")}
                  </span>
                </td>
                <td>
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${user.is_active ? "badge-active" : "badge-inactive"}`}>
                    {user.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Campaigns Management Page (ADMIN ONLY)
const CampaignsPage = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    start_date: "",
    end_date: "",
    target_regions: [],
    target_hotspot_ids: [],
    assigned_ad_ids: [],
  });
  const [availableAds, setAvailableAds] = useState([]);
  const user = getUser();

  useEffect(() => {
    fetchCampaigns();
    fetchApprovedAds();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API_URL}/campaigns/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setCampaigns(response.data);
    } catch (error) {
      toast.error("Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  const fetchApprovedAds = async () => {
    try {
      const response = await axios.get(`${API_URL}/ads/?status=approved`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setAvailableAds(response.data);
    } catch (error) {
      console.error("Failed to fetch ads");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
      };
      
      if (editingCampaign) {
        await axios.put(`${API_URL}/campaigns/${editingCampaign.id}`, payload, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("Campaign updated");
      } else {
        await axios.post(`${API_URL}/campaigns/`, payload, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("Campaign created");
      }
      
      setShowCreate(false);
      setEditingCampaign(null);
      setFormData({ name: "", description: "", start_date: "", end_date: "", target_regions: [], target_hotspot_ids: [], assigned_ad_ids: [] });
      fetchCampaigns();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save campaign");
    }
  };

  const handleStatusChange = async (campaignId, newStatus) => {
    try {
      await axios.post(`${API_URL}/campaigns/${campaignId}/status?status=${newStatus}`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success(`Campaign ${newStatus}`);
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  const handleDelete = async (campaignId) => {
    if (!window.confirm("Are you sure you want to delete this campaign?")) return;
    try {
      await axios.delete(`${API_URL}/campaigns/${campaignId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Campaign deleted");
      fetchCampaigns();
    } catch (error) {
      toast.error("Failed to delete campaign");
    }
  };

  const openEdit = (campaign) => {
    setEditingCampaign(campaign);
    setFormData({
      name: campaign.name,
      description: campaign.description || "",
      start_date: campaign.start_date?.split("T")[0] || "",
      end_date: campaign.end_date?.split("T")[0] || "",
      target_regions: campaign.target_regions || [],
      target_hotspot_ids: campaign.target_hotspot_ids || [],
      assigned_ad_ids: campaign.assigned_ad_ids || [],
    });
    setShowCreate(true);
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: "bg-gray-500/10 text-gray-400",
      scheduled: "bg-blue-500/10 text-blue-400",
      active: "bg-green-500/10 text-green-400",
      paused: "bg-yellow-500/10 text-yellow-400",
      completed: "bg-purple-500/10 text-purple-400",
    };
    return badges[status] || badges.draft;
  };

  return (
    <div className="space-y-6" data-testid="campaigns-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <p className="text-neutral-400 mt-1">Create and manage advertising campaigns (Admin Only)</p>
        </div>
        <Button onClick={() => { setShowCreate(true); setEditingCampaign(null); setFormData({ name: "", description: "", start_date: "", end_date: "", target_regions: [], target_hotspot_ids: [], assigned_ad_ids: [] }); }} data-testid="create-campaign-btn">
          <Plus className="w-4 h-4 mr-2" /> Create Campaign
        </Button>
      </div>

      {showCreate && (
        <div className="dashboard-card">
          <h2 className="text-lg font-semibold mb-4">{editingCampaign ? "Edit Campaign" : "Create New Campaign"}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Campaign Name*</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Description</label>
                <input type="text" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" />
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Start Date*</label>
                <input type="date" value={formData.start_date} onChange={(e) => setFormData({ ...formData, start_date: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">End Date*</label>
                <input type="date" value={formData.end_date} onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Target Regions (comma-separated)</label>
              <input type="text" value={formData.target_regions.join(", ")} onChange={(e) => setFormData({ ...formData, target_regions: e.target.value.split(",").map(r => r.trim()).filter(Boolean) })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" placeholder="Nairobi, Mombasa, Kisumu" />
            </div>
            <div className="flex gap-3">
              <Button type="submit">{editingCampaign ? "Update Campaign" : "Create Campaign"}</Button>
              <Button type="button" variant="outline" onClick={() => { setShowCreate(false); setEditingCampaign(null); }}>Cancel</Button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-card overflow-hidden">
        {loading ? (
          <div className="text-center py-8 text-neutral-400">Loading campaigns...</div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-8">
            <Target className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <p className="text-neutral-400">No campaigns yet. Create your first campaign.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Regions</th>
                <th>Performance</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((campaign) => (
                <tr key={campaign.id}>
                  <td>
                    <div className="font-medium">{campaign.name}</div>
                    <div className="text-neutral-500 text-xs">{campaign.description}</div>
                  </td>
                  <td>
                    <span className={`px-2 py-1 rounded-md text-xs ${getStatusBadge(campaign.status)}`}>
                      {campaign.status}
                    </span>
                  </td>
                  <td className="text-neutral-400 text-sm">
                    {new Date(campaign.start_date).toLocaleDateString()} - {new Date(campaign.end_date).toLocaleDateString()}
                  </td>
                  <td className="text-neutral-400 text-sm">
                    {campaign.target_regions?.join(", ") || "All"}
                  </td>
                  <td>
                    <div className="text-sm">
                      <span className="text-blue-400">{campaign.total_impressions || 0}</span> views
                      <span className="mx-2">·</span>
                      <span className="text-green-400">{campaign.total_clicks || 0}</span> clicks
                    </div>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      {campaign.status === "draft" && (
                        <Button size="sm" variant="outline" onClick={() => handleStatusChange(campaign.id, "active")} className="text-green-400 border-green-400/30">
                          <Play className="w-3 h-3 mr-1" /> Activate
                        </Button>
                      )}
                      {campaign.status === "active" && (
                        <Button size="sm" variant="outline" onClick={() => handleStatusChange(campaign.id, "paused")} className="text-yellow-400 border-yellow-400/30">
                          <Pause className="w-3 h-3 mr-1" /> Pause
                        </Button>
                      )}
                      {campaign.status === "paused" && (
                        <Button size="sm" variant="outline" onClick={() => handleStatusChange(campaign.id, "active")} className="text-green-400 border-green-400/30">
                          <Play className="w-3 h-3 mr-1" /> Resume
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => openEdit(campaign)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDelete(campaign.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// CAIWAVE TV Streams Page (ADMIN ONLY)
const CaiwaveTVPage = () => {
  const [streams, setStreams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingStream, setEditingStream] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    stream_url: "",
    start_time: "",
    end_time: "",
    access_type: "paid",
    price: 0,
    allowed_regions: [],
    thumbnail_url: "",
  });

  useEffect(() => {
    fetchStreams();
  }, []);

  const fetchStreams = async () => {
    try {
      const response = await axios.get(`${API_URL}/streams/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setStreams(response.data);
    } catch (error) {
      toast.error("Failed to load streams");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        price: parseFloat(formData.price) || 0,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
        allowed_hotspot_ids: [],
        pre_roll_ad_ids: [],
      };
      
      if (editingStream) {
        await axios.put(`${API_URL}/streams/${editingStream.id}`, payload, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("Stream updated");
      } else {
        await axios.post(`${API_URL}/streams/`, payload, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("Stream created");
      }
      
      setShowCreate(false);
      setEditingStream(null);
      setFormData({ name: "", description: "", stream_url: "", start_time: "", end_time: "", access_type: "paid", price: 0, allowed_regions: [], thumbnail_url: "" });
      fetchStreams();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save stream");
    }
  };

  const handleToggle = async (streamId) => {
    try {
      await axios.post(`${API_URL}/streams/${streamId}/toggle`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Stream status updated");
      fetchStreams();
    } catch (error) {
      toast.error("Failed to toggle stream");
    }
  };

  const handleDelete = async (streamId) => {
    if (!window.confirm("Are you sure you want to delete this stream?")) return;
    try {
      await axios.delete(`${API_URL}/streams/${streamId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Stream deleted");
      fetchStreams();
    } catch (error) {
      toast.error("Failed to delete stream");
    }
  };

  const openEdit = (stream) => {
    setEditingStream(stream);
    setFormData({
      name: stream.name,
      description: stream.description || "",
      stream_url: stream.stream_url,
      start_time: stream.start_time?.slice(0, 16) || "",
      end_time: stream.end_time?.slice(0, 16) || "",
      access_type: stream.access_type || "paid",
      price: stream.price || 0,
      allowed_regions: stream.allowed_regions || [],
      thumbnail_url: stream.thumbnail_url || "",
    });
    setShowCreate(true);
  };

  const getAccessBadge = (type) => {
    const badges = {
      free: "bg-green-500/10 text-green-400",
      discounted: "bg-yellow-500/10 text-yellow-400",
      sponsored: "bg-purple-500/10 text-purple-400",
      paid: "bg-blue-500/10 text-blue-400",
    };
    return badges[type] || badges.paid;
  };

  const isLive = (stream) => {
    const now = new Date();
    const start = new Date(stream.start_time);
    const end = new Date(stream.end_time);
    return stream.is_active && now >= start && now <= end;
  };

  return (
    <div className="space-y-6" data-testid="caiwave-tv-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Tv className="w-6 h-6 text-blue-400" /> CAIWAVE TV
          </h1>
          <p className="text-neutral-400 mt-1">Premium live access service powered by CAIWAVE WiFi</p>
        </div>
        <Button onClick={() => { setShowCreate(true); setEditingStream(null); setFormData({ name: "", description: "", stream_url: "", start_time: "", end_time: "", access_type: "paid", price: 0, allowed_regions: [], thumbnail_url: "" }); }} data-testid="create-stream-btn">
          <Plus className="w-4 h-4 mr-2" /> Add Stream
        </Button>
      </div>

      {showCreate && (
        <div className="dashboard-card">
          <h2 className="text-lg font-semibold mb-4">{editingStream ? "Edit Stream" : "Create New Stream"}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Event Name*</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required placeholder="Live Football Match" />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Stream URL*</label>
                <input type="url" value={formData.stream_url} onChange={(e) => setFormData({ ...formData, stream_url: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required placeholder="https://stream.caiwave.com/live/..." />
              </div>
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Description</label>
              <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" rows={2} placeholder="Brief description of the stream..." />
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Start Time*</label>
                <input type="datetime-local" value={formData.start_time} onChange={(e) => setFormData({ ...formData, start_time: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">End Time*</label>
                <input type="datetime-local" value={formData.end_time} onChange={(e) => setFormData({ ...formData, end_time: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Thumbnail URL</label>
                <input type="url" value={formData.thumbnail_url} onChange={(e) => setFormData({ ...formData, thumbnail_url: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" placeholder="https://..." />
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Access Type*</label>
                <select value={formData.access_type} onChange={(e) => setFormData({ ...formData, access_type: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2">
                  <option value="free">Free (with ads)</option>
                  <option value="discounted">Discounted</option>
                  <option value="sponsored">Sponsored</option>
                  <option value="paid">Paid</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Price (KES) {formData.access_type === "free" ? "(ignored)" : ""}</label>
                <input type="number" value={formData.price} onChange={(e) => setFormData({ ...formData, price: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" disabled={formData.access_type === "free"} />
              </div>
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Allowed Regions (comma-separated, empty = all)</label>
              <input type="text" value={formData.allowed_regions.join(", ")} onChange={(e) => setFormData({ ...formData, allowed_regions: e.target.value.split(",").map(r => r.trim()).filter(Boolean) })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" placeholder="Nairobi, Mombasa (leave empty for all)" />
            </div>
            <div className="flex gap-3">
              <Button type="submit">{editingStream ? "Update Stream" : "Create Stream"}</Button>
              <Button type="button" variant="outline" onClick={() => { setShowCreate(false); setEditingStream(null); }}>Cancel</Button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {loading ? (
          <div className="text-center py-8 text-neutral-400">Loading streams...</div>
        ) : streams.length === 0 ? (
          <div className="dashboard-card text-center py-8">
            <Tv className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <p className="text-neutral-400">No streams yet. Create your first CAIWAVE TV stream.</p>
          </div>
        ) : (
          streams.map((stream) => (
            <div key={stream.id} className="dashboard-card">
              <div className="flex items-start justify-between">
                <div className="flex gap-4">
                  <div className="w-32 h-20 bg-neutral-800 rounded-lg flex items-center justify-center overflow-hidden">
                    {stream.thumbnail_url ? (
                      <img src={stream.thumbnail_url} alt={stream.name} className="w-full h-full object-cover" />
                    ) : (
                      <Video className="w-8 h-8 text-neutral-600" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{stream.name}</h3>
                      {isLive(stream) && (
                        <span className="px-2 py-0.5 bg-red-500 text-white text-xs rounded animate-pulse">LIVE</span>
                      )}
                      <span className={`px-2 py-0.5 rounded text-xs ${getAccessBadge(stream.access_type)}`}>
                        {stream.access_type}
                      </span>
                    </div>
                    <p className="text-neutral-400 text-sm mt-1">{stream.description}</p>
                    <div className="flex gap-4 mt-2 text-sm text-neutral-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(stream.start_time).toLocaleString()} - {new Date(stream.end_time).toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        {stream.total_views || 0} views
                      </span>
                      {stream.price > 0 && (
                        <span className="text-green-400">KES {stream.price}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => handleToggle(stream.id)} className={stream.is_active ? "text-yellow-400 border-yellow-400/30" : "text-green-400 border-green-400/30"}>
                    {stream.is_active ? <><Pause className="w-3 h-3 mr-1" /> Disable</> : <><Play className="w-3 h-3 mr-1" /> Enable</>}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => openEdit(stream)}>
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDelete(stream.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Subsidized Uptime Page (ADMIN ONLY)
const SubsidizedUptimePage = () => {
  const [uptimes, setUptimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editingUptime, setEditingUptime] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    original_price: 35,
    discounted_price: 15,
    duration_hours: 25,
    start_date: "",
    end_date: "",
    daily_start_time: "",
    daily_end_time: "",
    allowed_regions: [],
    max_uses: "",
  });

  useEffect(() => {
    fetchUptimes();
  }, []);

  const fetchUptimes = async () => {
    try {
      const response = await axios.get(`${API_URL}/subsidized-uptime/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setUptimes(response.data);
    } catch (error) {
      toast.error("Failed to load subsidized uptimes");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        original_price: parseFloat(formData.original_price),
        discounted_price: parseFloat(formData.discounted_price),
        duration_hours: parseInt(formData.duration_hours),
        max_uses: formData.max_uses ? parseInt(formData.max_uses) : null,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
        allowed_hotspot_ids: [],
      };
      
      if (editingUptime) {
        await axios.put(`${API_URL}/subsidized-uptime/${editingUptime.id}`, payload, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("Subsidized uptime updated");
      } else {
        await axios.post(`${API_URL}/subsidized-uptime/`, payload, {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        });
        toast.success("Subsidized uptime created");
      }
      
      setShowCreate(false);
      setEditingUptime(null);
      setFormData({ name: "", description: "", original_price: 35, discounted_price: 15, duration_hours: 25, start_date: "", end_date: "", daily_start_time: "", daily_end_time: "", allowed_regions: [], max_uses: "" });
      fetchUptimes();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save");
    }
  };

  const handleStatusChange = async (uptimeId, newStatus) => {
    try {
      await axios.post(`${API_URL}/subsidized-uptime/${uptimeId}/status?status=${newStatus}`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success(`Status updated to ${newStatus}`);
      fetchUptimes();
    } catch (error) {
      toast.error("Failed to update status");
    }
  };

  const handleDelete = async (uptimeId) => {
    if (!window.confirm("Are you sure you want to delete this offer?")) return;
    try {
      await axios.delete(`${API_URL}/subsidized-uptime/${uptimeId}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      toast.success("Deleted successfully");
      fetchUptimes();
    } catch (error) {
      toast.error("Failed to delete");
    }
  };

  const openEdit = (uptime) => {
    setEditingUptime(uptime);
    setFormData({
      name: uptime.name,
      description: uptime.description || "",
      original_price: uptime.original_price,
      discounted_price: uptime.discounted_price,
      duration_hours: uptime.duration_hours,
      start_date: uptime.start_date?.split("T")[0] || "",
      end_date: uptime.end_date?.split("T")[0] || "",
      daily_start_time: uptime.daily_start_time || "",
      daily_end_time: uptime.daily_end_time || "",
      allowed_regions: uptime.allowed_regions || [],
      max_uses: uptime.max_uses || "",
    });
    setShowCreate(true);
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: "bg-gray-500/10 text-gray-400",
      scheduled: "bg-blue-500/10 text-blue-400",
      active: "bg-green-500/10 text-green-400",
      expired: "bg-red-500/10 text-red-400",
    };
    return badges[status] || badges.draft;
  };

  return (
    <div className="space-y-6" data-testid="subsidized-uptime-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Zap className="w-6 h-6 text-yellow-400" /> Subsidized Uptime
          </h1>
          <p className="text-neutral-400 mt-1">Create discounted/subsidized internet offers for events (Admin Only)</p>
        </div>
        <Button onClick={() => { setShowCreate(true); setEditingUptime(null); setFormData({ name: "", description: "", original_price: 35, discounted_price: 15, duration_hours: 25, start_date: "", end_date: "", daily_start_time: "", daily_end_time: "", allowed_regions: [], max_uses: "" }); }} data-testid="create-subsidy-btn">
          <Plus className="w-4 h-4 mr-2" /> Create Offer
        </Button>
      </div>

      <div className="dashboard-card bg-yellow-500/5 border-yellow-500/20">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5" />
          <div>
            <p className="font-medium text-yellow-400">Subsidized ≠ Free</p>
            <p className="text-neutral-400 text-sm mt-1">
              Subsidized uptime offers cheaper rates (e.g., KES 15 for 25 hours instead of KES 35 for 24 hours).
              Use for events, political campaigns, church services, or community broadcasts. Users still pay - just less.
            </p>
          </div>
        </div>
      </div>

      {showCreate && (
        <div className="dashboard-card">
          <h2 className="text-lg font-semibold mb-4">{editingUptime ? "Edit Offer" : "Create New Subsidized Offer"}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Offer Name*</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required placeholder="Church Service Special" />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Description</label>
                <input type="text" value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" placeholder="Special pricing for Sunday services" />
              </div>
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Original Price (KES)</label>
                <input type="number" value={formData.original_price} onChange={(e) => setFormData({ ...formData, original_price: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Discounted Price (KES)*</label>
                <input type="number" value={formData.discounted_price} onChange={(e) => setFormData({ ...formData, discounted_price: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Duration (Hours)*</label>
                <input type="number" value={formData.duration_hours} onChange={(e) => setFormData({ ...formData, duration_hours: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Start Date*</label>
                <input type="date" value={formData.start_date} onChange={(e) => setFormData({ ...formData, start_date: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">End Date*</label>
                <input type="date" value={formData.end_date} onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" required />
              </div>
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Daily Start Time (optional)</label>
                <input type="time" value={formData.daily_start_time} onChange={(e) => setFormData({ ...formData, daily_start_time: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Daily End Time (optional)</label>
                <input type="time" value={formData.daily_end_time} onChange={(e) => setFormData({ ...formData, daily_end_time: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" />
              </div>
              <div>
                <label className="block text-sm text-neutral-400 mb-1">Max Uses (optional)</label>
                <input type="number" value={formData.max_uses} onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" placeholder="Unlimited" />
              </div>
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Allowed Regions (comma-separated, empty = all)</label>
              <input type="text" value={formData.allowed_regions.join(", ")} onChange={(e) => setFormData({ ...formData, allowed_regions: e.target.value.split(",").map(r => r.trim()).filter(Boolean) })} className="w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2" placeholder="Nairobi, Mombasa" />
            </div>
            <div className="flex gap-3">
              <Button type="submit">{editingUptime ? "Update Offer" : "Create Offer"}</Button>
              <Button type="button" variant="outline" onClick={() => { setShowCreate(false); setEditingUptime(null); }}>Cancel</Button>
            </div>
          </form>
        </div>
      )}

      <div className="dashboard-card overflow-hidden">
        {loading ? (
          <div className="text-center py-8 text-neutral-400">Loading offers...</div>
        ) : uptimes.length === 0 ? (
          <div className="text-center py-8">
            <Zap className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <p className="text-neutral-400">No subsidized offers yet. Create your first offer.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Offer</th>
                <th>Pricing</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Usage</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {uptimes.map((uptime) => (
                <tr key={uptime.id}>
                  <td>
                    <div className="font-medium">{uptime.name}</div>
                    <div className="text-neutral-500 text-xs">{uptime.description}</div>
                  </td>
                  <td>
                    <div className="text-sm">
                      <span className="line-through text-neutral-500">KES {uptime.original_price}</span>
                      <span className="mx-2">→</span>
                      <span className="text-green-400 font-medium">KES {uptime.discounted_price}</span>
                    </div>
                    <div className="text-xs text-neutral-500">
                      {Math.round((1 - uptime.discounted_price / uptime.original_price) * 100)}% off
                    </div>
                  </td>
                  <td>
                    <div className="text-sm">{uptime.duration_hours} hours</div>
                    <div className="text-xs text-neutral-500">
                      {new Date(uptime.start_date).toLocaleDateString()} - {new Date(uptime.end_date).toLocaleDateString()}
                    </div>
                  </td>
                  <td>
                    <span className={`px-2 py-1 rounded-md text-xs ${getStatusBadge(uptime.status)}`}>
                      {uptime.status}
                    </span>
                  </td>
                  <td>
                    <div className="text-sm">
                      {uptime.total_uses || 0} uses
                      {uptime.max_uses && <span className="text-neutral-500"> / {uptime.max_uses}</span>}
                    </div>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      {uptime.status === "draft" && (
                        <Button size="sm" variant="outline" onClick={() => handleStatusChange(uptime.id, "active")} className="text-green-400 border-green-400/30">
                          Activate
                        </Button>
                      )}
                      {uptime.status === "active" && (
                        <Button size="sm" variant="outline" onClick={() => handleStatusChange(uptime.id, "expired")} className="text-red-400 border-red-400/30">
                          Expire
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => openEdit(uptime)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDelete(uptime.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Admin Invoice Management Page
const InvoiceManagementPage = () => {
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState("all");
  
  useEffect(() => {
    fetchInvoices();
  }, []);
  
  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API_URL}/invoices/admin/all`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      setInvoices(response.data.invoices);
      setStats(response.data.stats);
    } catch (error) {
      console.error("Failed to fetch invoices:", error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleMarkPaid = async (invoiceId) => {
    try {
      await axios.post(`${API_URL}/invoices/admin/mark-paid/${invoiceId}`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      toast.success("Invoice marked as paid");
      fetchInvoices();
    } catch (error) {
      toast.error("Failed to mark invoice as paid");
    }
  };
  
  const handleSuspendOverdue = async () => {
    try {
      const response = await axios.post(`${API_URL}/invoices/admin/suspend-overdue`, {}, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      toast.success(`Suspended ${response.data.suspended_count} hotspots`);
      fetchInvoices();
    } catch (error) {
      toast.error("Failed to suspend overdue hotspots");
    }
  };
  
  const getStatusBadge = (status) => {
    const badges = {
      draft: { bg: "bg-gray-500/10", text: "text-gray-400", label: "Draft" },
      trial: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Trial" },
      unpaid: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Unpaid" },
      paid: { bg: "bg-green-500/10", text: "text-green-400", label: "Paid" },
      overdue: { bg: "bg-red-500/10", text: "text-red-400", label: "Overdue" },
    };
    return badges[status] || { bg: "bg-gray-500/10", text: "text-gray-400", label: status };
  };
  
  const filteredInvoices = activeFilter === "all" 
    ? invoices 
    : invoices.filter(inv => inv.status === activeFilter);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6" data-testid="admin-invoice-management">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Invoice Management</h1>
          <p className="text-neutral-400 mt-1">Manage subscription invoices and payments</p>
        </div>
        <Button 
          onClick={handleSuspendOverdue}
          variant="outline" 
          className="border-red-500/50 text-red-400 hover:bg-red-500/10"
        >
          <Ban className="w-4 h-4 mr-2" />
          Suspend Overdue
        </Button>
      </div>
      
      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="dashboard-card">
            <p className="text-neutral-400 text-sm">Total Invoices</p>
            <p className="text-2xl font-bold mt-1">{stats.total}</p>
          </div>
          <div className="dashboard-card border-l-2 border-blue-500">
            <p className="text-neutral-400 text-sm">In Trial</p>
            <p className="text-2xl font-bold mt-1 text-blue-400">{stats.trial}</p>
          </div>
          <div className="dashboard-card border-l-2 border-yellow-500">
            <p className="text-neutral-400 text-sm">Unpaid</p>
            <p className="text-2xl font-bold mt-1 text-yellow-400">{stats.unpaid}</p>
          </div>
          <div className="dashboard-card border-l-2 border-red-500">
            <p className="text-neutral-400 text-sm">Overdue</p>
            <p className="text-2xl font-bold mt-1 text-red-400">{stats.overdue}</p>
          </div>
          <div className="dashboard-card border-l-2 border-green-500">
            <p className="text-neutral-400 text-sm">Revenue</p>
            <p className="text-2xl font-bold mt-1 text-green-400">KES {stats.total_revenue.toLocaleString()}</p>
          </div>
        </div>
      )}
      
      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-neutral-800 pb-4">
        {[
          { id: "all", label: "All" },
          { id: "trial", label: "Trial" },
          { id: "unpaid", label: "Unpaid" },
          { id: "overdue", label: "Overdue" },
          { id: "paid", label: "Paid" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveFilter(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm transition-colors ${
              activeFilter === tab.id
                ? "bg-blue-600/20 text-blue-400"
                : "text-neutral-400 hover:bg-neutral-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Invoice Table */}
      <div className="dashboard-card overflow-x-auto">
        {filteredInvoices.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <p className="text-neutral-500">No invoices found</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Invoice #</th>
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Owner</th>
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Hotspots</th>
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Amount</th>
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Status</th>
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Due Date</th>
                <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredInvoices.map((invoice) => {
                const badge = getStatusBadge(invoice.status);
                return (
                  <tr key={invoice.id} className="border-b border-neutral-800/50">
                    <td className="py-3 px-4 font-mono text-sm">{invoice.invoice_number}</td>
                    <td className="py-3 px-4 text-sm">{invoice.owner_id.slice(0, 8)}...</td>
                    <td className="py-3 px-4">{invoice.hotspot_count}</td>
                    <td className="py-3 px-4 font-semibold">KES {invoice.amount}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${badge.bg} ${badge.text}`}>
                        {badge.label}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-neutral-400">
                      {new Date(invoice.due_date).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      {invoice.status !== "paid" && (
                        <Button 
                          size="sm" 
                          onClick={() => handleMarkPaid(invoice.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Mark Paid
                        </Button>
                      )}
                      {invoice.status === "paid" && (
                        <span className="text-green-400 text-sm flex items-center gap-1">
                          <CheckCircle className="w-4 h-4" /> Paid
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Main Admin Dashboard Layout
const AdminDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const user = getUser();

  const navigation = [
    { name: "Overview", href: "/admin", icon: LayoutDashboard },
    { name: "Campaigns", href: "/admin/campaigns", icon: Target },
    { name: "CAIWAVE TV", href: "/admin/tv", icon: Tv },
    { name: "Subsidized Uptime", href: "/admin/subsidized", icon: Zap },
    { name: "Ad Approval", href: "/admin/ads", icon: Megaphone, badge: true },
    { name: "Invoices", href: "/admin/invoices", icon: FileText },
    { name: "Hotspots", href: "/admin/hotspots", icon: Radio },
    { name: "Packages", href: "/admin/packages", icon: Package },
    { name: "Users", href: "/admin/users", icon: Users },
    { name: "Revenue Settings", href: "/admin/revenue", icon: Sliders },
    { name: "Integrations", href: "/admin/integrations", icon: Settings },
    { name: "Marketplace", href: "/admin/marketplace", icon: ShoppingBag },
  ];

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: '#050505' }}>
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 sidebar transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ backgroundColor: '#0a0a0a', borderRight: '1px solid rgba(255,255,255,0.05)' }}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center gap-2 px-6 border-b border-neutral-800">
            <CaiwaveLogo size={32} />
            <div>
              <span className="font-semibold">CAIWAVE</span>
              <span className="ml-2 text-xs px-2 py-0.5 bg-purple-600/20 text-purple-400 rounded">
                Admin
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive =
                location.pathname === item.href ||
                (item.href !== "/admin" && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? "bg-blue-600/10 text-blue-500"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-800"
                  }`}
                >
                  <item.icon className="w-5 h-5" strokeWidth={1.5} />
                  {item.name}
                  {item.badge && item.name === "Ad Approval" && (
                    <span className="ml-auto w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User Section */}
          <div className="p-4 border-t border-neutral-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-purple-600/20 rounded-full flex items-center justify-center">
                <span className="font-medium text-purple-400">
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-xs text-neutral-400">Super Admin</p>
              </div>
            </div>
            <Button
              variant="outline"
              className="w-full border-neutral-700 text-neutral-400 hover:text-white"
              onClick={logout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 lg:pl-64">
        {/* Top Bar */}
        <header className="h-16 border-b border-neutral-800 flex items-center justify-between px-6" style={{ backgroundColor: '#050505' }}>
          <button
            className="lg:hidden p-2 -ml-2"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="flex items-center gap-4 ml-auto">
            <Link to="/owner">
              <Button variant="outline" size="sm" className="border-neutral-700">
                Owner View
              </Button>
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6 lg:p-8">
          <Routes>
            <Route index element={<AdminOverview />} />
            <Route path="campaigns" element={<CampaignsPage />} />
            <Route path="tv" element={<CaiwaveTVPage />} />
            <Route path="subsidized" element={<SubsidizedUptimePage />} />
            <Route path="ads" element={<AdApprovalPage />} />
            <Route path="invoices" element={<InvoiceManagementPage />} />
            <Route path="hotspots" element={<AllHotspotsPage />} />
            <Route path="packages" element={<PackagesPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="revenue" element={<RevenueSettingsPage />} />
            <Route path="integrations" element={<IntegrationSettingsPage />} />
            <Route
              path="marketplace"
              element={
                <div className="text-center py-12">
                  <ShoppingBag className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Equipment Marketplace</h2>
                  <p className="text-neutral-400">Manage marketplace items coming soon</p>
                </div>
              }
            />
          </Routes>
        </main>

        {/* Mandatory Footer */}
        <footer className="p-4 text-center border-t border-neutral-800">
          <p className="text-neutral-500 text-xs">
            Powered by <span className="text-blue-400 font-medium">CAIWAVE WiFi</span> © 2026. All Rights Reserved.
            <span className="mx-2">|</span>
            <a href="tel:0738570630" className="text-neutral-500 hover:text-blue-400 transition-colors">Support</a>
          </p>
        </footer>
      </div>
    </div>
  );
};

export default AdminDashboard;
