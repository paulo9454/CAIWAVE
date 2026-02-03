import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { getUser, logout } from "../../lib/auth";
import { API_URL, formatCurrency } from "../../lib/utils";
import axios from "axios";
import { toast } from "sonner";
import {
  LayoutDashboard,
  Image,
  Video,
  Type,
  Target,
  Settings,
  LogOut,
  Menu,
  TrendingUp,
  Eye,
  MousePointer,
  Plus,
  Upload,
  Calendar,
  Globe,
  MapPin,
  BarChart3,
} from "lucide-react";
import { CaiwaveLogo } from "../../components/CaiwaveLogo";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Advertiser Overview Component
const AdvertiserOverview = () => {
  const [ads, setAds] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = getUser();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [adsRes, campaignsRes] = await Promise.all([
        axios.get(`${API_URL}/ads`),
        axios.get(`${API_URL}/campaigns`),
      ]);
      setAds(adsRes.data);
      setCampaigns(campaignsRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const totalImpressions = ads.reduce((sum, ad) => sum + (ad.impressions || 0), 0);
  const totalClicks = ads.reduce((sum, ad) => sum + (ad.clicks || 0), 0);
  const activeCampaigns = campaigns.filter((c) => c.status === "active").length;

  const chartData = [
    { name: "Mon", impressions: 1200, clicks: 45 },
    { name: "Tue", impressions: 1800, clicks: 62 },
    { name: "Wed", impressions: 2200, clicks: 78 },
    { name: "Thu", impressions: 1950, clicks: 71 },
    { name: "Fri", impressions: 2800, clicks: 95 },
    { name: "Sat", impressions: 3200, clicks: 112 },
    { name: "Sun", impressions: 2600, clicks: 88 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="advertiser-dashboard">
      <div>
        <h1 className="text-2xl font-bold">Welcome, {user?.name}</h1>
        <p className="text-neutral-400 mt-1">Track your advertising performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card stat-card-primary">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Total Impressions</p>
              <p className="text-2xl font-bold mt-1">{totalImpressions.toLocaleString()}</p>
            </div>
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Eye className="w-6 h-6 text-blue-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-blue-400 text-sm mt-3 flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            +24.5% this week
          </p>
        </div>

        <div className="stat-card stat-card-success">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Total Clicks</p>
              <p className="text-2xl font-bold mt-1">{totalClicks.toLocaleString()}</p>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <MousePointer className="w-6 h-6 text-green-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-neutral-400 text-sm mt-3">
            CTR: {totalImpressions > 0 ? ((totalClicks / totalImpressions) * 100).toFixed(2) : 0}%
          </p>
        </div>

        <div className="stat-card stat-card-warning">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Active Campaigns</p>
              <p className="text-2xl font-bold mt-1">{activeCampaigns}</p>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Target className="w-6 h-6 text-yellow-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-neutral-400 text-sm mt-3">
            {campaigns.length} total campaigns
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Total Ads</p>
              <p className="text-2xl font-bold mt-1">{ads.length}</p>
            </div>
            <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
              <Image className="w-6 h-6 text-purple-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-neutral-400 text-sm mt-3">
            {ads.filter((a) => a.is_active).length} active
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="dashboard-card p-6">
        <h2 className="font-semibold mb-6">Performance Overview</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorImpressions" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
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
                dataKey="impressions"
                stroke="#7c3aed"
                fillOpacity={1}
                fill="url(#colorImpressions)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Ads */}
      <div className="dashboard-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Your Ads</h2>
          <Link to="/advertiser/ads">
            <Button variant="outline" size="sm" className="border-neutral-700">
              View All
            </Button>
          </Link>
        </div>
        {ads.length === 0 ? (
          <div className="text-center py-8">
            <Image className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No ads yet</h3>
            <p className="text-neutral-400 text-sm mb-4">Create your first ad to get started</p>
            <Link to="/advertiser/ads">
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Create Ad
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ads.slice(0, 3).map((ad) => (
              <div key={ad.id} className="bg-neutral-900/50 border border-neutral-800 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-3">
                  {ad.ad_type === "image" && <Image className="w-5 h-5 text-blue-400" />}
                  {ad.ad_type === "video" && <Video className="w-5 h-5 text-red-400" />}
                  {ad.ad_type === "text" && <Type className="w-5 h-5 text-green-400" />}
                  <span className="font-medium">{ad.title}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-400">Impressions</span>
                  <span>{ad.impressions || 0}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-neutral-400">Clicks</span>
                  <span>{ad.clicks || 0}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Ads Management Component
const AdsPage = () => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    ad_type: "image",
    content_url: "",
    text_content: "",
    link_url: "",
    duration_seconds: "10",
  });

  useEffect(() => {
    fetchAds();
  }, []);

  const fetchAds = async () => {
    try {
      const response = await axios.get(`${API_URL}/ads?active_only=false`);
      setAds(response.data);
    } catch (error) {
      console.error("Failed to fetch ads:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/ads`, {
        ...formData,
        duration_seconds: parseInt(formData.duration_seconds),
      });
      toast.success("Ad created successfully");
      setShowForm(false);
      setFormData({
        title: "",
        ad_type: "image",
        content_url: "",
        text_content: "",
        link_url: "",
        duration_seconds: "10",
      });
      fetchAds();
    } catch (error) {
      toast.error("Failed to create ad");
    }
  };

  return (
    <div className="space-y-6" data-testid="ads-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Ads</h1>
          <p className="text-neutral-400 mt-1">Create and manage your advertisements</p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-purple-600 hover:bg-purple-700"
          data-testid="create-ad-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Ad
        </Button>
      </div>

      {/* Ad Creation Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="dashboard-card p-6 space-y-4">
          <h3 className="font-semibold">New Advertisement</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-neutral-400">Ad Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="e.g., Summer Sale"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Ad Type</label>
              <select
                value={formData.ad_type}
                onChange={(e) => setFormData({ ...formData, ad_type: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
              >
                <option value="image">Image Banner</option>
                <option value="video">Video Ad</option>
                <option value="text">Text Announcement</option>
                <option value="link">Sponsored Link</option>
              </select>
            </div>
            {(formData.ad_type === "image" || formData.ad_type === "video") && (
              <div className="md:col-span-2">
                <label className="text-sm text-neutral-400">Content URL</label>
                <input
                  type="url"
                  value={formData.content_url}
                  onChange={(e) => setFormData({ ...formData, content_url: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                  placeholder="https://example.com/image.jpg"
                />
              </div>
            )}
            {formData.ad_type === "text" && (
              <div className="md:col-span-2">
                <label className="text-sm text-neutral-400">Text Content</label>
                <textarea
                  value={formData.text_content}
                  onChange={(e) => setFormData({ ...formData, text_content: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                  placeholder="Your ad message..."
                  rows={3}
                />
              </div>
            )}
            <div>
              <label className="text-sm text-neutral-400">Click-through URL</label>
              <input
                type="url"
                value={formData.link_url}
                onChange={(e) => setFormData({ ...formData, link_url: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="https://yourwebsite.com"
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Duration (seconds)</label>
              <input
                type="number"
                value={formData.duration_seconds}
                onChange={(e) => setFormData({ ...formData, duration_seconds: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="10"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
              Create Ad
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowForm(false)}
              className="border-neutral-700"
            >
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Ads Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : ads.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <Image className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No ads yet</h3>
            <p className="text-neutral-400 text-sm">Create your first ad to start advertising</p>
          </div>
        ) : (
          ads.map((ad) => (
            <div key={ad.id} className="dashboard-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  {ad.ad_type === "image" && (
                    <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
                      <Image className="w-4 h-4 text-blue-400" />
                    </div>
                  )}
                  {ad.ad_type === "video" && (
                    <div className="w-8 h-8 bg-red-500/10 rounded-lg flex items-center justify-center">
                      <Video className="w-4 h-4 text-red-400" />
                    </div>
                  )}
                  {ad.ad_type === "text" && (
                    <div className="w-8 h-8 bg-green-500/10 rounded-lg flex items-center justify-center">
                      <Type className="w-4 h-4 text-green-400" />
                    </div>
                  )}
                  <span className="text-xs text-neutral-400 uppercase">{ad.ad_type}</span>
                </div>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    ad.is_active ? "badge-active" : "badge-inactive"
                  }`}
                >
                  {ad.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <h3 className="font-semibold mb-2">{ad.title}</h3>
              {ad.text_content && (
                <p className="text-sm text-neutral-400 mb-4 line-clamp-2">{ad.text_content}</p>
              )}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-neutral-800">
                <div>
                  <p className="text-neutral-400 text-xs">Impressions</p>
                  <p className="font-bold">{(ad.impressions || 0).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-xs">Clicks</p>
                  <p className="font-bold">{(ad.clicks || 0).toLocaleString()}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Campaigns Page Component
const CampaignsPage = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    budget: "",
    start_date: "",
    end_date: "",
    target_global: true,
    ad_ids: [],
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [campaignsRes, adsRes] = await Promise.all([
        axios.get(`${API_URL}/campaigns`),
        axios.get(`${API_URL}/ads`),
      ]);
      setCampaigns(campaignsRes.data);
      setAds(adsRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/campaigns`, {
        ...formData,
        budget: parseFloat(formData.budget),
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString(),
      });
      toast.success("Campaign created successfully");
      setShowForm(false);
      fetchData();
    } catch (error) {
      toast.error("Failed to create campaign");
    }
  };

  return (
    <div className="space-y-6" data-testid="campaigns-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <p className="text-neutral-400 mt-1">Schedule and target your ads</p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-purple-600 hover:bg-purple-700"
          data-testid="create-campaign-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Campaign
        </Button>
      </div>

      {/* Campaign Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="dashboard-card p-6 space-y-4">
          <h3 className="font-semibold">New Campaign</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-neutral-400">Campaign Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="e.g., Holiday Promo"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Budget (KES)</label>
              <input
                type="number"
                value={formData.budget}
                onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="10000"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Start Date</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">End Date</label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm text-neutral-400 mb-2 block">Target Audience</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={formData.target_global}
                    onChange={() => setFormData({ ...formData, target_global: true })}
                    className="w-4 h-4"
                  />
                  <Globe className="w-4 h-4 text-blue-400" />
                  <span>All Hotspots (Global)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={!formData.target_global}
                    onChange={() => setFormData({ ...formData, target_global: false })}
                    className="w-4 h-4"
                  />
                  <MapPin className="w-4 h-4 text-purple-400" />
                  <span>Specific Locations</span>
                </label>
              </div>
            </div>
            {ads.length > 0 && (
              <div className="md:col-span-2">
                <label className="text-sm text-neutral-400 mb-2 block">Select Ads</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {ads.map((ad) => (
                    <label
                      key={ad.id}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors ${
                        formData.ad_ids.includes(ad.id)
                          ? "border-purple-500 bg-purple-500/10"
                          : "border-neutral-700 hover:border-neutral-600"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={formData.ad_ids.includes(ad.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({
                              ...formData,
                              ad_ids: [...formData.ad_ids, ad.id],
                            });
                          } else {
                            setFormData({
                              ...formData,
                              ad_ids: formData.ad_ids.filter((id) => id !== ad.id),
                            });
                          }
                        }}
                        className="sr-only"
                      />
                      <span className="text-sm">{ad.title}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-3">
            <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
              Create Campaign
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowForm(false)}
              className="border-neutral-700"
            >
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Campaigns List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : campaigns.length === 0 ? (
          <div className="dashboard-card p-12 text-center">
            <Target className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No campaigns yet</h3>
            <p className="text-neutral-400 text-sm">Create a campaign to start showing your ads</p>
          </div>
        ) : (
          campaigns.map((campaign) => (
            <div key={campaign.id} className="dashboard-card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="font-semibold">{campaign.name}</h3>
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        campaign.status === "active"
                          ? "badge-active"
                          : campaign.status === "pending"
                          ? "badge-pending"
                          : "badge-inactive"
                      }`}
                    >
                      {campaign.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-sm text-neutral-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(campaign.start_date).toLocaleDateString()} -{" "}
                      {new Date(campaign.end_date).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1">
                      {campaign.target_global ? (
                        <>
                          <Globe className="w-4 h-4" />
                          Global
                        </>
                      ) : (
                        <>
                          <MapPin className="w-4 h-4" />
                          Local
                        </>
                      )}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-neutral-400">Budget</p>
                  <p className="font-bold">{formatCurrency(campaign.budget)}</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-neutral-800">
                <div>
                  <p className="text-neutral-400 text-xs">Impressions</p>
                  <p className="font-bold">{(campaign.total_impressions || 0).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-xs">Spent</p>
                  <p className="font-bold">{formatCurrency(campaign.total_spent || 0)}</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-xs">Ads</p>
                  <p className="font-bold">{campaign.ad_ids?.length || 0}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Main Advertiser Dashboard Layout
const AdvertiserDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const user = getUser();

  const navigation = [
    { name: "Overview", href: "/advertiser", icon: LayoutDashboard },
    { name: "My Ads", href: "/advertiser/ads", icon: Image },
    { name: "Campaigns", href: "/advertiser/campaigns", icon: Target },
    { name: "Analytics", href: "/advertiser/analytics", icon: BarChart3 },
    { name: "Settings", href: "/advertiser/settings", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-[#050505] flex">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 sidebar transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center gap-2 px-6 border-b border-neutral-800">
            <CaiwaveLogo size={32} />
            <div>
              <span className="font-semibold">CAIWAVE</span>
              <span className="ml-2 text-xs px-2 py-0.5 bg-purple-600/20 text-purple-400 rounded">
                Ads
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive =
                location.pathname === item.href ||
                (item.href !== "/advertiser" && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? "bg-purple-600/10 text-purple-500"
                      : "text-neutral-400 hover:text-white hover:bg-neutral-800"
                  }`}
                >
                  <item.icon className="w-5 h-5" strokeWidth={1.5} />
                  {item.name}
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
                <p className="text-xs text-neutral-400">Advertiser</p>
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
        <header className="h-16 border-b border-neutral-800 flex items-center justify-between px-6">
          <button
            className="lg:hidden p-2 -ml-2"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>

          <div className="ml-auto">
            <Link to="/">
              <Button variant="outline" size="sm" className="border-neutral-700">
                Back to Site
              </Button>
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6 lg:p-8">
          <Routes>
            <Route index element={<AdvertiserOverview />} />
            <Route path="ads" element={<AdsPage />} />
            <Route path="campaigns" element={<CampaignsPage />} />
            <Route
              path="analytics"
              element={
                <div className="text-center py-12">
                  <BarChart3 className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Ad Analytics</h2>
                  <p className="text-neutral-400">Detailed analytics coming soon</p>
                </div>
              }
            />
            <Route
              path="settings"
              element={
                <div className="text-center py-12">
                  <Settings className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Account Settings</h2>
                  <p className="text-neutral-400">Settings coming soon</p>
                </div>
              }
            />
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
    </div>
  );
};

export default AdvertiserDashboard;
