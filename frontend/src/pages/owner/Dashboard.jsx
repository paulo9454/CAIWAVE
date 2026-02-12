import { useState, useEffect } from "react";
import { Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/button";
import { getUser, logout, getAuthToken, ROLES } from "../../lib/auth";
import { API_URL, formatCurrency } from "../../lib/utils";
import axios from "axios";
import { toast } from "sonner";
import {
  LayoutDashboard,
  Radio,
  CreditCard,
  Settings,
  LogOut,
  Menu,
  X,
  TrendingUp,
  Users,
  Clock,
  DollarSign,
  ChevronRight,
  Plus,
  BarChart3,
  FileText,
  AlertTriangle,
  CheckCircle,
  Phone,
  Calendar,
  Zap,
  MapPin,
  Trophy,
  Activity,
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

// Subscription Status Banner Component
const SubscriptionBanner = ({ subscription, onPayNow }) => {
  if (!subscription) return null;
  
  const { subscription_status, trial_days_remaining, current_invoice, monthly_fee } = subscription;
  
  const getStatusConfig = () => {
    switch (subscription_status) {
      case "trial":
        return {
          bg: "bg-blue-500/10 border-blue-500/30",
          icon: <Clock className="w-5 h-5 text-blue-400" />,
          title: `Free Trial - ${trial_days_remaining} days remaining`,
          description: `Your trial ends in ${trial_days_remaining} days. Pay KES ${monthly_fee} to continue after trial.`,
          showPayButton: trial_days_remaining <= 3,
          urgent: false
        };
      case "active":
        return {
          bg: "bg-green-500/10 border-green-500/30",
          icon: <CheckCircle className="w-5 h-5 text-green-400" />,
          title: "Subscription Active",
          description: "Your subscription is active. Enjoy all features!",
          showPayButton: false,
          urgent: false
        };
      case "grace_period":
        return {
          bg: "bg-yellow-500/10 border-yellow-500/30",
          icon: <AlertTriangle className="w-5 h-5 text-yellow-400" />,
          title: "Payment Overdue",
          description: `Your trial has ended. Pay KES ${monthly_fee} now to avoid suspension.`,
          showPayButton: true,
          urgent: true
        };
      case "suspended":
        return {
          bg: "bg-red-500/10 border-red-500/30",
          icon: <AlertTriangle className="w-5 h-5 text-red-400" />,
          title: "Account Suspended",
          description: `Your hotspot is suspended due to non-payment. Pay KES ${monthly_fee} to reactivate.`,
          showPayButton: true,
          urgent: true
        };
      default:
        return null;
    }
  };
  
  const config = getStatusConfig();
  if (!config) return null;
  
  return (
    <div className={`p-4 rounded-xl border ${config.bg} mb-6`} data-testid="subscription-banner">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          {config.icon}
          <div>
            <h3 className="font-semibold">{config.title}</h3>
            <p className="text-sm text-neutral-400">{config.description}</p>
          </div>
        </div>
        {config.showPayButton && current_invoice && (
          <Button
            onClick={() => onPayNow(current_invoice)}
            className={config.urgent ? "bg-red-600 hover:bg-red-700" : "bg-blue-600 hover:bg-blue-700"}
            data-testid="pay-now-btn"
          >
            <CreditCard className="w-4 h-4 mr-2" />
            Pay KES {monthly_fee} Now
          </Button>
        )}
      </div>
    </div>
  );
};

// Payment Modal Component (Paystack)
const PaymentModal = ({ invoice, onClose, onSuccess }) => {
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
        `${API_URL}/invoices/pay/${invoice.id}`,
        { phone_number: `254${phone}` },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } }
      );
      
      if (response.data.success) {
        if (response.data.authorization_url) {
          // Redirect to Paystack payment page
          toast.success("Redirecting to payment page...");
          window.open(response.data.authorization_url, "_blank");
          onClose();
          // Show instructions
          toast.info("Complete payment in the new tab, then refresh this page");
        } else {
          toast.success(response.data.message);
          onSuccess();
          onClose();
        }
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
          <h2 className="text-xl font-semibold">Pay Subscription</h2>
          <button onClick={onClose} className="p-2 hover:bg-neutral-800 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 bg-neutral-800 rounded-lg mb-6">
          <div className="flex justify-between items-center">
            <span className="text-neutral-400">Invoice:</span>
            <span className="font-mono text-sm">{invoice.invoice_number}</span>
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-neutral-400">Hotspots:</span>
            <span>{invoice.hotspot_count}</span>
          </div>
          <div className="flex justify-between items-center mt-2">
            <span className="text-neutral-400">Amount:</span>
            <span className="font-bold text-2xl text-green-400">KES {invoice.amount}</span>
          </div>
        </div>
        
        <div className="mb-6">
          <label className="block text-sm text-neutral-400 mb-2">Phone Number (for payment confirmation)</label>
          <div className="flex items-center bg-neutral-800 border border-neutral-700 rounded-lg">
            <span className="px-4 text-neutral-500">+254</span>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 9))}
              className="flex-1 bg-transparent px-2 py-3 focus:outline-none"
              placeholder="724825975"
              data-testid="subscription-phone-input"
            />
          </div>
          <p className="text-xs text-neutral-500 mt-2">
            You'll be redirected to Paystack to complete payment via M-Pesa or Card
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
            data-testid="confirm-subscription-payment"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <CreditCard className="w-4 h-4 mr-2" />
                Pay with Paystack
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

