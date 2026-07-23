import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import {
  Edit,
  ExternalLink,
  ImagePlus,
  MousePointer,
  PackageOpen,
  Plus,
  Star,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "../../components/ui/button";
import { getAuthToken } from "../../lib/auth";
import { API_URL } from "../../lib/utils";
import { safeError } from "../../utils/safeError";

const emptyForm = {
  name: "",
  description: "",
  merchant_name: "",
  category: "",
  price: "",
  original_price: "",
  currency: "KES",
  purchase_url: "",
  is_featured: false,
  is_active: true,
};

const authConfig = () => ({
  headers: {
    Authorization: `Bearer ${getAuthToken()}`,
  },
});

const resolveImageUrl = (imageUrl) => {
  if (!imageUrl) return "";
  if (/^https?:\/\//i.test(imageUrl)) return imageUrl;

  const baseUrl = API_URL.replace(/\/api\/?$/, "");
  return `${baseUrl}${imageUrl}`;
};

const formatPrice = (value, currency = "KES") =>
  new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));

const validateImage = (file) =>
  new Promise((resolve, reject) => {
    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];

    if (!allowedTypes.includes(file.type)) {
      reject(new Error("Choose a JPG, PNG or WEBP image."));
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      reject(new Error("The image must not exceed 5MB."));
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    const image = new window.Image();

    image.onload = () => {
      URL.revokeObjectURL(objectUrl);

      if (
        image.naturalWidth !== 680 ||
        image.naturalHeight !== 680
      ) {
        reject(
          new Error(
            `Image is ${image.naturalWidth}×${image.naturalHeight}. ` +
              "CAIMART requires exactly 680×680 pixels."
          )
        );
        return;
      }

      resolve();
    };

    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("The selected image could not be read."));
    };

    image.src = objectUrl;
  });

