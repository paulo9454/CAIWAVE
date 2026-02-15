import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { initializeAuth, getUser, isAuthenticated, ROLES } from "./lib/auth";
import "./App.css";

// Pages
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import CaptivePortal from "./pages/CaptivePortal";
import SetupWizard from "./pages/SetupWizard";

// Dashboards
import OwnerDashboard from "./pages/owner/Dashboard";
import AdminDashboard from "./pages/admin/Dashboard";
import AdvertiserDashboard from "./pages/advertiser/Dashboard";

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const user = getUser();
  
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

function App() {
  useEffect(() => {
    initializeAuth();
  }, []);

  return (
    <div className="min-h-screen bg-[#050505] text-white dark">
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/portal/:hotspotId" element={<CaptivePortal />} />
          <Route path="/setup" element={<SetupWizard />} />
          
          {/* Hotspot Owner Dashboard */}
          <Route
            path="/owner/*"
            element={
              <ProtectedRoute allowedRoles={[ROLES.HOTSPOT_OWNER, ROLES.SUPER_ADMIN]}>
                <OwnerDashboard />
              </ProtectedRoute>
            }
          />
          
          {/* Admin Dashboard */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          
          {/* Advertiser Dashboard */}
          <Route
            path="/advertiser/*"
            element={
              <ProtectedRoute allowedRoles={[ROLES.ADVERTISER, ROLES.SUPER_ADMIN]}>
                <AdvertiserDashboard />
              </ProtectedRoute>
            }
          />
          
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
