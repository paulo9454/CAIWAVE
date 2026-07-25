import {
  BellRing,
  Gift,
  Headphones,
  ShoppingBag,
  Tv,
  Wifi,
} from "lucide-react";

const actions = [
  {
    id: "packages",
    icon: Wifi,
    title: "Buy WiFi",
    subtitle: "Choose a package",
    cardClass:
      "border-blue-400/20 bg-gradient-to-br from-blue-950/95 via-neutral-900 to-cyan-950/80 hover:border-blue-400/60 hover:shadow-blue-950/40",
    iconWrapClass:
      "bg-blue-400/15 text-blue-300 ring-blue-300/20",
  },
  {
    id: "free-wifi",
    icon: Gift,
    title: "Free WiFi",
    subtitle: "Watch an advert",
    cardClass:
      "border-emerald-400/20 bg-gradient-to-br from-emerald-950/95 via-neutral-900 to-green-950/80 hover:border-emerald-400/60 hover:shadow-emerald-950/40",
    iconWrapClass:
      "bg-emerald-400/15 text-emerald-300 ring-emerald-300/20",
  },
  {
    id: "notifications",
    icon: BellRing,
    title: "Notifications",
    subtitle: "Enable alerts",
    cardClass:
      "border-violet-400/20 bg-gradient-to-br from-violet-950/95 via-neutral-900 to-indigo-950/80 hover:border-violet-400/60 hover:shadow-violet-950/40",
    iconWrapClass:
      "bg-violet-400/15 text-violet-300 ring-violet-300/20",
  },
  {
    id: "tv",
    icon: Tv,
    title: "CAIWAVE TV",
    subtitle: "Watch live events",
    cardClass:
      "border-red-400/20 bg-gradient-to-br from-red-950/95 via-neutral-900 to-rose-950/80 hover:border-red-400/60 hover:shadow-red-950/40",
    iconWrapClass:
      "bg-red-400/15 text-red-300 ring-red-300/20",
  },
  {
    id: "marketplace",
    icon: ShoppingBag,
    title: "Marketplace",
    subtitle: "Explore offers",
    cardClass:
      "border-amber-400/20 bg-gradient-to-br from-amber-950/95 via-neutral-900 to-orange-950/80 hover:border-amber-400/60 hover:shadow-amber-950/40",
    iconWrapClass:
      "bg-amber-400/15 text-amber-300 ring-amber-300/20",
  },
  {
    id: "support",
    icon: Headphones,
    title: "Support",
    subtitle: "Get help",
    cardClass:
      "border-cyan-400/20 bg-gradient-to-br from-cyan-950/95 via-neutral-900 to-teal-950/80 hover:border-cyan-400/60 hover:shadow-cyan-950/40",
    iconWrapClass:
      "bg-cyan-400/15 text-cyan-300 ring-cyan-300/20",
  },
];

export default function QuickActions() {
  const scrollTo = (id) => {
    const element = document.getElementById(id);

    if (!element) {
      return;
    }

    element.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <section
      aria-label="Quick actions"
      className="relative z-20 mx-auto -mt-4 max-w-4xl px-4 sm:px-6"
    >
      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        {actions.map(
          ({
            id,
            icon: Icon,
            title,
            subtitle,
            cardClass,
            iconWrapClass,
          }) => (
            <button
              key={id}
              type="button"
              onClick={() => scrollTo(id)}
              className={`group min-w-0 overflow-hidden rounded-2xl border px-2 py-3.5 text-center shadow-xl backdrop-blur transition duration-200 hover:-translate-y-1 hover:shadow-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 sm:px-4 sm:py-4 ${cardClass}`}
            >
              <span
                className={`mx-auto flex h-10 w-10 items-center justify-center rounded-xl ring-1 transition duration-200 group-hover:scale-110 sm:h-11 sm:w-11 ${iconWrapClass}`}
              >
                <Icon
                  aria-hidden="true"
                  className="h-5 w-5 sm:h-6 sm:w-6"
                />
              </span>

              <span className="mt-2 block truncate text-xs font-bold text-white sm:text-sm">
                {title}
              </span>

              <span className="mt-0.5 block truncate text-[9px] text-neutral-400 sm:text-xs">
                {subtitle}
              </span>
            </button>
          )
        )}
      </div>
    </section>
  );
}
