import { ShieldCheck, Wifi, Zap } from "lucide-react";

const SkeletonBlock = ({ className = "" }) => (
  <div
    aria-hidden="true"
    className={`animate-pulse rounded-2xl bg-white/[0.07] ${className}`}
  />
);

export default function PortalLoadingScreen() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#050914] text-white">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-14rem] h-[30rem] w-[30rem] -translate-x-1/2 rounded-full bg-blue-600/20 blur-[110px]" />
        <div className="absolute bottom-[-12rem] right-[-10rem] h-[26rem] w-[26rem] rounded-full bg-cyan-500/10 blur-[100px]" />
      </div>

      <div className="relative mx-auto min-h-screen max-w-4xl px-4 pb-10 pt-6 sm:px-6">
        <header className="overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-sky-600 via-blue-700 to-indigo-950 p-5 shadow-2xl shadow-blue-950/30 sm:p-7">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-blue-700 shadow-lg">
              <Wifi className="h-6 w-6" />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-100">
                CAIWAVE
              </p>

              <p className="mt-1 text-lg font-bold sm:text-xl">
                Preparing your WiFi experience
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-3 gap-2 sm:gap-3">
            {[
              [Wifi, "Fast WiFi"],
              [ShieldCheck, "Secure"],
              [Zap, "Instant"],
            ].map(([Icon, label]) => (
              <div
                key={label}
                className="rounded-2xl border border-white/15 bg-white/10 px-2 py-3 text-center backdrop-blur-sm"
              >
                <Icon className="mx-auto h-5 w-5 text-cyan-100" />
                <p className="mt-1.5 text-xs font-semibold">{label}</p>
              </div>
            ))}
          </div>
        </header>

        <main className="mt-5 space-y-5">
          <section className="rounded-[1.75rem] border border-white/10 bg-white/[0.035] p-4 shadow-xl shadow-black/20 sm:p-6">
            <SkeletonBlock className="h-4 w-28" />
            <SkeletonBlock className="mt-3 h-7 w-56 max-w-full" />

            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {[1, 2, 3].map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-white/10 bg-white/[0.025] p-4"
                >
                  <SkeletonBlock className="h-6 w-20" />
                  <SkeletonBlock className="mt-4 h-4 w-24" />
                  <SkeletonBlock className="mt-2 h-3 w-16" />
                </div>
              ))}
            </div>
          </section>

          <section className="overflow-hidden rounded-[1.75rem] border border-white/10 bg-white/[0.035] shadow-xl shadow-black/20">
            <SkeletonBlock className="aspect-video w-full rounded-none" />

            <div className="p-4 sm:p-5">
              <SkeletonBlock className="h-3 w-32" />
              <SkeletonBlock className="mt-3 h-6 w-52 max-w-full" />
              <SkeletonBlock className="mt-3 h-4 w-full" />
              <SkeletonBlock className="mt-2 h-4 w-3/4" />
            </div>
          </section>

          <p className="text-center text-sm text-slate-400">
            Loading packages, vouchers and available services…
          </p>
        </main>
      </div>
    </div>
  );
}
