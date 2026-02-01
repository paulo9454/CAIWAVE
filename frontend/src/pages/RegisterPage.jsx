import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { register, getDashboardPath, ROLES } from "../lib/auth";
import { toast } from "sonner";
import { Wifi, ArrowLeft, Loader2 } from "lucide-react";

const RegisterPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    role: "hotspot_owner",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }

    if (formData.password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }

    setLoading(true);

    try {
      const userData = {
        name: formData.name,
        email: formData.email,
        phone: formData.phone || null,
        password: formData.password,
        role: formData.role,
      };

      const user = await register(userData);
      toast.success("Account created!", { description: `Welcome, ${user.name}!` });
      navigate(getDashboardPath(user.role));
    } catch (error) {
      const message = error.response?.data?.detail || "Registration failed";
      toast.error("Error", { description: message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#0a0a0a] border-r border-neutral-800 flex-col justify-between p-12">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <Wifi className="w-6 h-6 text-white" strokeWidth={1.5} />
          </div>
          <span className="font-semibold text-2xl">CAITECH</span>
        </Link>

        <div className="space-y-6">
          <h1 className="text-4xl font-bold leading-tight">
            Join the Network
            <br />
            <span className="gradient-text">Start Earning Today</span>
          </h1>
          <p className="text-neutral-400 text-lg max-w-md">
            No monthly fees. No complicated setup. Just connect your router and start earning from every WiFi session.
          </p>
          
          <div className="grid grid-cols-2 gap-4 pt-6">
            <div className="bg-neutral-800/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">70%</div>
              <div className="text-neutral-400 text-sm">Revenue Share</div>
            </div>
            <div className="bg-neutral-800/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">KES 5</div>
              <div className="text-neutral-400 text-sm">Min. Package</div>
            </div>
          </div>
        </div>

        <div className="text-neutral-500 text-sm">
          © 2024 CAITECH. All rights reserved.
        </div>
      </div>

      {/* Right Panel - Register Form */}
      <div className="flex-1 flex flex-col">
        <div className="p-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-neutral-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" strokeWidth={1.5} />
            Back to home
          </Link>
        </div>

        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-md space-y-8">
            {/* Mobile Logo */}
            <div className="lg:hidden flex justify-center">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Wifi className="w-6 h-6 text-white" strokeWidth={1.5} />
                </div>
                <span className="font-semibold text-2xl">CAITECH</span>
              </Link>
            </div>

            <div className="text-center lg:text-left">
              <h2 className="text-2xl font-bold">Create your account</h2>
              <p className="text-neutral-400 mt-2">Get started with CAITECH today</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5" data-testid="register-form">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className="bg-neutral-900 border-neutral-800 focus:border-blue-600"
                  data-testid="name-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="bg-neutral-900 border-neutral-800 focus:border-blue-600"
                  data-testid="email-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number (Optional)</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+254 7XX XXX XXX"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="bg-neutral-900 border-neutral-800 focus:border-blue-600"
                  data-testid="phone-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Account Type</Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({ ...formData, role: value })}
                >
                  <SelectTrigger className="bg-neutral-900 border-neutral-800" data-testid="role-select">
                    <SelectValue placeholder="Select account type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hotspot_owner">Hotspot Owner</SelectItem>
                    <SelectItem value="advertiser">Advertiser</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                    className="bg-neutral-900 border-neutral-800 focus:border-blue-600"
                    data-testid="password-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    required
                    className="bg-neutral-900 border-neutral-800 focus:border-blue-600"
                    data-testid="confirm-password-input"
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white btn-glow"
                disabled={loading}
                data-testid="register-submit-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  "Create account"
                )}
              </Button>

              <p className="text-xs text-neutral-500 text-center">
                By creating an account, you agree to our Terms of Service and Privacy Policy.
              </p>
            </form>

            <div className="text-center">
              <p className="text-neutral-400">
                Already have an account?{" "}
                <Link to="/login" className="text-blue-500 hover:text-blue-400 font-medium">
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
