import { ShoppingBag, Tv, Wifi } from "lucide-react";

const actions = [
  {
    id: "packages",
    icon: Wifi,
    title: "Connect",
    subtitle: "Buy WiFi",
  },
  {
    id: "tv",
    icon: Tv,
    title: "CAIWAVE TV",
    subtitle: "Live events",
  },
  {
    id: "marketplace",
    icon: ShoppingBag,
    title: "Marketplace",
    subtitle: "Explore",
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
        {actions.map(({ id, icon: Icon, title, subtitle }) => (
          <button
            key={id}
            type="button"
            onClick={() => scrollTo(id)}
            className="group min-w-0 rounded-2xl border border-white/10 bg-neutral-900/95 px-2 py-4 text-center shadow-xl backdrop-blur transition duration-200 hover:-translate-y-1 hover:border-blue-500/50 hover:bg-neutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 sm:px-4"
          >
            <Icon
              aria-hidden="true"
              className="mx-auto h-6 w-6 text-sky-400 transition-transform duration-200 group-hover:scale-110 sm:h-7 sm:w-7"
            />

            <span className="mt-2 block truncate text-xs font-semibold text-white sm:text-sm">
              {title}
            </span>

            <span className="mt-0.5 block truncate text-[10px] text-neutral-400 sm:text-xs">
              {subtitle}
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
