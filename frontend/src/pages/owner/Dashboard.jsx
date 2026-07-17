import { safeError } from "../../utils/safeError";
import { useState, useEffect, useCallback } from "react";
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
  Wallet,
  Copy,
  Ticket,
  RefreshCw,
  Ban,
  Wifi,
} from "lucide-react";
import { CaiwaveLogo } from "../../components/CaiwaveLogo";
import HotspotLocationFields from "../../components/HotspotLocationFields";
import HotspotLocationEditor from "../../components/HotspotLocationEditor";
import HotspotLocationSummary from "../../components/HotspotLocationSummary";
import PaymentSettings from "./PaymentSettings";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
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
      case "lifetime":
        return {
          bg: "bg-purple-500/10 border-purple-500/30",
          icon: <CheckCircle className="w-5 h-5 text-purple-400" />,
          title: "Lifetime Access",
          description: "You have lifetime access. No subscription fees required!",
          showPayButton: false,
          urgent: false
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
      toast.error(safeError(error));
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

    const interval = setInterval(() => {
      fetchData();
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, hotspotsRes, subscriptionRes] = await Promise.all([
        axios.get(`${API_URL}/analytics/dashboard`, { headers }),
        axios.get(`${API_URL}/hotspots/`, { headers }),
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

  const renderDiagnosticItem = (label, passed, detail = "") => (
    <div className="flex items-start gap-2 text-sm">
      <span className={passed ? "text-green-400" : "text-yellow-400"}>
        {passed ? "✓" : "⚠"}
      </span>
      <div>
        <p className={passed ? "text-neutral-200" : "text-neutral-300"}>{label}</p>
        {detail && <p className="text-xs text-neutral-500">{detail}</p>}
      </div>
    </div>
  );

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
                          hotspot.status === "active"
                            ? "bg-green-500"
                            : "bg-neutral-500"
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
  const [editingLocationHotspot, setEditingLocationHotspot] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    ssid: "",
    country_code: "KE",
    country_name: "Kenya",
    county: "",
    constituency: "",
    ward: "",
    location_name: "",
  });

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

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
        country_code: "KE",
        country_name: "Kenya",
        county: "",
        constituency: "",
        ward: "",
        location_name: "",
      });
      fetchHotspots();
    } catch (error) {
      toast.error(safeError(error));
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
            <HotspotLocationFields
              value={formData}
              onChange={setFormData}
            />
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

      {editingLocationHotspot && (
        <HotspotLocationEditor
          hotspot={editingLocationHotspot}
          onClose={() => setEditingLocationHotspot(null)}
          onSaved={fetchHotspots}
        />
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
                <th>Hotspot ID</th>
                <th>SSID</th>
                <th>Location</th>
                <th>Status</th>
                <th>Sessions</th>
                <th>Revenue</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {hotspots.map((hotspot) => (
                <tr key={hotspot.id}>
                  <td className="font-medium">{hotspot.name}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <code className="font-mono text-xs text-blue-400">{hotspot.id}</code>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(hotspot.id)}
                        className="text-neutral-400 hover:text-white"
                        title="Copy hotspot ID"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                  <td className="font-mono text-sm text-neutral-400">{hotspot.ssid}</td>
                  <td>
                    <HotspotLocationSummary hotspot={hotspot} />
                  </td>
                  <td>
                    {(() => {
                      const isActive = hotspot.status === "active";

                      return (
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                            isActive ? "badge-active" : "badge-inactive"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isActive ? "bg-green-500" : "bg-neutral-500"
                            }`}
                          />
                          {isActive ? "Active" : "Inactive"}
                        </span>
                      );
                    })()}
                  </td>
                  <td>{hotspot.total_sessions || 0}</td>
                  <td className="font-medium">
                    {formatCurrency(hotspot.total_revenue || 0)}
                  </td>
                  <td>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingLocationHotspot(hotspot)}
                    >
                      Edit Location
                    </Button>
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
  const [diagnostics, setDiagnostics] = useState({});
  const [timelines, setTimelines] = useState({});

  useEffect(() => {
    fetchData();

    const interval = setInterval(() => {
      fetchData();
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };
      
      const [hotspotsRes, routersRes] = await Promise.all([
        axios.get(`${API_URL}/hotspots/`, { headers }),
        axios.get(`${API_URL}/mikrotik-onboard/routers`, { headers }),
      ]);
      
      setHotspots(hotspotsRes.data);
      setRouters(routersRes.data);
      fetchDiagnostics(routersRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDiagnostics = async (routerList = routers) => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };

      const results = await Promise.all(
        routerList.map(async (router) => {
          try {
            const res = await axios.get(
              `${API_URL}/mikrotik-onboard/routers/${router.id}/diagnostics`,
              { headers }
            );
            return [router.id, res.data];
          } catch (err) {
            console.error("Failed to fetch router diagnostics:", router.id, err);
            return [router.id, null];
          }
        })
      );

      setDiagnostics(Object.fromEntries(results));
      await fetchTimelines(routerList);
    } catch (error) {
      console.error("Failed to fetch diagnostics:", error);
    }
  };

  const fetchTimelines = async (routerList = routers) => {
    try {
      const token = getAuthToken();
      const headers = { Authorization: `Bearer ${token}` };

      const results = await Promise.all(
        routerList.map(async (router) => {
          try {
            const res = await axios.get(
              `${API_URL}/mikrotik-onboard/routers/${router.id}/timeline?limit=5`,
              { headers }
            );
            return [router.id, res.data.events || []];
          } catch (err) {
            console.error("Failed to fetch router timeline:", router.id, err);
            return [router.id, []];
          }
        })
      );

      setTimelines(Object.fromEntries(results));
    } catch (error) {
      console.error("Failed to fetch timelines:", error);
    }
  };

  const formatAge = (seconds) => {
    if (seconds === null || seconds === undefined) return "unknown";
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
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
          bootstrap_token: "owner-dashboard",
          name: routerName.trim(),
          hotspot_id: selectedHotspot,
          wan_interface: "ether1",
          lan_interfaces: ["ether2", "ether3", "ether4", "ether5"],
          create_bridge: true,
          bridge_name: "bridge-hotspot",
          mode: "fresh",
          hotspot_cidr: "10.10.0.1/24",
          dhcp_pool: "10.10.0.10-10.10.0.254",
          dns_name: "login.caiwave.local",
        },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } }
      );
      
      setGeneratedScript(response.data);
      toast.success("Provisioning .rsc file generated!");
      fetchData();
    } catch (error) {
      toast.error(safeError(error));
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
      toast.error(safeError(error));
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

  const renderDiagnosticItem = (label, passed, detail = "") => (
    <div className="flex items-start gap-2 text-sm">
      <span className={passed ? "text-green-400" : "text-yellow-400"}>
        {passed ? "✓" : "⚠"}
      </span>
      <div>
        <p className={passed ? "text-neutral-200" : "text-neutral-300"}>{label}</p>
        {detail && <p className="text-xs text-neutral-500">{detail}</p>}
      </div>
    </div>
  );

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
        <div className="flex gap-2">
          <a href="/setup" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" className="border-blue-500 text-blue-400">
              Full Setup Wizard
            </Button>
          </a>
          <Button
            onClick={() => setShowAddRouter(true)}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="add-mikrotik-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add MikroTik
          </Button>
        </div>
      </div>

      {/* Setup Steps */}
      <div className="dashboard-card">
        <h2 className="font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-400" />
          Setup Steps
        </h2>
        <div className="grid md:grid-cols-4 gap-4">
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">1</span>
            </div>
            <h4 className="font-medium text-sm">Open WinBox</h4>
            <p className="text-xs text-neutral-500 mt-1">Connect to MikroTik</p>
          </div>
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">2</span>
            </div>
            <h4 className="font-medium text-sm">Upload .rsc</h4>
            <p className="text-xs text-neutral-500 mt-1">Upload file to MikroTik</p>
          </div>
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">3</span>
            </div>
            <h4 className="font-medium text-sm">Import File</h4>
            <p className="text-xs text-neutral-500 mt-1">Run import command</p>
          </div>
          <div className="p-4 bg-neutral-800/50 rounded-lg text-center">
            <div className="w-10 h-10 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
            <h4 className="font-medium text-sm">Confirm</h4>
            <p className="text-xs text-neutral-500 mt-1">Confirm connection</p>
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

                  {diagnostics[router.id] && (
                    <div className="mt-4 p-4 bg-neutral-900/70 border border-neutral-800 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-semibold">Router Diagnostics</h4>
                          <p className="text-xs text-neutral-500">{diagnostics[router.id].next_action}</p>
                          <p className="text-xs text-neutral-600 mt-1">
                            Auto-refreshing every 15s · heartbeat {formatAge(diagnostics[router.id].router?.heartbeat_age_seconds)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xl font-bold text-blue-400">{diagnostics[router.id].score}%</p>
                          <p className="text-xs text-neutral-500">
                            {diagnostics[router.id].passed}/{diagnostics[router.id].total} checks
                          </p>
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-3">
                        {renderDiagnosticItem("Heartbeat received", diagnostics[router.id].checks?.heartbeat_received)}
                        {renderDiagnosticItem("Heartbeat recent", diagnostics[router.id].checks?.heartbeat_recent)}
                        {renderDiagnosticItem("Router online", diagnostics[router.id].checks?.router_online)}
                        {renderDiagnosticItem("Connection confirmed", diagnostics[router.id].checks?.connection_confirmed)}
                        {renderDiagnosticItem("RADIUS configured", diagnostics[router.id].checks?.radius_configured)}
                        {renderDiagnosticItem("Paystack configured", diagnostics[router.id].checks?.paystack_configured)}
                        {renderDiagnosticItem("Bridge configured", diagnostics[router.id].checks?.bridge_configured)}
                        {renderDiagnosticItem("LAN ports configured", diagnostics[router.id].checks?.lan_ports_configured)}
                        {renderDiagnosticItem("DHCP configured", diagnostics[router.id].checks?.dhcp_configured)}
                        {renderDiagnosticItem("NAT configured", diagnostics[router.id].checks?.nat_configured)}
                        {renderDiagnosticItem("Hotspot configured", diagnostics[router.id].checks?.hotspot_configured)}
                        {renderDiagnosticItem("RADIUS client configured", diagnostics[router.id].checks?.radius_client_configured)}
                        {renderDiagnosticItem("Heartbeat scheduler configured", diagnostics[router.id].checks?.heartbeat_scheduler_configured)}
                        {renderDiagnosticItem("Walled garden configured", diagnostics[router.id].checks?.walled_garden_configured)}
                        {renderDiagnosticItem("First login seen", diagnostics[router.id].checks?.first_auth_seen)}
                        {renderDiagnosticItem("First login accepted", diagnostics[router.id].checks?.first_auth_success)}
                        {renderDiagnosticItem("Accounting seen", diagnostics[router.id].checks?.accounting_seen)}
                        {renderDiagnosticItem("Provisioning file generated", diagnostics[router.id].checks?.rsc_generated)}
                      </div>

                      {timelines[router.id]?.length > 0 && (
                        <div className="mt-4 border-t border-neutral-800 pt-3">
                          <h5 className="font-medium text-sm mb-2">Recent Timeline</h5>
                          <div className="space-y-2">
                            {timelines[router.id].map((event) => (
                              <div key={event.id} className="flex items-start gap-2 text-sm">
                                <span className={
                                  event.severity === "success" ? "text-green-400" :
                                  event.severity === "warning" ? "text-yellow-400" :
                                  event.severity === "error" ? "text-red-400" :
                                  "text-blue-400"
                                }>
                                  ●
                                </span>
                                <div>
                                  <p className="text-neutral-200">{event.title}</p>
                                  <p className="text-xs text-neutral-500">
                                    {new Date(event.timestamp).toLocaleString()} · {event.event_type}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-3 flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-neutral-700"
                          onClick={() => fetchDiagnostics([router])}
                        >
                          Refresh Diagnostics
                        </Button>
                        {diagnostics[router.id].production_ready && (
                          <span className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400">
                            Production Ready
                          </span>
                        )}
                      </div>
                    </div>
                  )}
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
                    <div className="mb-3 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm">
                      Recommended flow: this process links the MikroTik router to a specific hotspot ID in CAIWAVE.
                    </div>
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
                        Generate Provisioning File
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
                      <span className="font-semibold">Provisioning File Generated Successfully!</span>
                    </div>
                    <p className="text-sm text-neutral-400">
                      Download the .rsc file and import it into your MikroTik router.
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
                  <div className="p-3 mt-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-300 text-sm">
                    Router mapping context captured: selected hotspot ID, generated NAS identifier, and RADIUS secret are now tied to this onboarding session.
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
                  
                  {/* RSC Provisioning File */}
                  <div className="p-4 bg-neutral-900/70 border border-neutral-800 rounded-lg">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <h3 className="font-semibold">MikroTik .rsc Provisioning File</h3>
                        <p className="text-sm text-neutral-400 mt-1">
                          Download this file, upload it to MikroTik, then import it from RouterOS terminal.
                        </p>
                        <p className="text-xs text-neutral-500 mt-2 font-mono">
                          {generatedScript.single_rsc_provisioning?.filename || "caiwave-provisioning.rsc"}
                        </p>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-3">
                      <Button
                        onClick={() => {
                          const file = generatedScript.single_rsc_provisioning;
                          const blob = new Blob([file.content], { type: file.content_type || "text/plain" });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = file.filename || "caiwave-provisioning.rsc";
                          document.body.appendChild(a);
                          a.click();
                          a.remove();
                          URL.revokeObjectURL(url);
                        }}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        Download .rsc File
                      </Button>

                      <Button
                        variant="outline"
                        onClick={() => {
                          navigator.clipboard.writeText(generatedScript.single_rsc_provisioning?.content || "");
                          toast.success(".rsc content copied to clipboard!");
                        }}
                        className="border-neutral-700"
                      >
                        Copy .rsc Content
                      </Button>
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
      const response = await axios.get(`${API_URL}/payments/`);
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
  
  const renderDiagnosticItem = (label, passed, detail = "") => (
    <div className="flex items-start gap-2 text-sm">
      <span className={passed ? "text-green-400" : "text-yellow-400"}>
        {passed ? "✓" : "⚠"}
      </span>
      <div>
        <p className={passed ? "text-neutral-200" : "text-neutral-300"}>{label}</p>
        {detail && <p className="text-xs text-neutral-500">{detail}</p>}
      </div>
    </div>
  );

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

// Voucher Management Page
const EMPTY_VOUCHER_SUMMARY = {
  total: 0,
  unused: 0,
  processing: 0,
  redeemed: 0,
  revoked: 0,
  expired: 0,
};

const VoucherManagementPage = () => {

  const [hotspots, setHotspots] = useState([]);
  const [selectedHotspotId, setSelectedHotspotId] = useState("");
  const [summary, setSummary] = useState(EMPTY_VOUCHER_SUMMARY);
  const [batches, setBatches] = useState([]);
  const [loadingHotspots, setLoadingHotspots] = useState(true);
  const [loadingVouchers, setLoadingVouchers] = useState(false);
  const [loadError, setLoadError] = useState("");

  const authHeaders = () => ({
    Authorization: `Bearer ${getAuthToken()}`,
  });

  const fetchHotspots = useCallback(async () => {
    setLoadingHotspots(true);
    setLoadError("");

    try {
      const response = await axios.get(
        `${API_URL}/hotspots/`,
        { headers: authHeaders() }
      );

      const ownerHotspots = Array.isArray(response.data)
        ? response.data
        : [];

      setHotspots(ownerHotspots);

      setSelectedHotspotId((current) => {
        if (
          current &&
          ownerHotspots.some((hotspot) => hotspot.id === current)
        ) {
          return current;
        }

        return ownerHotspots[0]?.id || "";
      });
    } catch (error) {
      setLoadError(safeError(error));
      setHotspots([]);
      setSelectedHotspotId("");
    } finally {
      setLoadingHotspots(false);
    }
  }, []);

  const fetchVoucherData = useCallback(async (hotspotId) => {
    if (!hotspotId) {
      setSummary(EMPTY_VOUCHER_SUMMARY);
      setBatches([]);
      return;
    }

    setLoadingVouchers(true);
    setLoadError("");

    try {
      const headers = authHeaders();
      const params = { hotspot_id: hotspotId };

      const [summaryResponse, batchesResponse] = await Promise.all([
        axios.get(`${API_URL}/vouchers/summary`, {
          headers,
          params,
        }),
        axios.get(`${API_URL}/vouchers/batches`, {
          headers,
          params,
        }),
      ]);

      setSummary({
        ...EMPTY_VOUCHER_SUMMARY,
        ...(summaryResponse.data || {}),
      });

      setBatches(
        Array.isArray(batchesResponse.data)
          ? batchesResponse.data
          : []
      );
    } catch (error) {
      setLoadError(safeError(error));
      setSummary(EMPTY_VOUCHER_SUMMARY);
      setBatches([]);
    } finally {
      setLoadingVouchers(false);
    }
  }, []);

  useEffect(() => {
    fetchHotspots();
  }, [fetchHotspots]);

  useEffect(() => {
    fetchVoucherData(selectedHotspotId);
  }, [fetchVoucherData, selectedHotspotId]);

  const selectedHotspot = hotspots.find(
    (hotspot) => hotspot.id === selectedHotspotId
  );

  const summaryCards = [
    {
      label: "Total",
      value: summary.total,
      icon: Ticket,
      className: "text-blue-400",
    },
    {
      label: "Unused",
      value: summary.unused,
      icon: CheckCircle,
      className: "text-green-400",
    },
    {
      label: "Redeemed",
      value: summary.redeemed,
      icon: Wifi,
      className: "text-purple-400",
    },
    {
      label: "Revoked",
      value: summary.revoked,
      icon: Ban,
      className: "text-red-400",
    },
    {
      label: "Expired",
      value: summary.expired,
      icon: Clock,
      className: "text-orange-400",
    },
  ];

  const formatVoucherDate = (value) => {
    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "—";
    }

    return date.toLocaleString();
  };

  return (
    <div>
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voucher Management</h1>
          <p className="mt-1 text-neutral-400">
            Generate, manage, and track prepaid WiFi vouchers for your hotspots.
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          className="border-neutral-700"
          onClick={() => {
            fetchHotspots();

            if (selectedHotspotId) {
              fetchVoucherData(selectedHotspotId);
            }
          }}
          disabled={loadingHotspots || loadingVouchers}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${
              loadingHotspots || loadingVouchers
                ? "animate-spin"
                : ""
            }`}
          />
          Refresh
        </Button>
      </div>

      {loadError && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-red-400" />
            <div>
              <p className="font-medium text-red-300">
                Voucher data could not be loaded
              </p>
              <p className="mt-1 text-sm text-red-200/70">
                {loadError}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="mb-6 rounded-xl border border-neutral-800 bg-neutral-900 p-5">
        <label
          htmlFor="voucher-hotspot"
          className="mb-2 block text-sm font-medium text-neutral-300"
        >
          Hotspot
        </label>

        {loadingHotspots ? (
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading hotspots…
          </div>
        ) : hotspots.length === 0 ? (
          <div className="rounded-lg border border-dashed border-neutral-700 p-5 text-sm text-neutral-400">
            No hotspots are available. Create and activate a hotspot before
            generating vouchers.
          </div>
        ) : (
          <>
            <select
              id="voucher-hotspot"
              value={selectedHotspotId}
              onChange={(event) =>
                setSelectedHotspotId(event.target.value)
              }
              className="w-full rounded-lg border border-neutral-700 bg-neutral-950 px-4 py-3 text-white outline-none focus:border-blue-500"
            >
              {hotspots.map((hotspot) => (
                <option key={hotspot.id} value={hotspot.id}>
                  {hotspot.name || hotspot.ssid || hotspot.id}
                </option>
              ))}
            </select>

            {selectedHotspot && (
              <p className="mt-2 text-xs text-neutral-500">
                {selectedHotspot.ssid
                  ? `SSID: ${selectedHotspot.ssid}`
                  : "Selected hotspot"}
                {selectedHotspot.location_name
                  ? ` • ${selectedHotspot.location_name}`
                  : ""}
              </p>
            )}
          </>
        )}
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-400">
                {card.label}
              </p>
              <card.icon className={`h-5 w-5 ${card.className}`} />
            </div>

            <p className="mt-3 text-3xl font-bold">
              {loadingVouchers ? "—" : card.value}
            </p>
          </div>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900">
        <div className="border-b border-neutral-800 px-5 py-4">
          <h2 className="font-semibold">Voucher Batches</h2>
          <p className="mt-1 text-sm text-neutral-400">
            Voucher batches created for the selected hotspot.
          </p>
        </div>

        {loadingVouchers ? (
          <div className="flex items-center justify-center gap-3 p-12 text-neutral-400">
            <RefreshCw className="h-5 w-5 animate-spin" />
            Loading voucher batches…
          </div>
        ) : !selectedHotspotId ? (
          <div className="p-12 text-center text-neutral-400">
            Select a hotspot to view voucher batches.
          </div>
        ) : batches.length === 0 ? (
          <div className="p-12 text-center">
            <Ticket className="mx-auto mb-4 h-10 w-10 text-neutral-600" />
            <h3 className="font-medium">No voucher batches yet</h3>
            <p className="mt-1 text-sm text-neutral-500">
              Generated voucher batches will appear here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-800">
              <thead className="bg-neutral-950/60">
                <tr className="text-left text-xs uppercase tracking-wide text-neutral-500">
                  <th className="px-5 py-3">Batch</th>
                  <th className="px-5 py-3">Purpose</th>
                  <th className="px-5 py-3">Created</th>
                  <th className="px-5 py-3">Total</th>
                  <th className="px-5 py-3">Unused</th>
                  <th className="px-5 py-3">Redeemed</th>
                  <th className="px-5 py-3">Revoked</th>
                  <th className="px-5 py-3">Expired</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-neutral-800">
                {batches.map((batch) => (
                  <tr
                    key={batch.batch_id}
                    className="text-sm hover:bg-neutral-800/40"
                  >
                    <td className="px-5 py-4">
                      <p className="font-medium text-white">
                        {batch.batch_name || "Unnamed batch"}
                      </p>
                      <p className="mt-1 font-mono text-xs text-neutral-500">
                        {batch.batch_id}
                      </p>
                    </td>
                    <td className="px-5 py-4 capitalize text-neutral-300">
                      {(batch.purpose || "standard").replaceAll("_", " ")}
                    </td>
                    <td className="whitespace-nowrap px-5 py-4 text-neutral-400">
                      {formatVoucherDate(batch.created_at)}
                    </td>
                    <td className="px-5 py-4 font-medium">
                      {batch.total}
                    </td>
                    <td className="px-5 py-4 text-green-400">
                      {batch.unused}
                    </td>
                    <td className="px-5 py-4 text-purple-400">
                      {batch.redeemed}
                    </td>
                    <td className="px-5 py-4 text-red-400">
                      {batch.revoked}
                    </td>
                    <td className="px-5 py-4 text-orange-400">
                      {batch.expired}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
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
    { name: "Vouchers", href: "/owner/vouchers", icon: Ticket },
    { name: "MikroTik Setup", href: "/owner/mikrotik", icon: Zap },
    { name: "Billing", href: "/owner/billing", icon: FileText },
    { name: "Payments", href: "/owner/payments", icon: CreditCard },
    { name: "Payouts", href: "/owner/payouts", icon: Wallet },
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
            <Route path="vouchers" element={<VoucherManagementPage />} />
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
              path="payouts"
              element={<PaymentSettings />}
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
