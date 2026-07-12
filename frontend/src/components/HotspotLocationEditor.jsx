import { useEffect, useState } from "react";
import axios from "axios";
import { X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "./ui/button";
import { API_URL } from "../lib/utils";
import { getAuthToken } from "../lib/auth";
import { safeError } from "../utils/safeError";
import HotspotLocationFields from "./HotspotLocationFields";

const buildInitialLocation = (hotspot) => ({
  country_code: hotspot?.country_code || "KE",
  country_name: hotspot?.country_name || "Kenya",
  county: hotspot?.county || "",
  constituency: hotspot?.constituency || "",
  ward: hotspot?.ward || "",
  location_name: hotspot?.location_name || "",
  latitude: hotspot?.latitude ?? null,
  longitude: hotspot?.longitude ?? null,
});

const HotspotLocationEditor = ({
  hotspot,
  onClose,
  onSaved,
  inputComponent = null,
}) => {
  const [formData, setFormData] = useState(
    buildInitialLocation(hotspot)
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setFormData(buildInitialLocation(hotspot));
  }, [hotspot]);

  if (!hotspot) {
    return null;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);

    try {
      const response = await axios.put(
        `${API_URL}/hotspots/${hotspot.id}/location`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );

      toast.success("Hotspot location updated.");

      if (onSaved) {
        await onSaved(response.data);
      }

      onClose();
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-neutral-800 bg-neutral-950 p-6">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">
              Edit Hotspot Location
            </h2>

            <p className="mt-1 text-sm text-neutral-400">
              {hotspot.name}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="text-neutral-400 hover:text-white"
            aria-label="Close location editor"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <HotspotLocationFields
              value={formData}
              onChange={setFormData}
              inputComponent={inputComponent}
            />
          </div>

          <div className="flex justify-end gap-3 border-t border-neutral-800 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </Button>

            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save Location"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default HotspotLocationEditor;