// Dashboard Overview Component
const DashboardOverview = () => {
  const [stats, setStats] = useState(null);
  const [hotspots, setHotspots] = useState([]);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [payingInvoice, setPayingInvoice] = useState(null);
  const user = getUser();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, hotspotsRes, subscriptionRes] = await Promise.all([
        axios.get(`${API_URL}/analytics/dashboard`, { headers }),
        axios.get(`${API_URL}/hotspots`, { headers }),
        axios.get(`${API_URL}/subscriptions/status`, { headers }),
      ]);
      setStats(statsRes.data);
      setHotspots(hotspotsRes.data);
      setSubscription(subscriptionRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Mock chart data
  const chartData = [
    { name: "Mon", revenue: 1200, sessions: 45 },
    { name: "Tue", revenue: 1800, sessions: 62 },
    { name: "Wed", revenue: 2200, sessions: 78 },
    { name: "Thu", revenue: 1950, sessions: 71 },
    { name: "Fri", revenue: 2800, sessions: 95 },
    { name: "Sat", revenue: 3200, sessions: 112 },
    { name: "Sun", revenue: 2600, sessions: 88 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="owner-dashboard">
      {/* Subscription Status Banner */}
      <SubscriptionBanner 
        subscription={subscription} 
        onPayNow={(invoice) => setPayingInvoice(invoice)} 
      />
      
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold">Welcome back, {user?.name}</h1>
        <p className="text-neutral-400 mt-1">Here&apos;s your hotspot performance overview</p>
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
            +12.5% from last week
          </p>
        </div>

        <div className="stat-card stat-card-primary">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Active Hotspots</p>
              <p className="text-2xl font-bold mt-1">
                {stats?.active_hotspots || 0} / {stats?.total_hotspots || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Radio className="w-6 h-6 text-blue-500" strokeWidth={1.5} />
            </div>
          </div>
        </div>

        <div className="stat-card stat-card-warning">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Total Sessions</p>
              <p className="text-2xl font-bold mt-1">{stats?.total_sessions || 0}</p>
            </div>
            <div className="w-12 h-12 bg-yellow-500/10 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-yellow-500" strokeWidth={1.5} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-neutral-400 text-sm">Your Share (70%)</p>
              <p className="text-2xl font-bold mt-1">
                {formatCurrency((stats?.total_revenue || 0) * 0.7)}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center">
              <CreditCard className="w-6 h-6 text-purple-500" strokeWidth={1.5} />
            </div>
          </div>
        </div>
      </div>

      {/* Chart & Recent Activity */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <div className="lg:col-span-2 dashboard-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-semibold">Revenue Overview</h2>
            <select className="bg-neutral-800 border border-neutral-700 rounded-md px-3 py-1 text-sm">
              <option>Last 7 days</option>
              <option>Last 30 days</option>
            </select>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
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
                  fill="url(#colorRevenue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card p-6">
          <h2 className="font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link to="/owner/hotspots">
              <Button
                variant="outline"
                className="w-full justify-between border-neutral-700 hover:bg-neutral-800"
              >
                <span className="flex items-center gap-2">
                  <Plus className="w-4 h-4" />
                  Add Hotspot
                </span>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link to="/owner/payments">
              <Button
                variant="outline"
                className="w-full justify-between border-neutral-700 hover:bg-neutral-800"
              >
                <span className="flex items-center gap-2">
                  <CreditCard className="w-4 h-4" />
                  View Payments
                </span>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
            <Button
              variant="outline"
              className="w-full justify-between border-green-700 text-green-400 hover:bg-green-900/20"
            >
              <span className="flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Withdraw Earnings
              </span>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          {/* Recent Hotspots */}
          <div className="mt-6 pt-6 border-t border-neutral-800">
            <h3 className="text-sm font-medium text-neutral-400 mb-3">Your Hotspots</h3>
            {hotspots.length === 0 ? (
              <p className="text-neutral-500 text-sm">No hotspots yet</p>
            ) : (
              <div className="space-y-2">
                {hotspots.slice(0, 3).map((hotspot) => (
                  <div
                    key={hotspot.id}
                    className="flex items-center justify-between p-2 rounded-md bg-neutral-800/50"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          hotspot.is_active ? "bg-green-500" : "bg-neutral-500"
                        }`}
                      />
                      <span className="text-sm">{hotspot.name}</span>
                    </div>
                    <span className="text-xs text-neutral-400">
                      {formatCurrency(hotspot.total_revenue || 0)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Payment Modal */}
      {payingInvoice && (
        <PaymentModal
          invoice={payingInvoice}
          onClose={() => setPayingInvoice(null)}
          onSuccess={fetchData}
        />
      )}
    </div>
  );
};

// Hotspots Management Component
const HotspotsPage = () => {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    ssid: "",
    location_name: "",
    ward: "",
    constituency: "",
  });

  useEffect(() => {
    fetchHotspots();
  }, []);

  const fetchHotspots = async () => {
    try {
      const response = await axios.get(`${API_URL}/hotspots/`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setHotspots(response.data);
    } catch (error) {
      console.error("Failed to fetch hotspots:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const user = getUser();
      await axios.post(
        `${API_URL}/hotspots/`,
        {
          ...formData,
          owner_id: user.id,
        },
        {
          headers: { Authorization: `Bearer ${getAuthToken()}` },
        }
      );
      toast.success("Hotspot created successfully");
      setShowForm(false);
      setFormData({
        name: "",
        ssid: "",
        location_name: "",
        ward: "",
        constituency: "",
      });
      fetchHotspots();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create hotspot");
    }
  };

  return (
    <div className="space-y-6" data-testid="hotspots-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Hotspots</h1>
          <p className="text-neutral-400 mt-1">Manage your WiFi hotspot locations</p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700"
          data-testid="add-hotspot-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Hotspot
        </Button>
      </div>

      {/* Add Hotspot Form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="dashboard-card p-6 space-y-4"
          data-testid="hotspot-form"
        >
          <h3 className="font-semibold">New Hotspot</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-neutral-400">Hotspot Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="e.g., Shop WiFi"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">SSID</label>
              <input
                type="text"
                value={formData.ssid}
                onChange={(e) => setFormData({ ...formData, ssid: e.target.value })}
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="e.g., CAIWAVE_Shop"
                required
              />
            </div>
            <div>
              <label className="text-sm text-neutral-400">Location</label>
              <input
                type="text"
                value={formData.location_name}
                onChange={(e) =>
                  setFormData({ ...formData, location_name: e.target.value })
                }
                className="w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md"
                placeholder="e.g., Nairobi CBD"
                required
              />
            </div>
          </div>
          <p className="text-sm text-neutral-500 mt-2">
            After creating your hotspot, go to "MikroTik Setup" to configure your router.
          </p>
          <div className="flex gap-3 mt-4">
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              Create Hotspot
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

      {/* Hotspots Table */}
      <div className="dashboard-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : hotspots.length === 0 ? (
          <div className="p-8 text-center">
            <Radio className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No hotspots yet</h3>
            <p className="text-neutral-400 text-sm">
              Add your first hotspot to start earning
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
                <th>Sessions</th>
                <th>Revenue</th>
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
                        hotspot.is_active ? "badge-active" : "badge-inactive"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          hotspot.is_active ? "bg-green-500" : "bg-neutral-500"
                        }`}
                      />
                      {hotspot.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>{hotspot.total_sessions || 0}</td>
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

// MikroTik Setup Component
const MikroTikSetupPage = () => {
  const [hotspots, setHotspots] = useState([]);
  const [routers, setRouters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddRouter, setShowAddRouter] = useState(false);
  const [selectedHotspot, setSelectedHotspot] = useState("");
  const [routerName, setRouterName] = useState("");
  const [generatedScript, setGeneratedScript] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };
      
      const [hotspotsRes, routersRes] = await Promise.all([
        axios.get(`${API_URL}/hotspots`, { headers }),
        axios.get(`${API_URL}/mikrotik-onboard/routers`, { headers }),
      ]);
      
      setHotspots(hotspotsRes.data);
      setRouters(routersRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterRouter = async () => {
    if (!selectedHotspot || !routerName.trim()) {
      toast.error("Please select a hotspot and enter router name");
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.post(
        `${API_URL}/mikrotik-onboard/register`,
        {
          name: routerName.trim(),
          hotspot_id: selectedHotspot,
        },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } }
      );
      
      setGeneratedScript(response.data);
      toast.success("Configuration script generated!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to generate script");
    } finally {
      setGenerating(false);
    }
  };

  const handleConfirmConnection = async (router) => {
    setConfirming(true);
    try {
      await axios.post(
        `${API_URL}/mikrotik-onboard/confirm`,
        {
          router_id: router.id,
          nas_identifier: router.nas_identifier,
        },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } }
      );
      
      toast.success("Router connection confirmed!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to confirm connection");
    } finally {
      setConfirming(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending_configuration: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Pending Setup" },
      configured: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Configured" },
      connected: { bg: "bg-green-500/10", text: "text-green-400", label: "Connected" },
      offline: { bg: "bg-red-500/10", text: "text-red-400", label: "Offline" },
      error: { bg: "bg-red-500/10", text: "text-red-400", label: "Error" },
    };
    return badges[status] || { bg: "bg-gray-500/10", text: "text-gray-400", label: status };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="mikrotik-setup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">MikroTik Setup</h1>
          <p className="text-neutral-400 mt-1">Configure your MikroTik routers for CAIWAVE integration</p>
        </div>
        <Button
          onClick={() => setShowAddRouter(true)}
          className="bg-blue-600 hover:bg-blue-700"
          data-testid="add-mikrotik-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add MikroTik
        </Button>
      </div>

      {/* Setup Instructions */}
      <div className="dashboard-card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" />
          Quick Setup Guide
        </h2>
        <div className="grid md:grid-cols-4 gap-4">
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">1</span>
            </div>
            <h4 className="font-medium text-sm">Reset Router</h4>
            <p className="text-xs text-neutral-500 mt-1">System reset for fresh install</p>
          </div>
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">2</span>
            </div>
            <h4 className="font-medium text-sm">Configure Internet</h4>
            <p className="text-xs text-neutral-500 mt-1">DHCP Client on ether1</p>
          </div>
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">3</span>
            </div>
            <h4 className="font-medium text-sm">Run Script</h4>
            <p className="text-xs text-neutral-500 mt-1">Paste in Terminal</p>
          </div>
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <h4 className="font-medium text-sm">Confirm</h4>
            <p className="text-xs text-neutral-500 mt-1">Verify connection</p>
          </div>
        </div>
      </div>

      {/* Registered Routers */}
      <div className="dashboard-card">
        <h2 className="font-semibold mb-4">Registered Routers ({routers.length})</h2>
        
        {routers.length === 0 ? (
          <div className="text-center py-12">
            <Radio className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <p className="text-neutral-400">No routers registered yet</p>
            <Button
              onClick={() => setShowAddRouter(true)}
              variant="outline"
              className="mt-4 border-neutral-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Your First Router
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {routers.map((router) => {
              const statusBadge = getStatusBadge(router.status);
              const hotspot = hotspots.find(h => h.id === router.hotspot_id);
              
              return (
                <div
                  key={router.id}
                  className="p-4 bg-neutral-800/50 rounded-lg border border-neutral-700"
                  data-testid={`router-${router.id}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${router.connection_confirmed ? 'bg-green-400' : 'bg-yellow-400'}`} />
                      <h3 className="font-semibold">{router.name}</h3>
                      <span className={`text-xs px-2 py-1 rounded ${statusBadge.bg} ${statusBadge.text}`}>
                        {statusBadge.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {!router.connection_confirmed && (
                        <Button
                          size="sm"
                          onClick={() => handleConfirmConnection(router)}
                          disabled={confirming}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Confirm
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-neutral-500">Hotspot</p>
                      <p className="font-medium">{hotspot?.name || "Unknown"}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">NAS Identifier</p>
                      <p className="font-mono text-xs">{router.nas_identifier}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">Created</p>
                      <p>{new Date(router.created_at).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-neutral-500">Last Seen</p>
                      <p>{router.last_seen ? new Date(router.last_seen).toLocaleString() : "Never"}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Router Modal */}
      {showAddRouter && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-900 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-neutral-800">
            <div className="p-6 border-b border-neutral-800 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Add MikroTik Router</h2>
              <button
                onClick={() => {
                  setShowAddRouter(false);
                  setGeneratedScript(null);
                  setRouterName("");
                  setSelectedHotspot("");
                }}
                className="p-2 hover:bg-neutral-800 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              {!generatedScript ? (
                <>
                  {/* Router Name Input */}
                  <div>
                    <label className="block text-sm text-neutral-400 mb-2">Router Name</label>
                    <input
                      type="text"
                      value={routerName}
                      onChange={(e) => setRouterName(e.target.value)}
                      placeholder="e.g., Main Office Router"
                      className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
                      data-testid="router-name-input"
                    />
                  </div>
                  
                  {/* Hotspot Selection */}
                  <div>
                    <label className="block text-sm text-neutral-400 mb-2">Select Hotspot</label>
                    <select
                      value={selectedHotspot}
                      onChange={(e) => setSelectedHotspot(e.target.value)}
                      className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
                      data-testid="hotspot-select"
                    >
                      <option value="">Choose a hotspot...</option>
                      {hotspots.map((h) => (
                        <option key={h.id} value={h.id}>{h.name} - {h.location_name}</option>
                      ))}
                    </select>
                  </div>
                  
                  {/* Generate Button */}
                  <Button
                    onClick={handleRegisterRouter}
                    disabled={generating || !selectedHotspot || !routerName.trim()}
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    data-testid="generate-script-btn"
                  >
                    {generating ? (
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <Zap className="w-4 h-4 mr-2" />
                        Generate Configuration Script
                      </>
                    )}
                  </Button>
                </>
              ) : (
                <>
                  {/* Script Generated Success */}
                  <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <div className="flex items-center gap-2 text-green-400 mb-2">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-semibold">Script Generated Successfully!</span>
                    </div>
                    <p className="text-sm text-neutral-400">
                      Copy the script below and paste it into your MikroTik Terminal.
                    </p>
                  </div>
                  
                  {/* Credentials Info */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="p-4 bg-neutral-800/50 rounded-lg">
                      <p className="text-neutral-500 text-sm">NAS Identifier</p>
                      <p className="font-mono text-sm mt-1">{generatedScript.nas_identifier}</p>
                    </div>
                    <div className="p-4 bg-neutral-800/50 rounded-lg">
                      <p className="text-neutral-500 text-sm">RADIUS Secret</p>
                      <p className="font-mono text-sm mt-1 blur-sm hover:blur-none transition-all cursor-pointer">
                        {generatedScript.radius_secret}
                      </p>
                    </div>
                  </div>
                  
                  {/* Instructions */}
                  <div>
                    <h3 className="font-semibold mb-3">Instructions</h3>
                    <ol className="space-y-2 text-sm text-neutral-400">
                      {generatedScript.instructions.map((instruction, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs flex-shrink-0">
                            {i + 1}
                          </span>
                          {instruction.replace(/^\d+\.\s*/, '')}
                        </li>
                      ))}
                    </ol>
                  </div>
                  
                  {/* Script Box */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">Configuration Script</h3>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(generatedScript.script)}
                        className="border-neutral-700"
                      >
                        Copy Script
                      </Button>
                    </div>
                    <div className="bg-neutral-950 rounded-lg p-4 max-h-64 overflow-y-auto">
                      <pre className="text-xs text-neutral-300 whitespace-pre-wrap font-mono">
                        {generatedScript.script}
                      </pre>
                    </div>
                  </div>
                  
                  {/* Close Button */}
                  <Button
                    onClick={() => {
                      setShowAddRouter(false);
                      setGeneratedScript(null);
                      setRouterName("");
                      setSelectedHotspot("");
                    }}
                    variant="outline"
                    className="w-full border-neutral-700"
                  >
                    Close
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Payments Page Component
const PaymentsPage = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      const response = await axios.get(`${API_URL}/payments`);
      setPayments(response.data);
    } catch (error) {
      console.error("Failed to fetch payments:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="payments-page">
      <div>
        <h1 className="text-2xl font-bold">Payment History</h1>
        <p className="text-neutral-400 mt-1">Track all transactions across your hotspots</p>
      </div>

      <div className="dashboard-card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : payments.length === 0 ? (
          <div className="p-8 text-center">
            <CreditCard className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">No payments yet</h3>
            <p className="text-neutral-400 text-sm">
              Payments will appear here when users purchase packages
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Phone</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id}>
                  <td>
                    {new Date(payment.created_at).toLocaleDateString("en-KE", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="font-mono">{payment.phone_number}</td>
                  <td className="font-medium">{formatCurrency(payment.amount)}</td>
                  <td>
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                        payment.status === "completed"
                          ? "badge-active"
                          : payment.status === "pending"
                          ? "badge-pending"
                          : "badge-inactive"
                      }`}
                    >
                      {payment.status}
                    </span>
                  </td>
                  <td className="font-mono text-sm text-neutral-400">
                    {payment.mpesa_receipt || "-"}
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

// Billing & Invoices Page
const BillingPage = () => {
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [payingInvoice, setPayingInvoice] = useState(null);
  
  useEffect(() => {
    fetchBillingData();
  }, []);
  
  const fetchBillingData = async () => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };
      
      const [subRes, invoicesRes] = await Promise.all([
        axios.get(`${API_URL}/subscriptions/status`, { headers }),
        axios.get(`${API_URL}/invoices/`, { headers }),
      ]);
      
      setSubscription(subRes.data);
      setInvoices(invoicesRes.data);
    } catch (error) {
      console.error("Failed to fetch billing data:", error);
    } finally {
      setLoading(false);
    }
  };
  
  const getStatusBadge = (status) => {
    const badges = {
      trial: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Trial" },
      unpaid: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Unpaid" },
      paid: { bg: "bg-green-500/10", text: "text-green-400", label: "Paid" },
      overdue: { bg: "bg-red-500/10", text: "text-red-400", label: "Overdue" },
    };
    return badges[status] || { bg: "bg-gray-500/10", text: "text-gray-400", label: status };
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6" data-testid="billing-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Billing & Invoices</h1>
          <p className="text-neutral-400 mt-1">Manage your subscription and view invoices</p>
        </div>
      </div>
      
      {/* Subscription Summary */}
      {subscription && (
        <div className="dashboard-card">
          <h2 className="font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-400" />
            Subscription Status
          </h2>
          
          <div className="grid md:grid-cols-4 gap-4">
            <div className="p-4 bg-neutral-800/50 rounded-lg">
              <p className="text-neutral-400 text-sm">Status</p>
              <p className="text-lg font-semibold capitalize">{subscription.subscription_status}</p>
            </div>
            <div className="p-4 bg-neutral-800/50 rounded-lg">
              <p className="text-neutral-400 text-sm">Trial Days Left</p>
              <p className="text-lg font-semibold">{subscription.trial_days_remaining}</p>
            </div>
            <div className="p-4 bg-neutral-800/50 rounded-lg">
              <p className="text-neutral-400 text-sm">Hotspots</p>
              <p className="text-lg font-semibold">{subscription.hotspot_count}</p>
            </div>
            <div className="p-4 bg-neutral-800/50 rounded-lg">
              <p className="text-neutral-400 text-sm">Monthly Fee</p>
              <p className="text-lg font-semibold text-green-400">KES {subscription.monthly_fee}</p>
            </div>
          </div>
          
          {subscription.current_invoice && subscription.current_invoice.status !== "paid" && (
            <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-center justify-between">
              <div>
                <p className="font-medium text-yellow-400">Payment Due</p>
                <p className="text-sm text-neutral-400">
                  Invoice #{subscription.current_invoice.invoice_number} - Due: {new Date(subscription.current_invoice.due_date).toLocaleDateString()}
                </p>
              </div>
              <Button 
                onClick={() => setPayingInvoice(subscription.current_invoice)}
                className="bg-yellow-600 hover:bg-yellow-700"
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Pay Now
              </Button>
            </div>
          )}
        </div>
      )}
      
      {/* Invoice History */}
      <div className="dashboard-card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-400" />
          Invoice History
        </h2>
        
        {invoices.length === 0 ? (
          <p className="text-neutral-500 text-center py-8">No invoices yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-neutral-800">
                  <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Invoice #</th>
                  <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Period</th>
                  <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Amount</th>
                  <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Status</th>
                  <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Due Date</th>
                  <th className="text-left py-3 px-4 text-neutral-400 font-medium text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => {
                  const badge = getStatusBadge(invoice.status);
                  return (
                    <tr key={invoice.id} className="border-b border-neutral-800/50">
                      <td className="py-3 px-4 font-mono text-sm">{invoice.invoice_number}</td>
                      <td className="py-3 px-4 text-sm">
                        {new Date(invoice.billing_period_start).toLocaleDateString()} - {new Date(invoice.billing_period_end).toLocaleDateString()}
                      </td>
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
                            onClick={() => setPayingInvoice(invoice)}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            Pay
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
          </div>
        )}
      </div>
      
      {/* Payment Modal */}
      {payingInvoice && (
        <PaymentModal
          invoice={payingInvoice}
          onClose={() => setPayingInvoice(null)}
          onSuccess={fetchBillingData}
        />
      )}
    </div>
  );
};

// Main Dashboard Layout
const OwnerDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = getUser();

  const navigation = [
    { name: "Overview", href: "/owner", icon: LayoutDashboard },
    { name: "Hotspots", href: "/owner/hotspots", icon: Radio },
    { name: "MikroTik Setup", href: "/owner/mikrotik", icon: Zap },
    { name: "Billing", href: "/owner/billing", icon: FileText },
    { name: "Payments", href: "/owner/payments", icon: CreditCard },
    { name: "Analytics", href: "/owner/analytics", icon: BarChart3 },
    { name: "Settings", href: "/owner/settings", icon: Settings },
  ];

  const handleLogout = () => {
    logout();
  };

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
            <span className="font-semibold text-lg">CAIWAVE</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {navigation.map((item) => {
              const isActive =
                location.pathname === item.href ||
                (item.href !== "/owner" && location.pathname.startsWith(item.href));
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
              <div className="w-10 h-10 bg-neutral-800 rounded-full flex items-center justify-center">
                <span className="font-medium text-sm">
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-xs text-neutral-400 truncate">{user?.email}</p>
              </div>
            </div>
            <Button
              variant="outline"
              className="w-full border-neutral-700 text-neutral-400 hover:text-white"
              onClick={handleLogout}
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
            {user?.role === ROLES.SUPER_ADMIN && (
              <Link to="/admin">
                <Button variant="outline" size="sm" className="border-neutral-700">
                  Admin Panel
                </Button>
              </Link>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6 lg:p-8">
          <Routes>
            <Route index element={<DashboardOverview />} />
            <Route path="hotspots" element={<HotspotsPage />} />
            <Route path="mikrotik" element={<MikroTikSetupPage />} />
            <Route path="billing" element={<BillingPage />} />
            <Route path="payments" element={<PaymentsPage />} />
            <Route
              path="analytics"
              element={
                <div className="text-center py-12">
                  <BarChart3 className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Analytics</h2>
                  <p className="text-neutral-400">Detailed analytics coming soon</p>
                </div>
              }
            />
            <Route
              path="settings"
              element={
                <div className="text-center py-12">
                  <Settings className="w-12 h-12 text-neutral-600 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold mb-2">Settings</h2>
                  <p className="text-neutral-400">Account settings coming soon</p>
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

export default OwnerDashboard;
