import { useEffect, useState } from "react";
import axios from "axios";

import { API_URL } from "../lib/utils";
import { safeError } from "../utils/safeError";

const fieldClassName =
  "w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md disabled:opacity-50";

const HotspotLocationFields = ({
  value,
  onChange,
  showWard = true,
  inputComponent: InputComponent = null,
}) => {
  const [counties, setCounties] = useState([]);
  const [constituencies, setConstituencies] = useState([]);
  const [loadingCounties, setLoadingCounties] = useState(true);
  const [loadingConstituencies, setLoadingConstituencies] = useState(false);
  const [error, setError] = useState("");

  const updateField = (field, fieldValue) => {
    onChange({
      ...value,
      [field]: fieldValue,
    });
  };

  useEffect(() => {
    let cancelled = false;

    const loadCounties = async () => {
      try {
        setLoadingCounties(true);
        setError("");

        const response = await axios.get(`${API_URL}/locations/counties`);

        if (!cancelled) {
          setCounties(response.data?.counties || []);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(safeError(requestError));
        }
      } finally {
        if (!cancelled) {
          setLoadingCounties(false);
        }
      }
    };

    loadCounties();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadConstituencies = async () => {
      if (!value.county) {
        setConstituencies([]);
        return;
      }

      try {
        setLoadingConstituencies(true);
        setError("");

        const response = await axios.get(
          `${API_URL}/locations/constituencies`,
          {
            params: { county: value.county },
          }
        );

        if (!cancelled) {
          setConstituencies(response.data?.constituencies || []);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(safeError(requestError));
        }
      } finally {
        if (!cancelled) {
          setLoadingConstituencies(false);
        }
      }
    };

    loadConstituencies();

    return () => {
      cancelled = true;
    };
  }, [value.county]);

  const handleCountyChange = (event) => {
    onChange({
      ...value,
      county: event.target.value,
      constituency: "",
    });
  };

  const renderTextInput = ({
    field,
    placeholder,
    required = false,
  }) => {
    if (InputComponent) {
      return (
        <InputComponent
          value={value[field] || ""}
          onChange={(event) => updateField(field, event.target.value)}
          placeholder={placeholder}
          required={required}
        />
      );
    }

    return (
      <input
        type="text"
        value={value[field] || ""}
        onChange={(event) => updateField(field, event.target.value)}
        className={fieldClassName}
        placeholder={placeholder}
        required={required}
      />
    );
  };

  return (
    <>
      <div>
        <label className="block text-sm font-medium mb-1">
          Country *
        </label>

        <select
          value={value.country_code || "KE"}
          onChange={() => {}}
          className={fieldClassName}
          required
          disabled
        >
          <option value="KE">Kenya</option>
        </select>

        <p className="mt-1 text-xs text-neutral-500">
          More East African countries will be added later.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">
          County *
        </label>

        <select
          value={value.county || ""}
          onChange={handleCountyChange}
          className={fieldClassName}
          required
          disabled={loadingCounties}
          data-testid="hotspot-county-select"
        >
          <option value="">
            {loadingCounties ? "Loading counties…" : "Select county"}
          </option>

          {counties.map((county) => (
            <option key={county} value={county}>
              {county}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">
          Constituency *
        </label>

        <select
          value={value.constituency || ""}
          onChange={(event) =>
            updateField("constituency", event.target.value)
          }
          className={fieldClassName}
          required
          disabled={!value.county || loadingConstituencies}
          data-testid="hotspot-constituency-select"
        >
          <option value="">
            {!value.county
              ? "Select county first"
              : loadingConstituencies
                ? "Loading constituencies…"
                : "Select constituency"}
          </option>

          {constituencies.map((constituency) => (
            <option key={constituency} value={constituency}>
              {constituency}
            </option>
          ))}
        </select>
      </div>

      {showWard && (
        <div>
          <label className="block text-sm font-medium mb-1">
            Ward
          </label>

          {renderTextInput({
            field: "ward",
            placeholder: "Optional ward",
          })}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">
          Location Name *
        </label>

        {renderTextInput({
          field: "location_name",
          placeholder: "e.g., Tononoka Grounds",
          required: true,
        })}
      </div>

      {error && (
        <p className="text-sm text-red-400 md:col-span-2">
          Could not load location options: {error}
        </p>
      )}
    </>
  );
};

export default HotspotLocationFields;
