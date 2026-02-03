import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { getUser, logout } from "../../lib/auth";
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

// Ad Approval Page - CRITICAL FOR CAIWAVE ADMIN
const AdApprovalPage = () => {
  const [pendingAds, setPendingAds] = useState([]);
  const [allAds, setAllAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("pending");

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAds = async () => {
    try {
      const [pendingRes, allRes] = await Promise.all([
        axios.get(`${API_URL}/ads/pending`),
        axios.get(`${API_URL}/ads`),
      ]);
      setPendingAds(pendingRes.data);
      setAllAds(allRes.data);
    } catch (error) {
      console.error("Failed to fetch ads:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (adId) => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/approve`, { approved: true });
      toast.success("Ad approved successfully");
      fetchAds();
    } catch (error) {
      toast.error("Failed to approve ad");
    }
  };

  const handleReject = async (adId, reason = "Does not meet guidelines") => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/approve`, {
        approved: false,
        rejection_reason: reason,
      });
      toast.success("Ad rejected");
      fetchAds();
    } catch (error) {
      toast.error("Failed to reject ad");
    }
  };

  const handleSuspend = async (adId) => {
    try {
      await axios.post(`${API_URL}/ads/${adId}/suspend`);
      toast.success("Ad suspended");
      fetchAds();
    } catch (error) {
      toast.error("Failed to suspend ad");
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: "badge-pending",
      approved: "badge-active",
      rejected: "badge-inactive",
      suspended: "badge-inactive",
    };
    return badges[status] || "badge-inactive";
  };

  return (
    <div className="space-y-6" data-testid="ad-approval-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Ad Management</h1>
          <p className="text-neutral-400 mt-1">Review and approve advertiser submissions</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <AlertCircle className="w-5 h-5 text-yellow-500" />
          <span className="text-yellow-400 text-sm font-medium">
            {pendingAds.length} pending review
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-neutral-800 pb-2">
        <button
          onClick={() => setActiveTab("pending")}
          className={`px-4 py-2 rounded-lg transition-colors ${
            activeTab === "pending"
              ? "bg-yellow-500/10 text-yellow-400"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          Pending ({pendingAds.length})
        </button>
        <button
          onClick={() => setActiveTab("all")}
          className={`px-4 py-2 rounded-lg transition-colors ${
            activeTab === "all"
              ? "bg-blue-500/10 text-blue-400"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          All Ads ({allAds.length})
        </button>
      </div>

      {/* Pending Ads */}
      {activeTab === "pending" && (
        <div className="space-y-4">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : pendingAds.length === 0 ? (
            <div className="dashboard-card p-12 text-center">
              <Check className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="font-semibold mb-2">All caught up!</h3>
              <p className="text-neutral-400 text-sm">No ads pending review</p>
            </div>
          ) : (
            pendingAds.map((ad) => (
              <div key={ad.id} className="dashboard-card p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-lg">{ad.title}</h3>
                      <span className="px-2 py-1 bg-neutral-800 rounded text-xs uppercase">
                        {ad.ad_type}
                      </span>
                    </div>
                    {ad.text_content && (
                      <p className="text-neutral-400 mb-4">{ad.text_content}</p>
                    )}
                    {ad.content_url && (
                      <p className="text-neutral-500 text-sm mb-4">
                        Content URL: {ad.content_url}
                      </p>
                    )}
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div>
                        <span className="text-neutral-500">Targeting:</span>{" "}
                        {ad.targeting?.is_global ? (
                          <span className="text-blue-400">Global</span>
                        ) : (
                          <span className="text-purple-400">Local</span>
                        )}
                      </div>
                      <div>
                        <span className="text-neutral-500">Duration:</span>{" "}
                        {ad.duration_seconds}s
                      </div>
                      <div>
                        <span className="text-neutral-500">Submitted:</span>{" "}
                        {new Date(ad.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 mt-6 pt-4 border-t border-neutral-800">
                  <Button
                    onClick={() => handleApprove(ad.id)}
                    className="bg-green-600 hover:bg-green-700 flex-1"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    onClick={() => handleReject(ad.id)}
                    variant="outline"
                    className="border-red-700 text-red-400 hover:bg-red-900/20 flex-1"
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reject
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* All Ads */}
      {activeTab === "all" && (
        <div className="dashboard-card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
            </div>
          ) : allAds.length === 0 ? (
            <div className="p-8 text-center">
              <Megaphone className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
              <h3 className="font-semibold mb-2">No ads yet</h3>
              <p className="text-neutral-400 text-sm">
                Ads will appear here when advertisers create them
              </p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Impressions</th>
                  <th>Clicks</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allAds.map((ad) => (
                  <tr key={ad.id}>
                    <td className="font-medium">{ad.title}</td>
                    <td className="uppercase text-xs">{ad.ad_type}</td>
                    <td>
                      <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(ad.status)}`}>
                        {ad.status}
                      </span>
                    </td>
                    <td>{ad.impressions || 0}</td>
                    <td>{ad.clicks || 0}</td>
                    <td>
                      {ad.status === "approved" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleSuspend(ad.id)}
                          className="border-red-700 text-red-400"
                        >
                          Suspend
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
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
  const [mpesaStatus, setMpesaStatus] = useState(null);
  const [smsStatus, setSmsStatus] = useState(null);
  const [whatsappStatus, setWhatsappStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatuses();
  }, []);

  const fetchStatuses = async () => {
    try {
      const [mpesa, sms, whatsapp] = await Promise.all([
        axios.get(`${API_URL}/settings/mpesa`),
        axios.get(`${API_URL}/settings/sms`),
        axios.get(`${API_URL}/settings/whatsapp`),
      ]);
      setMpesaStatus(mpesa.data);
      setSmsStatus(sms.data);
      setWhatsappStatus(whatsapp.data);
    } catch (error) {
      console.error("Failed to fetch statuses:", error);
    } finally {
      setLoading(false);
    }
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
        <p className="text-neutral-400 mt-1">Configure payment and notification integrations</p>
      </div>

      {/* M-Pesa */}
      <div className="dashboard-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <h3 className="font-semibold">M-Pesa Daraja API</h3>
              <p className="text-neutral-400 text-sm">Safaricom mobile payments</p>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm ${mpesaStatus?.configured ? "badge-active" : "badge-pending"}`}>
            {mpesaStatus?.configured ? "Configured" : "Not Configured"}
          </span>
        </div>
        {mpesaStatus?.configured ? (
          <div className="bg-neutral-900 rounded-lg p-4 space-y-2 text-sm">
            <p><span className="text-neutral-400">Environment:</span> {mpesaStatus.environment}</p>
            <p><span className="text-neutral-400">Shortcode:</span> {mpesaStatus.shortcode_configured ? "✓ Set" : "✗ Not set"}</p>
            <p><span className="text-neutral-400">Callback URL:</span> {mpesaStatus.callback_url}</p>
          </div>
        ) : (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-yellow-400 text-sm">
              Add M-Pesa credentials to backend/.env file:
            </p>
            <pre className="mt-2 text-xs text-neutral-400 font-mono">
{`MPESA_CONSUMER_KEY=your_key
MPESA_CONSUMER_SECRET=your_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-domain/api/mpesa/callback`}
            </pre>
          </div>
        )}
      </div>

      {/* SMS */}
      <div className="dashboard-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Bell className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <h3 className="font-semibold">SMS Gateway</h3>
              <p className="text-neutral-400 text-sm">Africa's Talking / Centipid</p>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm ${smsStatus?.configured ? "badge-active" : "badge-pending"}`}>
            {smsStatus?.configured ? "Configured" : "Not Configured"}
          </span>
        </div>
        {!smsStatus?.configured && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-yellow-400 text-sm">
              Add SMS credentials to backend/.env file:
            </p>
            <pre className="mt-2 text-xs text-neutral-400 font-mono">
{`SMS_PROVIDER=africas_talking
SMS_API_KEY=your_api_key
SMS_USERNAME=your_username
SMS_SENDER_ID=CAIWAVE`}
            </pre>
          </div>
        )}
      </div>

      {/* WhatsApp */}
      <div className="dashboard-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
              <Bell className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <h3 className="font-semibold">WhatsApp (Twilio)</h3>
              <p className="text-neutral-400 text-sm">WhatsApp Business notifications</p>
            </div>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm ${whatsappStatus?.configured ? "badge-active" : "badge-pending"}`}>
            {whatsappStatus?.configured ? "Configured" : "Not Configured"}
          </span>
        </div>
        {!whatsappStatus?.configured && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <p className="text-yellow-400 text-sm">
              Add Twilio credentials to backend/.env file:
            </p>
            <pre className="mt-2 text-xs text-neutral-400 font-mono">
{`TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886`}
            </pre>
          </div>
        )}
      </div>
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
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // For now, show current admin
    setUsers([
      { id: "1", name: "CAIWAVE Admin", email: "admin@caiwave.com", role: "super_admin", is_active: true },
    ]);
    setLoading(false);
  }, []);

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

// Main Admin Dashboard Layout
const AdminDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const user = getUser();

  const navigation = [
    { name: "Overview", href: "/admin", icon: LayoutDashboard },
    { name: "Ad Approval", href: "/admin/ads", icon: Megaphone, badge: true },
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
            <Route path="ads" element={<AdApprovalPage />} />
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
