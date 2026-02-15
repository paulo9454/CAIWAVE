import { useState, useEffect } from "react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { API_URL } from "../../lib/utils";
import { getAuthToken } from "../../lib/auth";
import axios from "axios";
import { toast } from "sonner";
import {
  Building2,
  CreditCard,
  CheckCircle,
  AlertCircle,
  Loader2,
  Banknote,
  Phone,
  Mail,
} from "lucide-react";

const PaymentSettings = () => {
  const [banks, setBanks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [subaccountStatus, setSubaccountStatus] = useState(null);
  const [formData, setFormData] = useState({
    business_name: "",
    settlement_bank: "",
    account_number: "",
    primary_contact_email: "",
    primary_contact_phone: "",
  });

  useEffect(() => {
    fetchBanks();
    checkSubaccountStatus();
  }, []);

  const fetchBanks = async () => {
    try {
      const response = await axios.get(`${API_URL}/paystack/banks`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      setBanks(response.data || []);
    } catch (error) {
      console.error("Failed to fetch banks:", error);
      toast.error("Failed to load banks list");
    } finally {
      setLoading(false);
    }
  };

  const checkSubaccountStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` }
      });
      const user = response.data;
      if (user.paystack_subaccount_code) {
        setSubaccountStatus({
          connected: true,
          code: user.paystack_subaccount_code,
          bank_name: user.bank_name,
          account_number: user.account_number,
        });
      }
    } catch (error) {
      console.error("Failed to check subaccount status:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const response = await axios.post(
        `${API_URL}/paystack/subaccount/create`,
        {
          business_name: formData.business_name,
          bank_code: formData.settlement_bank,
          account_number: formData.account_number,
          percentage_charge: 30, // Owner gets 30% by default
          email: formData.primary_contact_email || undefined,
          phone: formData.primary_contact_phone || undefined,
        },
        {
          headers: { Authorization: `Bearer ${getAuthToken()}` }
        }
      );
      
      toast.success("Bank account connected successfully!");
      setSubaccountStatus({
        connected: true,
        code: response.data.subaccount_code,
        bank_name: banks.find(b => b.code === formData.settlement_bank)?.name,
        account_number: formData.account_number,
      });
    } catch (error) {
      const message = error.response?.data?.detail || "Failed to connect bank account";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="payment-settings-page">
      <div>
        <h1 className="text-2xl font-bold">Payment Settings</h1>
        <p className="text-neutral-400 mt-1">
          Connect your bank account to receive your share of WiFi payments
        </p>
      </div>

      {/* Current Status Card */}
      <div className={`p-6 rounded-xl border ${
        subaccountStatus?.connected 
          ? "bg-green-500/10 border-green-500/30" 
          : "bg-yellow-500/10 border-yellow-500/30"
      }`}>
        <div className="flex items-start gap-4">
          {subaccountStatus?.connected ? (
            <CheckCircle className="w-6 h-6 text-green-400 mt-1" />
          ) : (
            <AlertCircle className="w-6 h-6 text-yellow-400 mt-1" />
          )}
          <div>
            <h3 className="font-semibold text-lg">
              {subaccountStatus?.connected ? "Bank Account Connected" : "Bank Account Not Connected"}
            </h3>
            {subaccountStatus?.connected ? (
              <div className="mt-2 space-y-1 text-sm text-neutral-300">
                <p><span className="text-neutral-400">Bank:</span> {subaccountStatus.bank_name}</p>
                <p><span className="text-neutral-400">Account:</span> ****{subaccountStatus.account_number?.slice(-4)}</p>
                <p className="text-green-400 mt-2">
                  You will automatically receive your share when WiFi users make payments at your hotspots.
                </p>
              </div>
            ) : (
              <p className="text-neutral-400 mt-1">
                Connect your bank account to automatically receive your revenue share from WiFi payments.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Revenue Split Info */}
      <div className="dashboard-card p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Banknote className="w-5 h-5 text-blue-400" />
          How Revenue Sharing Works
        </h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
            <span className="text-neutral-400">Your Share (Hotspot Owner)</span>
            <span className="font-semibold text-green-400">30-50%</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg">
            <span className="text-neutral-400">Platform Fee (CAIWAVE)</span>
            <span className="font-semibold text-blue-400">50-70%</span>
          </div>
          <p className="text-neutral-500 text-xs mt-2">
            * Exact split depends on your partnership tier and hotspot performance
          </p>
        </div>
      </div>

      {/* Bank Account Form */}
      {!subaccountStatus?.connected && (
        <div className="dashboard-card p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-400" />
            Connect Bank Account
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Business/Account Name *</label>
              <Input
                value={formData.business_name}
                onChange={(e) => setFormData({...formData, business_name: e.target.value})}
                placeholder="e.g., John's Cyber Cafe"
                required
                data-testid="business-name-input"
              />
              <p className="text-xs text-neutral-500 mt-1">Name as it appears on your bank account</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Select Bank *</label>
              <select
                className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={formData.settlement_bank}
                onChange={(e) => setFormData({...formData, settlement_bank: e.target.value})}
                required
                data-testid="bank-select"
              >
                <option value="">Select your bank</option>
                {banks.map((bank) => (
                  <option key={bank.code} value={bank.code}>
                    {bank.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Account Number *</label>
              <Input
                value={formData.account_number}
                onChange={(e) => setFormData({...formData, account_number: e.target.value})}
                placeholder="Enter your account number"
                required
                data-testid="account-number-input"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Contact Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                  <Input
                    type="email"
                    className="pl-10"
                    value={formData.primary_contact_email}
                    onChange={(e) => setFormData({...formData, primary_contact_email: e.target.value})}
                    placeholder="email@example.com"
                    data-testid="contact-email-input"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Contact Phone</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                  <Input
                    className="pl-10"
                    value={formData.primary_contact_phone}
                    onChange={(e) => setFormData({...formData, primary_contact_phone: e.target.value})}
                    placeholder="0712345678"
                    data-testid="contact-phone-input"
                  />
                </div>
              </div>
            </div>

            <div className="pt-4">
              <Button 
                type="submit" 
                disabled={submitting} 
                className="w-full"
                data-testid="connect-bank-btn"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <CreditCard className="w-4 h-4 mr-2" />
                    Connect Bank Account
                  </>
                )}
              </Button>
            </div>

            <p className="text-xs text-neutral-500 text-center">
              By connecting your bank account, you agree to receive automatic payouts for your revenue share.
              Payouts are processed within 24-48 hours of each transaction.
            </p>
          </form>
        </div>
      )}

      {/* Already Connected - Show Update Option */}
      {subaccountStatus?.connected && (
        <div className="dashboard-card p-6">
          <h3 className="font-semibold mb-4">Need to Update Your Bank Details?</h3>
          <p className="text-neutral-400 text-sm mb-4">
            Contact CAIWAVE support to update your bank account details.
          </p>
          <Button variant="outline" asChild>
            <a href="tel:0738570630">Contact Support</a>
          </Button>
        </div>
      )}
    </div>
  );
};

export default PaymentSettings;
