import { Button } from "../components/ui/button";
import {
  CheckCircle,
  Server,
  Wifi,
  Shield,
  ArrowRight,
  Download,
  Router,
} from "lucide-react";

const SetupWizard = () => {
  return (
    <div className="min-h-screen bg-neutral-950 text-white p-6">
      <div className="max-w-5xl mx-auto py-12">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold mb-3">CAIWAVE Platform Setup</h1>
          <p className="text-neutral-400 text-lg">
            One-time platform readiness guide. Router provisioning now happens through the dashboard using generated .rsc files.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
            <Server className="w-8 h-8 text-blue-400 mb-4" />
            <h2 className="text-xl font-semibold mb-2">1. Platform Online</h2>
            <p className="text-neutral-400 text-sm">
              Confirm the CAIWAVE API, domain, SSL, database, and backend services are running.
            </p>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
            <Shield className="w-8 h-8 text-green-400 mb-4" />
            <h2 className="text-xl font-semibold mb-2">2. RADIUS Ready</h2>
            <p className="text-neutral-400 text-sm">
              Confirm RADIUS infrastructure is reachable by MikroTik routers and connected to CAIWAVE.
            </p>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
            <Wifi className="w-8 h-8 text-purple-400 mb-4" />
            <h2 className="text-xl font-semibold mb-2">3. Provision Routers</h2>
            <p className="text-neutral-400 text-sm">
              Use Owner or Admin Dashboard to generate a hotspot-bound MikroTik .rsc provisioning file.
            </p>
          </div>
        </div>

        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 mb-8">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-6 h-6 text-blue-400 mt-1" />
            <div>
              <h3 className="font-semibold text-blue-300 mb-2">New provisioning flow</h3>
              <p className="text-neutral-300 text-sm">
                This wizard no longer generates legacy copy-paste MikroTik scripts. The correct production flow is:
              </p>
              <div className="mt-4 grid md:grid-cols-4 gap-3 text-sm">
                <div className="bg-neutral-950/60 rounded-lg p-3">Create hotspot</div>
                <div className="bg-neutral-950/60 rounded-lg p-3">Generate .rsc</div>
                <div className="bg-neutral-950/60 rounded-lg p-3">Upload/import to MikroTik</div>
                <div className="bg-neutral-950/60 rounded-lg p-3">Confirm connection</div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Router className="w-5 h-5 text-green-400" />
            Continue to Router Provisioning
          </h2>

          <p className="text-neutral-400 mb-6">
            Generate router-specific provisioning files from the dashboard. Each .rsc file is bound to a hotspot, NAS identifier, and RADIUS secret.
          </p>

          <div className="flex flex-wrap gap-3">
            <Button onClick={() => (window.location.href = "/owner/mikrotik")} className="bg-blue-600 hover:bg-blue-700">
              Owner MikroTik Setup
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>

            <Button onClick={() => (window.location.href = "/admin/hotspots")} variant="outline" className="border-neutral-700">
              Admin Hotspots
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>

            <Button onClick={() => (window.location.href = "/")} variant="outline" className="border-neutral-700">
              Back Home
            </Button>
          </div>
        </div>

        <div className="mt-8 text-center text-xs text-neutral-600">
          Legacy FreeRADIUS and MikroTik script generators have been disabled to prevent configuration conflicts.
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
