import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { isAuthenticated, getUser, getDashboardPath } from "../lib/auth";
import { CaiwaveLogo } from "../components/CaiwaveLogo";
import {
  Wifi,
  TrendingUp,
  Users,
  MapPin,
  Shield,
  Zap,
  ChevronRight,
  Menu,
  X,
  Target,
  DollarSign,
  BarChart3,
  Radio,
  Tv,
  Play,
  Check,
} from "lucide-react";

const LandingPage = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const authenticated = isAuthenticated();
  const user = getUser();

  const handleGetStarted = () => {
    if (authenticated && user) {
      navigate(getDashboardPath(user.role));
    } else {
      navigate("/register");
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden text-white" style={{ backgroundColor: '#050505' }}>
      {/* Navigation */}
      <nav className="nav-glass fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-6 lg:px-12">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2" data-testid="logo">
              <CaiwaveLogo size={32} />
              <span className="font-semibold text-xl tracking-tight">CAIWAVE</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-neutral-400 hover:text-white transition-colors text-sm">
                Features
              </a>
              <a href="#how-it-works" className="text-neutral-400 hover:text-white transition-colors text-sm">
                How It Works
              </a>
              <a href="#pricing" className="text-neutral-400 hover:text-white transition-colors text-sm">
                Pricing
              </a>
              <a href="#caiwave-tv" className="text-neutral-400 hover:text-white transition-colors text-sm">
                CAIWAVE TV
              </a>
              <a href="#advertisers" className="text-neutral-400 hover:text-white transition-colors text-sm">
                For Advertisers
              </a>
            </div>

            <div className="hidden md:flex items-center gap-4">
              {authenticated ? (
                <Button
                  onClick={handleGetStarted}
                  className="bg-blue-600 hover:bg-blue-700 text-white btn-glow"
                  data-testid="dashboard-btn"
                >
                  Dashboard
                </Button>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" className="text-neutral-300 hover:text-white" data-testid="login-btn">
                      Sign In
                    </Button>
                  </Link>
                  <Button
                    onClick={handleGetStarted}
                    className="bg-blue-600 hover:bg-blue-700 text-white btn-glow"
                    data-testid="get-started-btn"
                  >
                    Get Started
                  </Button>
                </>
              )}
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#0a0a0a] border-t border-neutral-800 px-6 py-4">
            <div className="flex flex-col gap-4">
              <a href="#features" className="text-neutral-300 py-2">Features</a>
              <a href="#how-it-works" className="text-neutral-300 py-2">How It Works</a>
              <a href="#pricing" className="text-neutral-300 py-2">Pricing</a>
              <a href="#advertisers" className="text-neutral-300 py-2">For Advertisers</a>
              <div className="border-t border-neutral-800 pt-4 flex flex-col gap-2">
                {authenticated ? (
                  <Button onClick={handleGetStarted} className="bg-blue-600 w-full">
                    Dashboard
                  </Button>
                ) : (
                  <>
                    <Link to="/login" className="w-full">
                      <Button variant="outline" className="w-full border-neutral-700">Sign In</Button>
                    </Link>
                    <Button onClick={handleGetStarted} className="bg-blue-600 w-full">
                      Get Started
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 lg:px-12 relative">
        <div className="hero-gradient absolute inset-0 pointer-events-none" />
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600/10 border border-blue-600/20 rounded-full text-blue-400 text-sm">
                <Zap className="w-4 h-4" strokeWidth={1.5} />
                No Monthly Subscription
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
                Transform Your WiFi
                <br />
                <span className="gradient-text">Into Revenue</span>
              </h1>
              
              <p className="text-lg text-neutral-400 max-w-xl leading-relaxed">
                The complete hotspot billing platform with integrated advertising engine. 
                Earn from every connection while providing seamless internet access starting from KES 5.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Button
                  onClick={handleGetStarted}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white btn-glow px-8"
                  data-testid="hero-cta-btn"
                >
                  Start Earning Today
                  <ChevronRight className="w-5 h-5 ml-2" strokeWidth={1.5} />
                </Button>
                <a href="#how-it-works">
                  <Button size="lg" variant="outline" className="border-neutral-700 text-neutral-300 hover:bg-neutral-800">
                    See How It Works
                  </Button>
                </a>
              </div>
              
              <div className="flex items-center gap-8 pt-4">
                <div>
                  <div className="text-2xl font-bold">500+</div>
                  <div className="text-neutral-500 text-sm">Active Hotspots</div>
                </div>
                <div className="w-px h-12 bg-neutral-800" />
                <div>
                  <div className="text-2xl font-bold">50K+</div>
                  <div className="text-neutral-500 text-sm">Daily Users</div>
                </div>
                <div className="w-px h-12 bg-neutral-800" />
                <div>
                  <div className="text-2xl font-bold">KES 5</div>
                  <div className="text-neutral-500 text-sm">Starting Price</div>
                </div>
              </div>
            </div>
            
            <div className="relative hidden lg:block">
              <div className="relative rounded-xl overflow-hidden border border-neutral-800">
                <img
                  src="https://images.unsplash.com/photo-1680691257251-5fead813b73e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NjV8MHwxfHNlYXJjaHwxfHxzZXJ2ZXIlMjByYWNrJTIwYmx1ZXxlbnwwfHx8fDE3Njk5ODQ5NDh8MA&ixlib=rb-4.1.0&q=85&w=800"
                  alt="Network Infrastructure"
                  className="w-full h-auto object-cover opacity-80"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent to-transparent" />
              </div>
              
              {/* Floating Stats Card */}
              <div className="absolute -bottom-6 -left-6 bg-[#0a0a0a] border border-neutral-800 rounded-xl p-4 shadow-lg">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-green-500" strokeWidth={1.5} />
                  </div>
                  <div>
                    <div className="text-sm text-neutral-400">Today&apos;s Revenue</div>
                    <div className="font-semibold">KES 24,500</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 lg:px-12" style={{ backgroundColor: '#0a0a0a' }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Everything You Need to Run a
              <br />
              <span className="gradient-text">Profitable Hotspot Business</span>
            </h2>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              Professional ISP-grade tools without the complexity or monthly fees
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: DollarSign,
                title: "Micro-Pricing Support",
                description: "Accept payments from KES 5. Perfect for markets, shops, and high-traffic areas.",
              },
              {
                icon: Target,
                title: "Location-Based Ads",
                description: "Target ads by county, constituency, ward, or specific hotspot. Perfect for political campaigns.",
              },
              {
                icon: Radio,
                title: "MikroTik Integration",
                description: "Seamless RADIUS integration with MikroTik routers. Auto-configuration included.",
              },
              {
                icon: Users,
                title: "Free WiFi via Ads",
                description: "Offer sponsored free internet. Advertisers pay, users watch ads, you earn.",
              },
              {
                icon: BarChart3,
                title: "Real-Time Analytics",
                description: "Track sessions, revenue, and user engagement. Make data-driven decisions.",
              },
              {
                icon: Shield,
                title: "Secure Payments",
                description: "M-Pesa STK Push integration. Instant confirmation and session activation.",
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="border border-neutral-800 rounded-xl p-6 card-hover"
                style={{ backgroundColor: '#121212' }}
                data-testid={`feature-card-${index}`}
              >
                <div className="w-12 h-12 bg-blue-600/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-blue-500" strokeWidth={1.5} />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-neutral-400 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold mb-6">
                Simple Setup,
                <br />
                <span className="gradient-text">Powerful Results</span>
              </h2>
              
              <div className="space-y-8">
                {[
                  {
                    step: "01",
                    title: "Connect Your Router",
                    description: "Configure your MikroTik router with our auto-generated settings. Takes just 5 minutes.",
                  },
                  {
                    step: "02",
                    title: "Select Your Packages",
                    description: "Choose from pre-configured pricing tiers. No complicated setup needed.",
                  },
                  {
                    step: "03",
                    title: "Start Earning",
                    description: "Users connect, pay via M-Pesa, and you earn 70% of every transaction.",
                  },
                ].map((item, index) => (
                  <div key={index} className="flex gap-6">
                    <div className="flex-shrink-0 w-12 h-12 bg-blue-600/10 border border-blue-600/30 rounded-lg flex items-center justify-center">
                      <span className="text-blue-500 font-mono font-bold">{item.step}</span>
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{item.title}</h3>
                      <p className="text-neutral-400 text-sm">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <img
                src="https://images.unsplash.com/photo-1615847014013-0dfa967ba04f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHw0fHxsYXB0b3AlMjBjb2ZmZWUlMjBzaG9wfGVufDB8fHx8MTc2OTk4NDk0N3ww&ixlib=rb-4.1.0&q=85&w=600"
                alt="Business Owner"
                className="rounded-xl border border-neutral-800"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Hotspot Owner Pricing */}
      <section id="pricing" className="py-24 px-6 lg:px-12" style={{ backgroundColor: '#0a0a0a' }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-600/10 border border-green-600/20 rounded-full text-green-400 text-sm mb-6">
              <Wifi className="w-4 h-4" strokeWidth={1.5} />
              Hotspot Owner Plans
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Simple, Transparent
              <br />
              <span className="gradient-text">Pricing</span>
            </h2>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              Start earning from your WiFi hotspot today. 14-day free trial included.
            </p>
          </div>

          <div className="max-w-lg mx-auto">
            <div className="dashboard-card border-2 border-blue-500/30 relative overflow-hidden">
              <div className="absolute top-0 right-0 px-4 py-2 bg-blue-600 text-sm font-medium">
                14-Day Free Trial
              </div>
              
              <div className="text-center pt-8">
                <h3 className="text-xl font-semibold mb-2">Hotspot Subscription</h3>
                <div className="flex items-baseline justify-center gap-2 mb-2">
                  <span className="text-5xl font-bold text-blue-400">KES 500</span>
                  <span className="text-neutral-400">/month</span>
                </div>
                <p className="text-neutral-500 text-sm mb-6">per hotspot</p>
                
                <div className="space-y-3 text-left mb-8">
                  {[
                    "Full dashboard access",
                    "Ad revenue sharing",
                    "Real-time analytics",
                    "MikroTik integration",
                    "M-Pesa payment collection",
                    "Customer voucher system",
                    "Priority support"
                  ].map((feature, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center">
                        <Check className="w-3 h-3 text-green-400" />
                      </div>
                      <span className="text-neutral-300">{feature}</span>
                    </div>
                  ))}
                </div>
                
                <Link
                  to="/login"
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors block text-center"
                  data-testid="start-trial-btn"
                >
                  Start 14-Day Free Trial
                </Link>
                <p className="text-neutral-500 text-xs mt-3">No credit card required</p>
              </div>
            </div>
          </div>
          
          {/* WiFi Packages Info */}
          <div className="mt-16 text-center">
            <h3 className="text-xl font-semibold mb-4">WiFi Packages for End Users</h3>
            <p className="text-neutral-400 mb-8">Pre-configured pricing tiers from KES 5 to KES 600</p>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              {[
                { price: 5, duration: "30 min" },
                { price: 15, duration: "4 hours" },
                { price: 25, duration: "8 hours" },
                { price: 30, duration: "12 hours" },
                { price: 35, duration: "24 hours" },
                { price: 200, duration: "1 week" },
                { price: 600, duration: "1 month" },
              ].map((pkg, index) => (
                <div
                  key={index}
                  className="package-card"
                  data-testid={`package-${pkg.price}`}
                >
                  <div className="text-center">
                    <div className="text-xl font-bold mb-1">KES {pkg.price}</div>
                    <div className="text-neutral-400 text-xs">{pkg.duration}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CAIWAVE TV Section */}
      <section id="caiwave-tv" className="py-24 px-6 lg:px-12" style={{ background: 'linear-gradient(180deg, rgba(0,50,250,0.05) 0%, transparent 100%)' }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600/10 border border-blue-600/20 rounded-full text-blue-400 text-sm mb-6">
              <Tv className="w-4 h-4" strokeWidth={1.5} />
              Premium Live Access
            </div>
            
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              CAIWAVE TV
            </h2>
            <p className="text-neutral-400 max-w-2xl mx-auto">
              A premium live access service powered by CAIWAVE WiFi. Stream live events, political broadcasts, 
              church services, and more directly through WiFi hotspots.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {[
              {
                icon: Play,
                title: "Live Events",
                description: "Stream live football matches, concerts, community events directly to WiFi users",
              },
              {
                icon: Target,
                title: "Targeted Access",
                description: "Control which regions and hotspots can access specific streams",
              },
              {
                icon: Zap,
                title: "Subsidized Access",
                description: "Offer discounted rates for event streaming - KES 15 for 25 hours",
              },
            ].map((item, index) => (
              <div key={index} className="dashboard-card text-center">
                <div className="w-12 h-12 bg-blue-600/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <item.icon className="w-6 h-6 text-blue-400" strokeWidth={1.5} />
                </div>
                <h3 className="font-semibold mb-2">{item.title}</h3>
                <p className="text-neutral-400 text-sm">{item.description}</p>
              </div>
            ))}
          </div>

          <div className="dashboard-card bg-gradient-to-r from-blue-600/10 to-purple-600/10 border-blue-600/20">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div>
                <h3 className="text-xl font-semibold mb-2">Want to broadcast your event?</h3>
                <p className="text-neutral-400">
                  Political campaigns, church services, community announcements - reach thousands of WiFi users.
                </p>
              </div>
              <Button
                onClick={() => navigate("/register")}
                className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
              >
                Contact CAIWAVE
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Advertisers Section */}
      <section id="advertisers" className="py-24 px-6 lg:px-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="order-2 lg:order-1">
              <img
                src="https://images.unsplash.com/photo-1758691736975-9f7f643d178e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHwzfHxkaXZlcnNlJTIwYnVzaW5lc3MlMjB0ZWFtJTIwbWVldGluZ3xlbnwwfHx8fDE3Njk5ODQ5Mzd8MA&ixlib=rb-4.1.0&q=85&w=600"
                alt="Business Team"
                className="rounded-xl border border-neutral-800"
              />
            </div>
            
            <div className="order-1 lg:order-2">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600/10 border border-purple-600/20 rounded-full text-purple-400 text-sm mb-6">
                <Target className="w-4 h-4" strokeWidth={1.5} />
                For Advertisers & Campaigns
              </div>
              
              <h2 className="text-3xl sm:text-4xl font-bold mb-6">
                Reach Your Audience
                <br />
                <span className="text-purple-400">Where They Connect</span>
              </h2>
              
              <p className="text-neutral-400 mb-8 leading-relaxed">
                Target users by location with precision. Perfect for local businesses, political campaigns, 
                and brands wanting hyper-local reach. Your ad displays when users connect to WiFi.
              </p>
              
              <ul className="space-y-4 mb-8">
                {[
                  "Target by county, constituency, or ward",
                  "Image, video, and text ad formats",
                  "Real-time impression tracking",
                  "Sponsor free WiFi for brand awareness",
                ].map((item, index) => (
                  <li key={index} className="flex items-center gap-3 text-neutral-300">
                    <div className="w-5 h-5 bg-purple-600/20 rounded-full flex items-center justify-center">
                      <ChevronRight className="w-3 h-3 text-purple-400" strokeWidth={2} />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
              
              <Button
                onClick={() => navigate("/register")}
                className="bg-purple-600 hover:bg-purple-700 text-white"
                data-testid="advertiser-cta"
              >
                Start Advertising
                <ChevronRight className="w-5 h-5 ml-2" strokeWidth={1.5} />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 lg:px-12" style={{ backgroundColor: '#0a0a0a' }}>
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Transform Your
            <br />
            <span className="gradient-text">Hotspot Business?</span>
          </h2>
          <p className="text-neutral-400 mb-8 max-w-xl mx-auto">
            Join hundreds of hotspot owners earning from their WiFi networks. 
            No monthly fees, no complicated setup.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button
              onClick={handleGetStarted}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white btn-glow px-8"
              data-testid="cta-btn"
            >
              Get Started Free
              <ChevronRight className="w-5 h-5 ml-2" strokeWidth={1.5} />
            </Button>
            <Link to="/portal/demo">
              <Button size="lg" variant="outline" className="border-neutral-700 text-neutral-300 hover:bg-neutral-800">
                Try Demo Portal
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 lg:px-12 border-t border-neutral-800" style={{ backgroundColor: '#0a0a0a' }}>
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <CaiwaveLogo size={32} />
                <span className="font-semibold text-lg">CAIWAVE</span>
              </div>
              <p className="text-neutral-500 text-sm">
                The complete WiFi hotspot billing, advertising, and premium live access platform.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Platform</h4>
              <ul className="space-y-2 text-neutral-400 text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-neutral-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Support</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-neutral-400 text-sm">
                <li><a href="tel:0738570630" className="hover:text-white transition-colors">Contact Support</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors">FAQ</a></li>
              </ul>
            </div>
          </div>
          
          <div className="mt-12 pt-8 border-t border-neutral-800 text-center">
            <p className="text-neutral-500 text-sm">
              Powered by <span className="text-blue-400 font-medium">CAIWAVE WiFi</span> © 2026. All Rights Reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
