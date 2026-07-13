import { useEffect, useState } from "react";
import axios from "axios";
import {
  Ban,
  CheckCircle,
  Edit,
  Megaphone,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "./ui/button";
import { getAuthToken } from "../lib/auth";
import { API_URL, formatCurrency } from "../lib/utils";
import { safeError } from "../utils/safeError";

const EMPTY_FORM = {
  name: "",
  description: "",
  coverage_scope: "constituency",
  duration_days: 7,
  price: 5,
  max_impressions: 5000,
  status: "active",
};

const inputClassName =
  "w-full mt-1 px-3 py-2 bg-neutral-900 border border-neutral-700 rounded-md";

const AdminAdvertisingPackages = () => {
  const [packages, setPackages] = useState([]);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [editingPackage, setEditingPackage] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const authHeaders = () => ({
    Authorization: `Bearer ${getAuthToken()}`,
  });

  const fetchPackages = async () => {
    setLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/ad-packages/`,
        {
          params: {
            include_disabled: true,
          },
          headers: authHeaders(),
        }
      );

      setPackages(
        Array.isArray(response.data) ? response.data : []
      );
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, []);

  const openCreate = () => {
    setEditingPackage(null);
    setFormData({ ...EMPTY_FORM });
    setShowForm(true);
  };

  const openEdit = (pkg) => {
    setEditingPackage(pkg);

    setFormData({
      name: pkg.name || "",
      description: pkg.description || "",
      coverage_scope:
        pkg.coverage_scope || "constituency",
      duration_days: pkg.duration_days ?? 1,
      price: pkg.price ?? 1,
      max_impressions: pkg.max_impressions ?? "",
      status: pkg.status || "active",
    });

    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingPackage(null);
    setFormData({ ...EMPTY_FORM });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const payload = {
      name: formData.name.trim(),
      description: formData.description.trim(),
      coverage_scope: formData.coverage_scope,
      duration_days: Number(formData.duration_days),
      price: Number(formData.price),
      max_impressions:
        formData.max_impressions === ""
          ? null
          : Number(formData.max_impressions),
    };

    if (editingPackage) {
      payload.status = formData.status;
    }

    setSaving(true);

    try {
      if (editingPackage) {
        await axios.put(
          `${API_URL}/ad-packages/${editingPackage.id}`,
          payload,
          {
            headers: authHeaders(),
          }
        );

        toast.success("Advertising package updated.");
      } else {
        await axios.post(
          `${API_URL}/ad-packages/`,
          payload,
          {
            headers: authHeaders(),
          }
        );

        toast.success("Advertising package created.");
      }

      closeForm();
      await fetchPackages();
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setSaving(false);
    }
  };

  const togglePackage = async (pkg) => {
    try {
      await axios.post(
        `${API_URL}/ad-packages/${pkg.id}/toggle`,
        {},
        {
          headers: authHeaders(),
        }
      );

      toast.success(
        pkg.status === "active"
          ? "Advertising package disabled."
          : "Advertising package enabled."
      );

      await fetchPackages();
    } catch (error) {
      toast.error(safeError(error));
    }
  };

  const deletePackage = async (pkg) => {
    const confirmed = window.confirm(
      `Delete "${pkg.name}"? A package already used by an advert cannot be deleted.`
    );

    if (!confirmed) {
      return;
    }

    try {
      await axios.delete(
        `${API_URL}/ad-packages/${pkg.id}`,
        {
          headers: authHeaders(),
        }
      );

      toast.success("Advertising package deleted.");
      await fetchPackages();
    } catch (error) {
      toast.error(safeError(error));
    }
  };

  return (
    <div
      className="space-y-6"
      data-testid="advertising-packages-page"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            Advertising Packages
          </h1>
          <p className="mt-1 text-neutral-400">
            Manage advertiser pricing, coverage, duration and
            impression limits.
          </p>
        </div>

        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Create Package
        </Button>
      </div>

      <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
        <p className="font-medium text-blue-300">
          Advertising billing source of truth
        </p>
        <p className="mt-1 text-sm text-neutral-400">
          Prices saved here are shown to advertisers and used by
          the backend when initializing payment.
        </p>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="dashboard-card space-y-4 p-6"
        >
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">
              {editingPackage
                ? "Edit Advertising Package"
                : "Create Advertising Package"}
            </h2>

            <button
              type="button"
              onClick={closeForm}
              className="text-neutral-400 hover:text-white"
              aria-label="Close package form"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm text-neutral-400">
                Package Name
              </label>
              <input
                required
                value={formData.name}
                onChange={(event) =>
                  setFormData({
                    ...formData,
                    name: event.target.value,
                  })
                }
                className={inputClassName}
              />
            </div>

            <div>
              <label className="text-sm text-neutral-400">
                Coverage Scope
              </label>
              <select
                value={formData.coverage_scope}
                onChange={(event) =>
                  setFormData({
                    ...formData,
                    coverage_scope: event.target.value,
                  })
                }
                className={inputClassName}
              >
                <option value="constituency">
                  Constituency
                </option>
                <option value="county">County</option>
                <option value="national">National</option>
              </select>
            </div>

            <div>
              <label className="text-sm text-neutral-400">
                Price (KES)
              </label>
              <input
                required
                type="number"
                min="1"
                step="1"
                value={formData.price}
                onChange={(event) =>
                  setFormData({
                    ...formData,
                    price: event.target.value,
                  })
                }
                className={inputClassName}
              />
            </div>

            <div>
              <label className="text-sm text-neutral-400">
                Duration (Days)
              </label>
              <input
                required
                type="number"
                min="1"
                max="3650"
                value={formData.duration_days}
                onChange={(event) =>
                  setFormData({
                    ...formData,
                    duration_days: event.target.value,
                  })
                }
                className={inputClassName}
              />
            </div>

            <div>
              <label className="text-sm text-neutral-400">
                Maximum Impressions
              </label>
              <input
                type="number"
                min="1"
                value={formData.max_impressions}
                onChange={(event) =>
                  setFormData({
                    ...formData,
                    max_impressions: event.target.value,
                  })
                }
                className={inputClassName}
              />
            </div>

            {editingPackage && (
              <div>
                <label className="text-sm text-neutral-400">
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={(event) =>
                    setFormData({
                      ...formData,
                      status: event.target.value,
                    })
                  }
                  className={inputClassName}
                >
                  <option value="active">Active</option>
                  <option value="disabled">Disabled</option>
                </select>
              </div>
            )}
          </div>

          <div>
            <label className="text-sm text-neutral-400">
              Description
            </label>
            <textarea
              required
              rows={3}
              value={formData.description}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  description: event.target.value,
                })
              }
              className={inputClassName}
            />
          </div>

          {Number(formData.price) < 100 && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-300">
              This is a low testing price. Restore production
              pricing after completing the payment test.
            </div>
          )}

          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={closeForm}
              disabled={saving}
            >
              Cancel
            </Button>

            <Button type="submit" disabled={saving}>
              {saving
                ? "Saving…"
                : editingPackage
                  ? "Save Changes"
                  : "Create Package"}
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="dashboard-card p-12 text-center">
          Loading advertising packages…
        </div>
      ) : packages.length === 0 ? (
        <div className="dashboard-card p-12 text-center">
          <Megaphone className="mx-auto mb-3 h-10 w-10 text-neutral-600" />
          <p className="font-medium">
            No advertising packages found
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {packages.map((pkg) => {
            const active = pkg.status === "active";

            return (
              <div
                key={pkg.id}
                className="dashboard-card p-6"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex gap-3">
                    <div className="rounded-lg bg-purple-500/10 p-2">
                      <Megaphone className="h-5 w-5 text-purple-400" />
                    </div>

                    <div>
                      <h3 className="font-semibold">
                        {pkg.name}
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        {pkg.description}
                      </p>
                    </div>
                  </div>

                  <span
                    className={
                      active
                        ? "badge-active"
                        : "badge-inactive"
                    }
                  >
                    {active ? "Active" : "Disabled"}
                  </span>
                </div>

                <div className="mt-5 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">
                      Price
                    </span>
                    <span className="font-semibold text-green-400">
                      {formatCurrency(pkg.price)}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-neutral-400">
                      Duration
                    </span>
                    <span>{pkg.duration_days} days</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-neutral-400">
                      Coverage
                    </span>
                    <span className="capitalize">
                      {pkg.coverage_scope}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-neutral-400">
                      Max impressions
                    </span>
                    <span>
                      {pkg.max_impressions
                        ? Number(
                            pkg.max_impressions
                          ).toLocaleString()
                        : "Unlimited"}
                    </span>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openEdit(pkg)}
                  >
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => togglePackage(pkg)}
                  >
                    {active ? (
                      <Ban className="mr-2 h-4 w-4" />
                    ) : (
                      <CheckCircle className="mr-2 h-4 w-4" />
                    )}
                    {active ? "Disable" : "Enable"}
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    className="border-red-700 text-red-400"
                    onClick={() => deletePackage(pkg)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AdminAdvertisingPackages;
