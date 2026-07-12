import { useEffect, useState } from "react";
import axios from "axios";

import { API_URL } from "../lib/utils";
import { getAuthToken } from "../lib/auth";
import { safeError } from "../utils/safeError";

const toggleValue = (values, selectedValue) =>
  values.includes(selectedValue)
    ? values.filter((value) => value !== selectedValue)
    : [...values, selectedValue];

const CampaignAdSelector = ({ value, onChange }) => {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadEligibleAds = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await axios.get(
          `${API_URL}/campaigns/eligible-ads`,
          {
            headers: {
              Authorization: `Bearer ${getAuthToken()}`,
            },
          }
        );

        if (!cancelled) {
          setAds(Array.isArray(response.data) ? response.data : []);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(safeError(requestError));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadEligibleAds();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-3 rounded-lg border border-neutral-800 p-4">
      <div>
        <h3 className="font-medium">Advertisement Creatives *</h3>
        <p className="mt-1 text-sm text-neutral-400">
          Only paid, approved, active and unexpired advertisements are available.
        </p>
      </div>

      {loading ? (
        <p className="text-sm text-neutral-400">
          Loading eligible advertisements…
        </p>
      ) : ads.length === 0 ? (
        <div className="rounded-lg border border-amber-700/40 bg-amber-500/10 p-3 text-sm text-amber-300">
          No eligible advertisement is currently available. An advert must be approved and paid before it can be assigned.
        </div>
      ) : (
        <div className="grid max-h-80 gap-3 overflow-y-auto md:grid-cols-2">
          {ads.map((ad) => (
            <label
              key={ad.id}
              className="flex cursor-pointer items-start gap-3 rounded-lg border border-neutral-800 bg-neutral-900 p-3"
            >
              <input
                type="checkbox"
                className="mt-1"
                checked={(value || []).includes(ad.id)}
                onChange={() =>
                  onChange(toggleValue(value || [], ad.id))
                }
              />

              <div className="min-w-0">
                <div className="font-medium">{ad.title}</div>
                <div className="mt-1 text-xs text-neutral-400">
                  {ad.package_name || "Advertising package"}
                  {ad.ad_type ? ` · ${ad.ad_type}` : ""}
                </div>
                <div className="mt-1 text-xs text-green-400">
                  Active until{" "}
                  {ad.expires_at
                    ? new Date(ad.expires_at).toLocaleDateString()
                    : "unknown"}
                </div>
              </div>
            </label>
          ))}
        </div>
      )}

      {(value || []).length > 0 && (
        <p className="text-sm text-blue-400">
          {value.length} advertisement(s) selected
        </p>
      )}

      {error && (
        <p className="text-sm text-red-400">
          Could not load eligible advertisements: {error}
        </p>
      )}
    </div>
  );
};

export default CampaignAdSelector;
