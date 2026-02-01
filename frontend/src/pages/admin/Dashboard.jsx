import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { getUser, logout } from "../../lib/auth";
import { API_URL, formatCurrency } from "../../lib/utils";
import axios from "axios";
import { toast } from "sonner";
import {
  Wifi,
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
} from "lucide-react";
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
    { name: "KES 5", value: 35, color: "#2563eb" },
    { name: "KES 10", value: 28, color: "#7c3aed" },
    { name: "KES 20", value: 22, color: "#10b981" },
    { name: "KES 50", value: 10, color: "#f59e0b" },
    { name: "KES 100", value: 5, color: "#ef4444" },
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
                {formatCurrency(stats?.total_revenue || 47900)}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-green-500" strokeWidth={1.5} />
            </div>
          </div>
          <p className="text-green-400 text-sm mt-3 flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            +18.2% this month
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
              <p className="text-neutral-400 text-sm">Registered Users</p>
              <p className="text-2xl font-bold mt-1">{stats?.total_users || 0}</p>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Users className="w-6 h-6 text-yellow-500" strokeWidth={1.5} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Active Campaigns</p>
              <p className="text-2xl font-bold mt-1">{stats?.active_campaigns || 0}</p>
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
            {packageData.map((item) => (
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

// Packages Management Component
const PackagesPage = () => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingPackage, setEditingPackage] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    price: "",
    duration_minutes: "",
    speed_mbps: "10",
    description: "",
  });

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        price: parseFloat(formData.price),
        duration_minutes: parseInt(formData.duration_minutes),
        speed_mbps: parseFloat(formData.speed_mbps),
        is_active: true,
      };

      if (editingPackage) {
        await axios.put(`${API_URL}/packages/${editingPackage.id}`, data);
        toast.success("Package updated");
      } else {
        await axios.post(`${API_URL}/packages`, data);
        toast.success("Package created");
      }

      setShowForm(false);
      setEditingPackage(null);
      setFormData({
        name: "",
        price: "",
        duration_minutes: "",
        speed_mbps: "10",
        description: "",
      });
      fetchPackages();
    } catch (error) {
      toast.error("Failed to save package");
    }
  };

  const handleEdit = (pkg) => {
    setEditingPackage(pkg);
    setFormData({
      name: pkg.name,
      price: pkg.price.toString(),
      duration_minutes: pkg.duration_minutes.toString(),
      speed_mbps: pkg.speed_mbps.toString(),
      description: pkg.description || "",
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!confirm("Are you sure you want to delete this package?")) return;
    try {
      await axios.delete(`${API_URL}/packages/${id}`);
      toast.success("Package deleted");
      fetchPackages();
    } catch (error) {
      toast.error("Failed to delete package");
    }
  };

  return (
    <div className="space-y-6" data-testid="packages-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Internet Packages</h1>
          <p className="text-neutral-400 mt-1">Manage pricing and duration options</p>
        </div>
        <Button
          onClick={() => {
            setEditingPackage(null);
            setFormData({
              name: "",
              price: "",
              duration_minutes: "",
              speed_mbps: "10",
              description: "",
            });
            setShowForm(!showForm);
          }}
          className="bg-blue-600 hover:bg-blue-700"
          data-testid="add-package-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Package
        </Button>
      </div>

      {/* Package Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="dashboard-card p-6 space-y-4"
          data-testid="package-form"
        >
          <h3 className="font-semibold">
            {editingPackage ? "Edit Package" : "New Package"}
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="text-sm text-neutral-400">Package Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="e.g., Quick Access"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Price (KES)</label>
              <input
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="5"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Duration (minutes)</label>
              <input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) =>
                  setFormData({ ...formData, duration_minutes: e.target.value })
                }
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="15"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Speed (Mbps)</label>
              <input
                type="number"
                value={formData.speed_mbps}
                onChange={(e) =>
                  setFormData({ ...formData, speed_mbps: e.target.value })
                }
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="10"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-sm text-neutral-400">Description</label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="Brief description"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              {editingPackage ? "Update Package" : "Create Package"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setShowForm(false);
                setEditingPackage(null);
              }}
              className="border-neutral-700"
            >
              Cancel
            </Button>
          </div>
        </form>
      )}

      {/* Packages Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {packages.map((pkg) => (
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
                <span className="font-bold">{formatCurrency(pkg.price)}</span>
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
            <div className="flex gap-2 mt-4 pt-4 border-t border-neutral-800">
              <Button
                variant="outline"
                size="sm"
                className="flex-1 border-neutral-700"
                onClick={() => handleEdit(pkg)}
              >
                <Edit className="w-4 h-4 mr-1" />
                Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-red-700 text-red-400 hover:bg-red-900/20"
                onClick={() => handleDelete(pkg.id)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Seed Button */}
      <div className="dashboard-card p-6">
        <h3 className="font-semibold mb-2">Initialize Default Packages</h3>
        <p className="text-neutral-400 text-sm mb-4">
          Create the standard package tiers (KES 5, 10, 20, 50, 100)
        </p>
        <Button
          onClick={async () => {
            try {
              await axios.post(`${API_URL}/seed`);
              toast.success("Default packages created");
              fetchPackages();
            } catch (error) {
              toast.error("Failed to seed data");
            }
          }}
          variant="outline"
          className="border-neutral-700"
        >
          <Package className="w-4 h-4 mr-2" />
          Seed Default Packages
        </Button>
      </div>
    </div>
  );
};

