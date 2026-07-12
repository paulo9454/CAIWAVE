import { AlertTriangle, MapPin } from "lucide-react";

const HotspotLocationSummary = ({ hotspot }) => {
  const complete = Boolean(
    hotspot?.county &&
    hotspot?.constituency &&
    hotspot?.location_name
  );

  if (!complete) {
    return (
      <div className="flex items-center gap-2 text-sm text-amber-400">
        <AlertTriangle className="h-4 w-4" />
        <span>Location incomplete</span>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 font-medium">
        <MapPin className="h-4 w-4 text-blue-400" />
        <span>{hotspot.location_name}</span>
      </div>

      <p className="mt-1 text-xs text-neutral-400">
        {hotspot.constituency} · {hotspot.county}
      </p>
    </div>
  );
};

export default HotspotLocationSummary;
