import { useEffect, useRef } from "react";
import {
  Check,
  Clock,
  Gauge,
  LockKeyhole,
  Phone,
  Sparkles,
  Wifi,
  X,
  Zap,
} from "lucide-react";

import { Button } from "../ui/button";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "../ui/drawer";

const formatDuration = (minutes = 0) => {
  if (minutes < 60) return `${minutes} min`;

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  if (hours < 24) {
    return remainingMinutes
      ? `${hours}h ${remainingMinutes}m`
      : `${hours} hr`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;

  return remainingHours
    ? `${days}d ${remainingHours}h`
    : `${days} day${days === 1 ? "" : "s"}`;
};

const getPackageBadge = (pkg, index, total) => {
  if (pkg?.is_popular) return "Popular";
  if (pkg?.is_best_value) return "Best Value";
  if (total >= 3 && index === 1) return "Popular";
  if (total >= 4 && index === total - 1) return "Best Value";
  return null;
};

const PackagePurchasePanel = ({
  packages,
  selectedPackage,
  setSelectedPackage,
  phone,
  setPhone,
  email,
  setEmail,
  paying,
  handlePurchase,
  freeSession,
  paymentOpen,
  setPaymentOpen,
}) => {
  const phoneInputRef = useRef(null);

  useEffect(() => {
    if (!paymentOpen) return undefined;

    const timeout = window.setTimeout(() => {
      phoneInputRef.current?.focus();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [paymentOpen]);

  const selectPackage = (pkg) => {
    setSelectedPackage(pkg);
    setPaymentOpen(true);
  };

  return (
    <>
      <section className="overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-neutral-900 via-neutral-900 to-blue-950/40 shadow-2xl shadow-black/20">
        <div className="border-b border-white/10 px-4 py-5 sm:px-6">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-yellow-400/10 ring-1 ring-yellow-300/20">
              <Zap className="h-5 w-5 text-yellow-300" />
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-300">
                Fast checkout
              </p>

              <h2 className="mt-1 text-xl font-bold text-white">
                {freeSession
                  ? "Need more time? Upgrade"
                  : "Choose your WiFi package"}
              </h2>

              <p className="mt-1 text-sm text-neutral-400">
                Tap a package and enter your M-Pesa number in the popup.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3 sm:p-6">
          {packages.map((pkg, index) => {
            const isSelected = selectedPackage?.id === pkg.id;
            const badge = getPackageBadge(pkg, index, packages.length);

            return (
              <button
                key={pkg.id}
                type="button"
                onClick={() => selectPackage(pkg)}
                className={`group relative min-h-[154px] overflow-hidden rounded-2xl border p-4 text-left transition duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 ${
                  isSelected
                    ? "border-blue-400 bg-blue-500/15 shadow-lg shadow-blue-950/30"
                    : "border-white/10 bg-white/[0.04] hover:-translate-y-0.5 hover:border-white/20 hover:bg-white/[0.07]"
                }`}
              >
                {badge && (
                  <span className="absolute right-2 top-2 rounded-full bg-yellow-300 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-neutral-950">
                    {badge}
                  </span>
                )}

                {isSelected && (
                  <span className="absolute bottom-2 right-2 flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-white">
                    <Check className="h-4 w-4" />
                  </span>
                )}

                <div className="pr-12">
                  <p className="text-2xl font-black tracking-tight text-green-300">
                    KES {pkg.price}
                  </p>

                  <p className="mt-1 font-semibold text-white">
                    {pkg.name}
                  </p>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1 rounded-full bg-black/25 px-2.5 py-1 text-xs text-neutral-300">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDuration(pkg.duration_minutes)}
                  </span>

                  {pkg.speed_mbps && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-black/25 px-2.5 py-1 text-xs text-neutral-300">
                      <Gauge className="h-3.5 w-3.5" />
                      {pkg.speed_mbps} Mbps
                    </span>
                  )}
                </div>

                <p className="mt-4 text-xs font-medium text-blue-300">
                  Tap to continue
                </p>
              </button>
            );
          })}
        </div>
      </section>

      <Drawer
        open={paymentOpen}
        onOpenChange={(open) => {
          if (!paying) setPaymentOpen(open);
        }}
      >
        <DrawerContent className="border-white/10 bg-neutral-950 text-white">
          <div className="mx-auto max-h-[90vh] w-full max-w-lg overflow-y-auto pb-[max(0.5rem,env(safe-area-inset-bottom))]">
            <DrawerHeader className="relative border-b border-white/10 px-5 pb-5 pt-2 text-left">
              <DrawerClose asChild>
                <button
                  type="button"
                  disabled={paying}
                  aria-label="Close payment"
                  className="absolute right-4 top-1 flex h-9 w-9 items-center justify-center rounded-full bg-white/5 text-neutral-400 hover:bg-white/10 hover:text-white disabled:opacity-50"
                >
                  <X className="h-5 w-5" />
                </button>
              </DrawerClose>

              <div className="flex items-center gap-3 pr-12">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-500/15 ring-1 ring-blue-400/20">
                  <Wifi className="h-5 w-5 text-blue-300" />
                </div>

                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">
                    CAIWAVE WiFi
                  </p>

                  <DrawerTitle className="mt-1 text-xl text-white">
                    Complete your purchase
                  </DrawerTitle>
                </div>
              </div>

              <DrawerDescription className="mt-3 text-neutral-400">
                Confirm your package and enter the M-Pesa number that should
                receive the STK prompt.
              </DrawerDescription>
            </DrawerHeader>

            {selectedPackage && (
              <div className="space-y-5 px-5 py-5">
                <div className="rounded-2xl border border-blue-400/20 bg-gradient-to-br from-blue-500/15 to-emerald-500/10 p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm text-neutral-300">
                        Selected package
                      </p>

                      <h3 className="mt-1 text-xl font-bold text-white">
                        {selectedPackage.name}
                      </h3>
                    </div>

                    <p className="whitespace-nowrap text-2xl font-black text-green-300">
                      KES {selectedPackage.price}
                    </p>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-black/25 px-3 py-1.5 text-xs text-neutral-200">
                      <Clock className="h-3.5 w-3.5" />
                      {formatDuration(selectedPackage.duration_minutes)}
                    </span>

                    {selectedPackage.speed_mbps && (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-black/25 px-3 py-1.5 text-xs text-neutral-200">
                        <Gauge className="h-3.5 w-3.5" />
                        Up to {selectedPackage.speed_mbps} Mbps
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-neutral-300">
                  <p className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-yellow-300" />
                    Instant internet access after successful payment
                  </p>

                  <p className="flex items-center gap-2">
                    <LockKeyhole className="h-4 w-4 text-green-300" />
                    Secure M-Pesa payment
                  </p>

                  <p className="flex items-center gap-2">
                    <Wifi className="h-4 w-4 text-blue-300" />
                    Automatic WiFi connection after confirmation
                  </p>
                </div>

                <div>
                  <label
                    htmlFor="portal-mpesa-phone"
                    className="mb-2 block text-sm font-medium text-neutral-200"
                  >
                    M-Pesa phone number
                  </label>

                  <div className="flex items-center rounded-xl border border-white/10 bg-white/[0.05] focus-within:border-green-400/60 focus-within:ring-2 focus-within:ring-green-400/15">
                    <span className="border-r border-white/10 px-4 py-3.5 font-semibold text-neutral-300">
                      +254
                    </span>

                    <input
                      ref={phoneInputRef}
                      id="portal-mpesa-phone"
                      type="tel"
                      inputMode="numeric"
                      autoComplete="tel"
                      value={phone}
                      onChange={(event) =>
                        setPhone(
                          event.target.value
                            .replace(/\D/g, "")
                            .slice(0, 9)
                        )
                      }
                      className="min-w-0 flex-1 bg-transparent px-3 py-3.5 text-base text-white outline-none placeholder:text-neutral-600"
                      placeholder="7XXXXXXXX"
                    />
                  </div>

                  <p className="mt-2 text-xs text-neutral-500">
                    Use the Safaricom number that will approve the payment.
                  </p>
                </div>

                <div>
                  <label
                    htmlFor="portal-payment-email"
                    className="mb-2 block text-sm font-medium text-neutral-200"
                  >
                    Email{" "}
                    <span className="text-neutral-500">(optional)</span>
                  </label>

                  <input
                    id="portal-payment-email"
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 py-3.5 text-base text-white outline-none placeholder:text-neutral-600 focus:border-blue-400/60 focus:ring-2 focus:ring-blue-400/15"
                    placeholder="your@email.com"
                  />
                </div>
              </div>
            )}

            <DrawerFooter className="border-t border-white/10 px-5 pb-5 pt-4">
              <Button
                type="button"
                onClick={handlePurchase}
                disabled={paying || phone.length < 9}
                className="h-14 w-full rounded-xl bg-green-600 text-base font-bold text-white shadow-lg shadow-green-950/30 hover:bg-green-500 disabled:bg-neutral-800 disabled:text-neutral-500"
              >
                {paying ? (
                  <>
                    <span className="mr-3 h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Sending M-Pesa prompt...
                  </>
                ) : (
                  <>
                    <Phone className="mr-2 h-5 w-5" />
                    Pay KES {selectedPackage?.price ?? 0} via M-Pesa
                  </>
                )}
              </Button>

              <p className="flex items-center justify-center gap-1.5 text-center text-xs text-neutral-500">
                <LockKeyhole className="h-3.5 w-3.5" />
                Secure STK Push protected by Paystack
              </p>

              <DrawerClose asChild>
                <Button
                  type="button"
                  variant="ghost"
                  disabled={paying}
                  className="h-11 text-neutral-400 hover:bg-white/5 hover:text-white"
                >
                  Cancel
                </Button>
              </DrawerClose>
            </DrawerFooter>
          </div>
        </DrawerContent>
      </Drawer>
    </>
  );
};

export default PackagePurchasePanel;
