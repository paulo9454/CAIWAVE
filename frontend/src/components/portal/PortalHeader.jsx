import { ShieldCheck, Wifi, Zap } from "lucide-react";

const getGreeting = () => {
  const hour = new Date().getHours();

  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
};

export default function PortalHeader({ hotspot }) {
  const hotspotName = hotspot?.name || "CAIWAVE WiFi";

  return (
    <header className="relative overflow-hidden border-b border-white/10 bg-gradient-to-br from-sky-600 via-blue-700 to-indigo-950 text-white">
      <div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-cyan-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-28 -left-24 h-64 w-64 rounded-full bg-indigo-400/20 blur-3xl" />

      <div className="relative mx-auto max-w-4xl px-4 pb-7 pt-5 sm:px-6 sm:pb-8">
        <div className="flex items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/30 bg-white text-blue-700 shadow-lg shadow-blue-950/20">
              <Wifi className="h-6 w-6" />
            </div>

            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-100">
                CAIWAVE
              </p>

              <h1 className="truncate text-xl font-extrabold tracking-tight sm:text-2xl">
                Fast internet. More possibilities.
              </h1>
            </div>
          </div>

          <span className="hidden shrink-0 rounded-full border border-emerald-200/30 bg-emerald-400/15 px-3 py-1.5 text-xs font-semibold text-emerald-100 sm:inline-flex">
            Network available
          </span>
        </div>

        <div className="mt-6">
          <p className="text-sm font-medium text-blue-100">
            {getGreeting()} 👋
          </p>

          <p className="mt-1 text-sm text-white/75">
            You are connecting through
          </p>

          <h2 className="mt-1 truncate text-2xl font-bold tracking-tight sm:text-3xl">
            {hotspotName}
          </h2>
        </div>

        <div className="mt-6 grid grid-cols-3 gap-2 sm:gap-3">
          <div className="rounded-2xl border border-white/15 bg-white/10 px-2 py-3 text-center backdrop-blur-sm">
            <Wifi className="mx-auto h-5 w-5 text-cyan-200" />
            <p className="mt-1.5 text-xs font-semibold">Fast WiFi</p>
          </div>

          <div className="rounded-2xl border border-white/15 bg-white/10 px-2 py-3 text-center backdrop-blur-sm">
            <ShieldCheck className="mx-auto h-5 w-5 text-emerald-200" />
            <p className="mt-1.5 text-xs font-semibold">Secure access</p>
          </div>

          <div className="rounded-2xl border border-white/15 bg-white/10 px-2 py-3 text-center backdrop-blur-sm">
            <Zap className="mx-auto h-5 w-5 text-yellow-200" />
            <p className="mt-1.5 text-xs font-semibold">Instant setup</p>
          </div>
        </div>
      </div>
    </header>
  );
}
