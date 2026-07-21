import { Play } from "lucide-react";

const TVPanel = ({ streams }) => {
  if (!streams.length) return null;

  return (
    <div
      id="tv"
      className="scroll-mt-5 rounded-[1.75rem] border border-white/10 bg-neutral-900/90 p-4 shadow-xl shadow-black/20 sm:p-5"
    >
      <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
        <Play className="h-5 w-5 text-red-500" />
        CAIWAVE TV - Live Now
      </h2>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {streams.slice(0, 3).map((stream) => (
          <div
            key={stream.id}
            className="relative overflow-hidden rounded-lg bg-neutral-800"
          >
            {stream.thumbnail_url ? (
              <img
                src={stream.thumbnail_url}
                alt={stream.name}
                className="aspect-video w-full object-cover"
              />
            ) : (
              <div className="flex aspect-video w-full items-center justify-center bg-gradient-to-br from-red-900 to-purple-900">
                <Play className="h-8 w-8" />
              </div>
            )}

            <div className="absolute left-2 top-2 rounded bg-red-600 px-2 py-0.5 text-xs font-bold text-white">
              LIVE
            </div>

            <div className="p-2">
              <div className="truncate text-sm font-medium">{stream.name}</div>

              <div
                className={`mt-1 text-xs font-semibold ${
                  stream.access_type === "free"
                    ? "text-green-400"
                    : "text-yellow-400"
                }`}
              >
                {stream.access_type === "free"
                  ? "Free to watch"
                  : `KES ${stream.price || 0} access`}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-sm">
        {streams.some((stream) => stream.access_type === "free") && (
          <span className="rounded-full border border-green-500/30 bg-green-500/10 px-3 py-1 font-medium text-green-300">
            Free streams are free to watch
          </span>
        )}

        {streams.some((stream) => stream.access_type === "paid") && (
          <span className="rounded-full border border-yellow-500/30 bg-yellow-500/10 px-3 py-1 font-medium text-yellow-300">
            Paid streams show their access price
          </span>
        )}
      </div>
    </div>
  );
};

export default TVPanel;
