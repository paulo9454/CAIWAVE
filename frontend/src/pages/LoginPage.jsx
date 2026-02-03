import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { login, getDashboardPath } from "../lib/auth";
import { toast } from "sonner";
import { ArrowLeft, Loader2 } from "lucide-react";
import { CaiwaveLogo } from "../components/CaiwaveLogo";

const LoginPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const user = await login(formData.email, formData.password);
      toast.success("Welcome back!", { description: `Logged in as ${user.name}` });
      navigate(getDashboardPath(user.role));
    } catch (error) {
      const message = error.response?.data?.detail || "Invalid credentials";
      toast.error("Login failed", { description: message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#0a0a0a] border-r border-neutral-800 flex-col justify-between p-12">
        <Link to="/" className="flex items-center gap-2">
          <CaiwaveLogo size={40} />
          <span className="font-semibold text-2xl">CAIWAVE</span>
        </Link>

        <div className="space-y-6">
          <h1 className="text-4xl font-bold leading-tight">
            Transform Your WiFi
            <br />
            <span className="gradient-text">Into Revenue</span>
          </h1>
          <p className="text-neutral-400 text-lg max-w-md">
            Manage your hotspots, track earnings, and grow your business with our powerful platform.
          </p>
        </div>

        <div className="text-neutral-500 text-sm">
          © 2026 CAIWAVE. All rights reserved.
        </div>
      </div>

      {/* Right Panel - Login Form */}
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
                <CaiwaveLogo size={40} />
                <span className="font-semibold text-2xl">CAIWAVE</span>
              </Link>
            </div>

            <div className="text-center lg:text-left">
              <h2 className="text-2xl font-bold">Welcome back</h2>
              <p className="text-neutral-400 mt-2">Sign in to your account to continue</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6" data-testid="login-form">
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
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <a href="#" className="text-sm text-blue-500 hover:text-blue-400">
                    Forgot password?
                  </a>
                </div>
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

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white btn-glow"
                disabled={loading}
                data-testid="login-submit-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </Button>
            </form>

            <div className="text-center">
              <p className="text-neutral-400">
                Don't have an account?{" "}
                <Link to="/register" className="text-blue-500 hover:text-blue-400 font-medium">
                  Sign up
                </Link>
              </p>
            </div>

            {/* Demo Credentials */}
            <div className="mt-8 p-4 bg-neutral-900/50 border border-neutral-800 rounded-lg">
              <p className="text-sm text-neutral-400 mb-2">Demo credentials:</p>
              <div className="font-mono text-sm space-y-1">
                <p><span className="text-neutral-500">Admin:</span> admin@caitech.com / admin123</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