// Users Management Component
const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock users data for now
  useEffect(() => {
    setUsers([
      { id: "1", name: "Admin User", email: "admin@caitech.com", role: "super_admin", is_active: true },
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
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : (
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
                    <span className="px-2 py-1 bg-neutral-800 rounded-md text-xs">
                      {user.role.replace("_", " ")}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                        user.is_active ? "badge-active" : "badge-inactive"
                      }`}
                    >
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
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
                <th>Owner</th>
                <th>Status</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {hotspots.map((hotspot) => (
                <tr key={hotspot.id}>
                  <td className="font-medium">{hotspot.name}</td>
                  <td className="font-mono text-sm text-neutral-400">{hotspot.ssid}</td>
                  <td>{hotspot.location_name}</td>
                  <td className="text-neutral-400">{hotspot.owner_id.slice(0, 8)}...</td>
                  <td>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                        hotspot.is_active ? "badge-active" : "badge-inactive"
                      }`}
                    >
                      {hotspot.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="font-medium">
                    {formatCurrency(hotspot.total_revenue || 0)}
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

// Campaigns Management Component
const CampaignsPage = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      const response = await axios.get(`${API_URL}/campaigns`);
      setCampaigns(response.data);
    } catch (error) {
      console.error("Failed to fetch campaigns:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="campaigns-page">
      <div>
        <h1 className="text-2xl font-bold">Ad Campaigns</h1>
        <p className="text-neutral-400 mt-1">Manage advertising campaigns</p>
      </div>

      <div className="dashboard-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : campaigns.length === 0 ? (
          <div className="p-8 text-center">
            <Megaphone className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No campaigns yet</h3>
            <p className="text-neutral-400 text-sm">
              Campaigns will appear here when advertisers create them
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Budget</th>
                <th>Duration</th>
                <th>Target</th>
                <th>Status</th>
                <th>Impressions</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((campaign) => (
                <tr key={campaign.id}>
                  <td className="font-medium">{campaign.name}</td>
                  <td>{formatCurrency(campaign.budget)}</td>
                  <td className="text-sm text-neutral-400">
                    {new Date(campaign.start_date).toLocaleDateString()} -{" "}
                    {new Date(campaign.end_date).toLocaleDateString()}
                  </td>
                  <td>
                    {campaign.target_global ? (
                      <span className="flex items-center gap-1">
                        <Globe className="w-4 h-4 text-blue-400" />
                        Global
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Target className="w-4 h-4 text-purple-400" />
                        Local
                      </span>
                    )}
                  </td>
                  <td>
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
                  </td>
                  <td>{campaign.total_impressions || 0}</td>
                </tr>
              ))}
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
    { name: "Hotspots", href: "/admin/hotspots", icon: Radio },
    { name: "Packages", href: "/admin/packages", icon: Package },
    { name: "Campaigns", href: "/admin/campaigns", icon: Megaphone },
    { name: "Users", href: "/admin/users", icon: Users },
    { name: "Analytics", href: "/admin/analytics", icon: BarChart3 },
    { name: "Settings", href: "/admin/settings", icon: Settings },
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
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Wifi className="w-5 h-5 text-white" strokeWidth={1.5} />
            </div>
            <div>
              <span className="font-semibold">CAITECH</span>
              <span className="ml-2 text-xs px-2 py-0.5 bg-purple-600/20 text-purple-400 rounded">
                Admin
              </span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
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
        <header className="h-16 border-b border-neutral-800 flex items-center justify-between px-6">
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
            <Route path="hotspots" element={<AllHotspotsPage />} />
            <Route path="packages" element={<PackagesPage />} />
            <Route path="campaigns" element={<CampaignsPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route
              path="analytics"
              element={
                <div className="text-center py-12">
                  <BarChart3 className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Platform Analytics</h2>
                  <p className="text-neutral-400">Advanced analytics coming soon</p>
                </div>
              }
            />
            <Route
              path="settings"
              element={
                <div className="text-center py-12">
                  <Settings className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Platform Settings</h2>
                  <p className="text-neutral-400">Settings coming soon</p>
                </div>
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
