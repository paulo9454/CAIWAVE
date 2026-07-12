import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import { API_URL } from "../lib/utils";
import { getAuthToken } from "../lib/auth";
import { safeError } from "../utils/safeError";

const fieldClassName =
  "w-full bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2 disabled:opacity-50";

const scopeOptions = [
  {
    value: "national",
    label: "National",
    description: "All CAIWAVE hotspots in Kenya",
  },
  {
    value: "county",
    label: "County",
    description: "One or more selected counties",
  },
  {
    value: "constituency",
    label: "Constituency",
    description: "One or more selected constituencies",
  },
  {
    value: "hotspot",
    label: "Specific Hotspots",
    description: "Only selected hotspot locations",
  },
];

const toggleValue = (values, selectedValue) =>
  values.includes(selectedValue)
    ? values.filter((value) => value !== selectedValue)
    : [...values, selectedValue];

const CampaignTargetSelector = ({ value, onChange }) => {
  const [counties, setCounties] = useState([]);
  const [constituenciesByCounty, setConstituenciesByCounty] = useState({});
  const [hotspots, setHotspots] = useState([]);
  const [selectedCountyForConstituencies, setSelectedCountyForConstituencies] =
    useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadOptions = async () => {
      try {
        setLoading(true);
        setError("");

        const headers = {
          Authorization: `Bearer ${getAuthToken()}`,
        };

        const [countiesResponse, hotspotsResponse] = await Promise.all([
          axios.get(`${API_URL}/locations/counties`),
          axios.get(`${API_URL}/hotspots/`, { headers }),
        ]);

        const loadedCounties = countiesResponse.data?.counties || [];

        const constituencyResponses = await Promise.all(
          loadedCounties.map(async (county) => {
            const response = await axios.get(
              `${API_URL}/locations/constituencies`,
              { params: { county } }
            );

            return [
              county,
              response.data?.constituencies || [],
            ];
          })
        );

        if (!cancelled) {
          setCounties(loadedCounties);
          setConstituenciesByCounty(
            Object.fromEntries(constituencyResponses)
          );
          setHotspots(
            Array.isArray(hotspotsResponse.data)
              ? hotspotsResponse.data
              : []
          );
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

    loadOptions();

    return () => {
      cancelled = true;
    };
  }, []);

  const selectedScope = value.coverage_scope || "national";

  const constituencyCountyOptions = useMemo(
    () => constituenciesByCounty[selectedCountyForConstituencies] || [],
    [constituenciesByCounty, selectedCountyForConstituencies]
  );

  const handleScopeChange = (coverageScope) => {
    onChange({
      ...value,
      coverage_scope: coverageScope,
      country_code: "KE",
      country_name: "Kenya",
      target_counties: [],
      target_constituencies: [],
      target_hotspot_ids: [],
      target_regions: [],
    });

    setSelectedCountyForConstituencies("");
  };

  return (
    <div className="space-y-4 rounded-lg border border-neutral-800 p-4">
      <div>
        <h3 className="font-medium">Campaign Coverage</h3>
        <p className="mt-1 text-sm text-neutral-400">
          Choose exactly where this campaign should appear.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {scopeOptions.map((scope) => (
          <button
            key={scope.value}
            type="button"
            onClick={() => handleScopeChange(scope.value)}
            className={`rounded-lg border p-3 text-left transition-colors ${
              selectedScope === scope.value
                ? "border-blue-500 bg-blue-500/10"
                : "border-neutral-800 bg-neutral-900 hover:border-neutral-700"
            }`}
          >
            <div className="font-medium">{scope.label}</div>
            <div className="mt-1 text-xs text-neutral-400">
              {scope.description}
            </div>
          </button>
        ))}
      </div>

      <div>
        <label className="mb-1 block text-sm text-neutral-400">
          Country
        </label>
        <select
          value="KE"
          disabled
          className={fieldClassName}
        >
          <option value="KE">Kenya</option>
        </select>
      </div>

      {selectedScope === "national" && (
        <div className="rounded-lg border border-green-700/40 bg-green-500/10 p-3 text-sm text-green-300">
          This campaign will be eligible at all configured CAIWAVE hotspots in Kenya.
        </div>
      )}

      {selectedScope === "county" && (
        <div>
          <label className="mb-2 block text-sm text-neutral-400">
            Select Counties *
          </label>

          <div className="grid max-h-64 gap-2 overflow-y-auto md:grid-cols-2">
            {counties.map((county) => (
              <label
                key={county}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-neutral-800 bg-neutral-900 p-3"
              >
                <input
                  type="checkbox"
                  checked={(value.target_counties || []).includes(county)}
                  onChange={() =>
                    onChange({
                      ...value,
                      target_counties: toggleValue(
                        value.target_counties || [],
                        county
                      ),
                    })
                  }
                />
                <span>{county}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {selectedScope === "constituency" && (
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm text-neutral-400">
              Choose County to View Constituencies
            </label>

            <select
              value={selectedCountyForConstituencies}
              onChange={(event) =>
                setSelectedCountyForConstituencies(event.target.value)
              }
              className={fieldClassName}
              disabled={loading}
            >
              <option value="">Select county</option>
              {counties.map((county) => (
                <option key={county} value={county}>
                  {county}
                </option>
              ))}
            </select>
          </div>

          {selectedCountyForConstituencies && (
            <div>
              <label className="mb-2 block text-sm text-neutral-400">
                Select Constituencies *
              </label>

              <div className="grid max-h-64 gap-2 overflow-y-auto md:grid-cols-2">
                {constituencyCountyOptions.map((constituency) => (
                  <label
                    key={constituency}
                    className="flex cursor-pointer items-center gap-3 rounded-lg border border-neutral-800 bg-neutral-900 p-3"
                  >
                    <input
                      type="checkbox"
                      checked={(value.target_constituencies || []).includes(
                        constituency
                      )}
                      onChange={() =>
                        onChange({
                          ...value,
                          target_constituencies: toggleValue(
                            value.target_constituencies || [],
                            constituency
                          ),
                        })
                      }
                    />
                    <span>{constituency}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {(value.target_constituencies || []).length > 0 && (
            <p className="text-sm text-blue-400">
              {value.target_constituencies.length} constituency target(s) selected
            </p>
          )}
        </div>
      )}

      {selectedScope === "hotspot" && (
        <div>
          <label className="mb-2 block text-sm text-neutral-400">
            Select Hotspots *
          </label>

          <div className="grid max-h-72 gap-2 overflow-y-auto">
            {hotspots.map((hotspot) => (
              <label
                key={hotspot.id}
                className="flex cursor-pointer items-start gap-3 rounded-lg border border-neutral-800 bg-neutral-900 p-3"
              >
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={(value.target_hotspot_ids || []).includes(
                    hotspot.id
                  )}
                  onChange={() =>
                    onChange({
                      ...value,
                      target_hotspot_ids: toggleValue(
                        value.target_hotspot_ids || [],
                        hotspot.id
                      ),
                    })
                  }
                />

                <div>
                  <div className="font-medium">{hotspot.name}</div>
                  <div className="mt-1 text-xs text-neutral-400">
                    {hotspot.location_name || "Unnamed location"}
                    {hotspot.constituency
                      ? ` · ${hotspot.constituency}`
                      : ""}
                    {hotspot.county ? ` · ${hotspot.county}` : ""}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400">
          Could not load targeting options: {error}
        </p>
      )}
    </div>
  );
};

export default CampaignTargetSelector;