export default function CaimartPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [imageFile, setImageFile] = useState(null);
  const [imageInputKey, setImageInputKey] = useState(0);
  const [saving, setSaving] = useState(false);
  const [busyProductId, setBusyProductId] = useState(null);

  const fetchProducts = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_URL}/marketplace/admin`,
        authConfig()
      );
      setProducts(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingProduct(null);
    setImageFile(null);
    setImageInputKey((value) => value + 1);
    setShowForm(false);
  };

  const startCreate = () => {
    setForm(emptyForm);
    setEditingProduct(null);
    setImageFile(null);
    setImageInputKey((value) => value + 1);
    setShowForm(true);
  };

  const startEdit = (product) => {
    setEditingProduct(product);
    setForm({
      name: product.name || "",
      description: product.description || "",
      merchant_name: product.merchant_name || "",
      category: product.category || "",
      price: String(product.price ?? ""),
      original_price:
        product.original_price == null
          ? ""
          : String(product.original_price),
      currency: product.currency || "KES",
      purchase_url: product.purchase_url || "",
      is_featured: Boolean(product.is_featured),
      is_active: Boolean(product.is_active),
    });
    setImageFile(null);
    setImageInputKey((value) => value + 1);
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const uploadImage = async (productId, file) => {
    const upload = new FormData();
    upload.append("image", file);

    await axios.post(
      `${API_URL}/marketplace/${productId}/upload-image`,
      upload,
      {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          "Content-Type": "multipart/form-data",
        },
      }
    );
  };

  const handleImageChange = async (event) => {
    const file = event.target.files?.[0] || null;

    if (!file) {
      setImageFile(null);
      return;
    }

    try {
      await validateImage(file);
      setImageFile(file);
      toast.success("680×680 product image accepted.");
    } catch (error) {
      event.target.value = "";
      setImageFile(null);
      toast.error(error.message);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!editingProduct && !imageFile) {
      toast.error("A 680×680 product image is required.");
      return;
    }

    setSaving(true);

    try {
      if (imageFile) {
        await validateImage(imageFile);
      }

      const payload = {
        ...form,
        price: Number(form.price),
        original_price:
          form.original_price === ""
            ? null
            : Number(form.original_price),
        image_url: editingProduct?.image_url || null,
      };

      const response = editingProduct
        ? await axios.put(
            `${API_URL}/marketplace/${editingProduct.id}`,
            payload,
            authConfig()
          )
        : await axios.post(
            `${API_URL}/marketplace/`,
            payload,
            authConfig()
          );

      const savedProduct = response.data;

      if (imageFile) {
        await uploadImage(savedProduct.id, imageFile);
      }

      toast.success(
        editingProduct
          ? "CAIMART product updated."
          : "CAIMART product created."
      );

      resetForm();
      await fetchProducts();
    } catch (error) {
      toast.error(safeError(error));
      await fetchProducts();
    } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async (product) => {
    setBusyProductId(product.id);

    try {
      await axios.put(
        `${API_URL}/marketplace/${product.id}/status`,
        null,
        {
          ...authConfig(),
          params: {
            is_active: !product.is_active,
          },
        }
      );

      toast.success(
        product.is_active
          ? "Product deactivated."
          : "Product activated."
      );
      await fetchProducts();
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setBusyProductId(null);
    }
  };

  const deleteProduct = async (product) => {
    const confirmed = window.confirm(
      `Delete "${product.name}" permanently?`
    );

    if (!confirmed) return;

    setBusyProductId(product.id);

    try {
      await axios.delete(
        `${API_URL}/marketplace/${product.id}`,
        authConfig()
      );
      toast.success("CAIMART product deleted.");
      await fetchProducts();
    } catch (error) {
      toast.error(safeError(error));
    } finally {
      setBusyProductId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">CAIMART Affiliate Market</h1>
          <p className="mt-1 text-sm text-neutral-400">
            Manage merchant products, affiliate destinations and click activity.
          </p>
        </div>

        <Button onClick={startCreate} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Product
        </Button>
      </div>

      <div className="rounded-xl border border-blue-700/30 bg-blue-950/30 p-4">
        <div className="flex gap-3">
          <ImagePlus className="mt-0.5 h-5 w-5 shrink-0 text-blue-400" />
          <div>
            <p className="font-semibold text-blue-100">
              Product image requirement
            </p>
            <p className="mt-1 text-sm text-blue-200/70">
              Upload a square JPG, PNG or WEBP image measuring exactly
              680×680 pixels. Maximum file size is 5MB.
            </p>
          </div>
        </div>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="dashboard-card space-y-5"
        >
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">
                {editingProduct ? "Edit Product" : "Create Product"}
              </h2>
              <p className="text-sm text-neutral-400">
                Customers will be redirected to the merchant to complete
                their purchase.
              </p>
            </div>

            <Button type="button" variant="outline" onClick={resetForm}>
              Cancel
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-1.5">
              <span className="text-sm text-neutral-300">Product name *</span>
              <input
                required
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
                className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
              />
            </label>

            <label className="space-y-1.5">
              <span className="text-sm text-neutral-300">Merchant *</span>
              <input
                required
                value={form.merchant_name}
                onChange={(event) =>
                  setForm({
                    ...form,
                    merchant_name: event.target.value,
                  })
                }
                className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
                placeholder="Jumia"
              />
            </label>

            <label className="space-y-1.5">
              <span className="text-sm text-neutral-300">Category *</span>
              <input
                required
                value={form.category}
                onChange={(event) =>
                  setForm({ ...form, category: event.target.value })
                }
                className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
                placeholder="electronics"
              />
            </label>

            <label className="space-y-1.5">
              <span className="text-sm text-neutral-300">
                Affiliate purchase URL *
              </span>
              <input
                required
                type="url"
                value={form.purchase_url}
                onChange={(event) =>
                  setForm({
                    ...form,
                    purchase_url: event.target.value,
                  })
                }
                className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
                placeholder="https://merchant.example/product"
              />
            </label>

            <label className="space-y-1.5">
              <span className="text-sm text-neutral-300">
                Current price *
              </span>
              <input
                required
                min="0"
                step="0.01"
                type="number"
                value={form.price}
                onChange={(event) =>
                  setForm({ ...form, price: event.target.value })
                }
                className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
              />
            </label>

            <label className="space-y-1.5">
              <span className="text-sm text-neutral-300">
                Original price
              </span>
              <input
                min="0"
                step="0.01"
                type="number"
                value={form.original_price}
                onChange={(event) =>
                  setForm({
                    ...form,
                    original_price: event.target.value,
                  })
                }
                className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
              />
            </label>
          </div>

          <label className="block space-y-1.5">
            <span className="text-sm text-neutral-300">Description *</span>
            <textarea
              required
              rows={3}
              value={form.description}
              onChange={(event) =>
                setForm({
                  ...form,
                  description: event.target.value,
                })
              }
              className="w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2"
            />
          </label>

          <label className="block space-y-1.5">
            <span className="text-sm text-neutral-300">
              680×680 product image {editingProduct ? "" : "*"}
            </span>
            <input
              key={imageInputKey}
              required={!editingProduct}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleImageChange}
              className="block w-full rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm"
            />
            {editingProduct?.image_url && !imageFile && (
              <span className="text-xs text-neutral-500">
                Leave empty to retain the current image.
              </span>
            )}
          </label>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={form.is_featured}
              onChange={(event) =>
                setForm({
                  ...form,
                  is_featured: event.target.checked,
                })
              }
              className="h-4 w-4"
            />
            <span className="text-sm text-neutral-300">
              Feature this product prominently
            </span>
          </label>

          {!editingProduct && (
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) =>
                  setForm({
                    ...form,
                    is_active: event.target.checked,
                  })
                }
                className="h-4 w-4"
              />
              <span className="text-sm text-neutral-300">
                Publish immediately
              </span>
            </label>
          )}

          <Button type="submit" disabled={saving}>
            {saving
              ? "Saving…"
              : editingProduct
              ? "Update Product"
              : "Create Product"}
          </Button>
        </form>
      )}

      {loading ? (
        <div className="dashboard-card py-12 text-center text-neutral-400">
          Loading CAIMART products…
        </div>
      ) : products.length === 0 ? (
        <div className="dashboard-card py-12 text-center">
          <PackageOpen className="mx-auto h-12 w-12 text-neutral-600" />
          <h2 className="mt-4 text-lg font-semibold">No products yet</h2>
          <p className="mt-1 text-sm text-neutral-400">
            Create the first CAIMART affiliate product.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {products.map((product) => {
            const disabled = busyProductId === product.id;
            const imageUrl = resolveImageUrl(product.image_url);

            return (
              <article
                key={product.id}
                className="dashboard-card overflow-hidden p-0"
              >
                <div className="relative aspect-square bg-neutral-900">
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={product.name}
                      className="h-full w-full object-contain"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-neutral-600">
                      <ImagePlus className="h-12 w-12" />
                    </div>
                  )}

                  <div className="absolute left-3 top-3 flex gap-2">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        product.is_active
                          ? "bg-green-500/90 text-white"
                          : "bg-neutral-700/90 text-neutral-200"
                      }`}
                    >
                      {product.is_active ? "Active" : "Inactive"}
                    </span>

                    {product.is_featured && (
                      <span className="flex items-center gap-1 rounded-full bg-amber-500/90 px-2.5 py-1 text-xs font-semibold text-black">
                        <Star className="h-3 w-3" />
                        Featured
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-4 p-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-blue-400">
                      {product.merchant_name}
                    </p>
                    <h2 className="mt-1 text-lg font-semibold">
                      {product.name}
                    </h2>
                    <p className="mt-1 line-clamp-2 text-sm text-neutral-400">
                      {product.description}
                    </p>
                  </div>

                  <div className="flex items-end gap-2">
                    <span className="font-semibold text-green-400">
                      {formatPrice(product.price, product.currency)}
                    </span>
                    {product.original_price != null && (
                      <span className="text-sm text-neutral-500 line-through">
                        {formatPrice(
                          product.original_price,
                          product.currency
                        )}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="rounded-md bg-neutral-800 px-2 py-1 text-neutral-300">
                      {product.category}
                    </span>
                    <span className="flex items-center gap-1 text-neutral-400">
                      <MousePointer className="h-4 w-4" />
                      {product.click_count || 0} clicks
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      disabled={disabled}
                      onClick={() => startEdit(product)}
                      className="gap-2"
                    >
                      <Edit className="h-4 w-4" />
                      Edit
                    </Button>

                    <Button
                      type="button"
                      variant="outline"
                      disabled={disabled}
                      onClick={() => toggleStatus(product)}
                    >
                      {product.is_active ? "Deactivate" : "Activate"}
                    </Button>

                    <a
                      href={product.purchase_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 rounded-md border border-neutral-700 px-3 py-2 text-sm hover:bg-neutral-800"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Merchant
                    </a>

                    <Button
                      type="button"
                      variant="outline"
                      disabled={disabled}
                      onClick={() => deleteProduct(product)}
                      className="gap-2 border-red-900 text-red-400 hover:bg-red-950"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
