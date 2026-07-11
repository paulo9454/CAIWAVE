import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertCircle,
  Banknote,
  Building2,
  CheckCircle,
  CreditCard,
  Loader2,
  Save,
  Smartphone,
} from "lucide-react";

import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { API_URL } from "../../lib/utils";
import { getAuthToken } from "../../lib/auth";


const EMPTY_FORM = {
  status: "draft",
  default_customer_method: "paystack",

  paystack_enabled: true,
  paystack_subaccount_code: "",

  paybill_enabled: false,
  paybill_number: "",
  paybill_business_name: "",
  paybill_reference_template: "HOTSPOT-{hotspot_id}",

  till_enabled: false,
  till_number: "",
  till_business_name: "",

  bank_enabled: false,
  bank_name: "",
  bank_branch: "",
  bank_account_name: "",
  bank_account_number: "",

  settlement_method: "paystack_subaccount",
};


const METHOD_OPTIONS = [
  {
    value: "paystack",
    label: "Paystack Checkout",
  },
  {
    value: "mpesa_paybill",
    label: "M-Pesa Paybill",
  },
  {
    value: "mpesa_till",
    label: "M-Pesa Till",
  },
  {
    value: "bank_transfer",
    label: "Bank Transfer",
  },
];


const SETTLEMENT_OPTIONS = [
  {
    value: "paystack_subaccount",
    label: "Paystack Subaccount",
  },
  {
    value: "direct_paybill",
    label: "Direct Paybill",
  },
  {
    value: "direct_till",
    label: "Direct Till",
  },
  {
    value: "bank_account",
    label: "Bank Account",
  },
];


const PaymentSettings = () => {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingSensitiveDetails, setEditingSensitiveDetails] = useState(false);

  const headers = useMemo(() => ({
    Authorization: `Bearer ${getAuthToken()}`,
  }), []);

  useEffect(() => {
    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const loadProfile = async () => {
    setLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/owner/payment-profile`,
        { headers },
      );

      const data = response.data;
      setProfile(data);

      setForm((current) => ({
        ...current,
        status: data.status || "draft",
        default_customer_method:
          data.default_customer_method || "paystack",

        paystack_enabled:
          Boolean(data.customer_payment_methods?.paystack?.enabled),

        paybill_enabled:
          Boolean(data.customer_payment_methods?.mpesa_paybill?.enabled),
        paybill_business_name:
          data.customer_payment_methods?.mpesa_paybill?.business_name || "",
        paybill_reference_template:
          data.customer_payment_methods?.mpesa_paybill
            ?.account_reference_template || "HOTSPOT-{hotspot_id}",

        till_enabled:
          Boolean(data.customer_payment_methods?.mpesa_till?.enabled),
        till_business_name:
          data.customer_payment_methods?.mpesa_till?.business_name || "",

        bank_enabled:
          Boolean(data.customer_payment_methods?.bank_transfer?.enabled),
        bank_name:
          data.customer_payment_methods?.bank_transfer?.bank_name || "",
        bank_branch:
          data.customer_payment_methods?.bank_transfer?.branch || "",
        bank_account_name:
          data.customer_payment_methods?.bank_transfer?.account_name || "",

        settlement_method:
          data.settlement?.method || "paystack_subaccount",

        paystack_subaccount_code: "",
        paybill_number: "",
        till_number: "",
        bank_account_number: "",
      }));
    } catch (error) {
      if (error.response?.status === 404) {
        setProfile(null);
        setForm(EMPTY_FORM);
      } else {
        toast.error(
          error.response?.data?.detail
          || "Failed to load payment settings",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const enabledMethods = useMemo(() => ({
    paystack: form.paystack_enabled,
    mpesa_paybill: form.paybill_enabled,
    mpesa_till: form.till_enabled,
    bank_transfer: form.bank_enabled,
  }), [form]);

  const validateForm = () => {
    if (!Object.values(enabledMethods).some(Boolean)) {
      return "Enable at least one customer payment method.";
    }

    if (!enabledMethods[form.default_customer_method]) {
      return "The default customer method must be enabled.";
    }

    if (
      form.paystack_enabled
      && (!profile || editingSensitiveDetails)
      && !form.paystack_subaccount_code.trim()
    ) {
      return "Enter the Paystack subaccount code.";
    }

    if (form.paybill_enabled) {
      if (
        (!profile || editingSensitiveDetails)
        && !form.paybill_number.trim()
      ) {
        return "Enter the M-Pesa Paybill number.";
      }

      if (!form.paybill_reference_template.trim()) {
        return "Enter a Paybill account-reference template.";
      }
    }

    if (
      form.till_enabled
      && (!profile || editingSensitiveDetails)
      && !form.till_number.trim()
    ) {
      return "Enter the M-Pesa Till number.";
    }

    if (form.bank_enabled) {
      if (!form.bank_name.trim()) {
        return "Enter the bank name.";
      }

      if (!form.bank_account_name.trim()) {
        return "Enter the bank account name.";
      }

      if (
        (!profile || editingSensitiveDetails)
        && !form.bank_account_number.trim()
      ) {
        return "Enter the bank account number.";
      }
    }

    if (
      form.settlement_method === "direct_paybill"
      && !form.paybill_enabled
    ) {
      return "Direct Paybill settlement requires Paybill to be enabled.";
    }

    if (
      form.settlement_method === "direct_till"
      && !form.till_enabled
    ) {
      return "Direct Till settlement requires Till to be enabled.";
    }

    if (
      form.settlement_method === "bank_account"
      && !form.bank_enabled
    ) {
      return "Bank settlement requires bank transfer to be enabled.";
    }

    return null;
  };

  const buildCreatePayload = () => ({
    owner_id: "self",
    status: form.status,
    default_customer_method: form.default_customer_method,

    customer_payment_methods: {
      paystack: {
        enabled: form.paystack_enabled,
        checkout_mode: "hosted",
        verification_mode: "automatic",
      },

      mpesa_paybill: {
        enabled: form.paybill_enabled,
        paybill_number:
          form.paybill_enabled ? form.paybill_number.trim() : null,
        business_name:
          form.paybill_business_name.trim() || null,
        account_reference_template:
          form.paybill_enabled
            ? form.paybill_reference_template.trim()
            : null,
        verification_mode: "manual",
      },

      mpesa_till: {
        enabled: form.till_enabled,
        till_number:
          form.till_enabled ? form.till_number.trim() : null,
        business_name:
          form.till_business_name.trim() || null,
        verification_mode: "manual",
      },

      bank_transfer: {
        enabled: form.bank_enabled,
        bank_name:
          form.bank_enabled ? form.bank_name.trim() : null,
        branch:
          form.bank_branch.trim() || null,
        account_name:
          form.bank_enabled ? form.bank_account_name.trim() : null,
        account_number:
          form.bank_enabled ? form.bank_account_number.trim() : null,
        verification_mode: "manual",
      },
    },

    settlement: {
      method: form.settlement_method,

      paystack_subaccount_code:
        form.settlement_method === "paystack_subaccount"
          ? form.paystack_subaccount_code.trim()
          : null,

      paybill_number:
        form.settlement_method === "direct_paybill"
          ? form.paybill_number.trim()
          : null,

      till_number:
        form.settlement_method === "direct_till"
          ? form.till_number.trim()
          : null,

      bank_name:
        form.settlement_method === "bank_account"
          ? form.bank_name.trim()
          : null,

      bank_branch:
        form.settlement_method === "bank_account"
          ? form.bank_branch.trim() || null
          : null,

      bank_account_name:
        form.settlement_method === "bank_account"
          ? form.bank_account_name.trim()
          : null,

      bank_account_number:
        form.settlement_method === "bank_account"
          ? form.bank_account_number.trim()
          : null,
    },
  });

  const saveProfile = async (event) => {
    event.preventDefault();

    const validationError = validateForm();

    if (validationError) {
      toast.error(validationError);
      return;
    }

    if (profile && !editingSensitiveDetails) {
      try {
        setSaving(true);

        const response = await axios.put(
          `${API_URL}/owner/payment-profile`,
          {
            status: form.status,
            default_customer_method: form.default_customer_method,
          },
          { headers },
        );

        setProfile(response.data);
        toast.success("Payment profile updated.");
      } catch (error) {
        toast.error(
          error.response?.data?.detail
          || "Failed to update payment profile",
        );
      } finally {
        setSaving(false);
      }

      return;
    }

    const payload = buildCreatePayload();

    try {
      setSaving(true);

      const response = profile
        ? await axios.put(
          `${API_URL}/owner/payment-profile`,
          {
            status: payload.status,
            default_customer_method: payload.default_customer_method,
            customer_payment_methods: payload.customer_payment_methods,
            settlement: payload.settlement,
          },
          { headers },
        )
        : await axios.post(
          `${API_URL}/owner/payment-profile`,
          payload,
          { headers },
        );

      setProfile(response.data);
      setEditingSensitiveDetails(false);
      toast.success(
        profile
          ? "Payment details updated successfully."
          : "Payment profile created successfully.",
      );

      await loadProfile();
    } catch (error) {
      toast.error(
        error.response?.data?.detail
        || "Failed to save payment profile",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="payment-settings-page">
      <div>
        <h1 className="text-2xl font-bold">Payment Settings</h1>
        <p className="mt-1 text-neutral-400">
          Configure how customers pay and where your hotspot revenue is received.
        </p>
      </div>

      <div className={`rounded-xl border p-5 ${
        profile?.status === "active"
          ? "border-green-500/30 bg-green-500/10"
          : "border-yellow-500/30 bg-yellow-500/10"
      }`}>
        <div className="flex items-start gap-3">
          {profile?.status === "active" ? (
            <CheckCircle className="mt-1 h-6 w-6 text-green-400" />
          ) : (
            <AlertCircle className="mt-1 h-6 w-6 text-yellow-400" />
          )}

          <div>
            <h3 className="font-semibold">
              {profile
                ? `Payment profile: ${profile.status}`
                : "Payment profile not configured"}
            </h3>

            <p className="mt-1 text-sm text-neutral-400">
              Manual Paybill, Till and bank payments will not automatically
              activate internet until payment verification is integrated.
            </p>
          </div>
        </div>
      </div>

      {profile && (
        <div className="dashboard-card p-5">
          <h3 className="mb-4 font-semibold">Saved Payment Details</h3>

          <div className="grid gap-3 text-sm md:grid-cols-2">
            <p>
              Default method:{" "}
              <span className="font-medium">
                {profile.default_customer_method}
              </span>
            </p>

            <p>
              Settlement:{" "}
              <span className="font-medium">
                {profile.settlement?.method}
              </span>
            </p>

            {profile.settlement?.paystack_subaccount_masked && (
              <p>
                Paystack account:{" "}
                {profile.settlement.paystack_subaccount_masked}
              </p>
            )}

            {profile.settlement?.paybill_number_masked && (
              <p>
                Paybill: {profile.settlement.paybill_number_masked}
              </p>
            )}

            {profile.settlement?.till_number_masked && (
              <p>
                Till: {profile.settlement.till_number_masked}
              </p>
            )}

            {profile.settlement?.bank_account_number_masked && (
              <p>
                Bank account:{" "}
                {profile.settlement.bank_account_number_masked}
              </p>
            )}
          </div>

          <Button
            type="button"
            variant="outline"
            className="mt-4"
            onClick={() => setEditingSensitiveDetails((current) => !current)}
          >
            {editingSensitiveDetails
              ? "Cancel sensitive detail update"
              : "Replace payment details"}
          </Button>
        </div>
      )}

      <form onSubmit={saveProfile} className="space-y-6">
        <div className="dashboard-card p-6">
          <h3 className="mb-4 flex items-center gap-2 font-semibold">
            <CreditCard className="h-5 w-5 text-blue-400" />
            Customer Payment Methods
          </h3>

          <div className="grid gap-4 md:grid-cols-2">
            <MethodToggle
              label="Paystack Checkout"
              description="Hosted checkout with supported Paystack channels."
              checked={form.paystack_enabled}
              onChange={(checked) => setField("paystack_enabled", checked)}
            />

            <MethodToggle
              label="M-Pesa Paybill"
              description="Customer pays using your Paybill and account reference."
              checked={form.paybill_enabled}
              onChange={(checked) => setField("paybill_enabled", checked)}
            />

            <MethodToggle
              label="M-Pesa Till"
              description="Customer pays directly to your Buy Goods Till."
              checked={form.till_enabled}
              onChange={(checked) => setField("till_enabled", checked)}
            />

            <MethodToggle
              label="Bank Transfer"
              description="Display your bank-transfer instructions."
              checked={form.bank_enabled}
              onChange={(checked) => setField("bank_enabled", checked)}
            />
          </div>

          <div className="mt-5">
            <label className="mb-1 block text-sm font-medium">
              Default customer payment method
            </label>

            <select
              value={form.default_customer_method}
              onChange={(event) => {
                setField("default_customer_method", event.target.value);
              }}
              className="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2"
            >
              {METHOD_OPTIONS
                .filter((option) => enabledMethods[option.value])
                .map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
            </select>
          </div>
        </div>

        {form.paystack_enabled && (!profile || editingSensitiveDetails) && (
          <PaymentSection
            icon={CreditCard}
            title="Paystack Settlement"
          >
            <Field
              label="Paystack Subaccount Code"
              value={form.paystack_subaccount_code}
              onChange={(value) => {
                setField("paystack_subaccount_code", value);
              }}
              placeholder="ACCT_xxxxxxxxx"
            />
          </PaymentSection>
        )}

        {form.paybill_enabled && (
          <PaymentSection icon={Smartphone} title="M-Pesa Paybill">
            {(!profile || editingSensitiveDetails) && (
              <Field
                label="Paybill Number"
                value={form.paybill_number}
                onChange={(value) => setField("paybill_number", value)}
                placeholder="123456"
              />
            )}

            <Field
              label="Business Name"
              value={form.paybill_business_name}
              onChange={(value) => {
                setField("paybill_business_name", value);
              }}
              placeholder="Your business name"
            />

            <Field
              label="Account Reference Template"
              value={form.paybill_reference_template}
              onChange={(value) => {
                setField("paybill_reference_template", value);
              }}
              placeholder="HOTSPOT-{hotspot_id}"
            />
          </PaymentSection>
        )}

        {form.till_enabled && (
          <PaymentSection icon={Smartphone} title="M-Pesa Till">
            {(!profile || editingSensitiveDetails) && (
              <Field
                label="Till Number"
                value={form.till_number}
                onChange={(value) => setField("till_number", value)}
                placeholder="123456"
              />
            )}

            <Field
              label="Business Name"
              value={form.till_business_name}
              onChange={(value) => {
                setField("till_business_name", value);
              }}
              placeholder="Your business name"
            />
          </PaymentSection>
        )}

        {form.bank_enabled && (
          <PaymentSection icon={Building2} title="Bank Account">
            <Field
              label="Bank Name"
              value={form.bank_name}
              onChange={(value) => setField("bank_name", value)}
              placeholder="Bank name"
            />

            <Field
              label="Branch"
              value={form.bank_branch}
              onChange={(value) => setField("bank_branch", value)}
              placeholder="Branch"
            />

            <Field
              label="Account Name"
              value={form.bank_account_name}
              onChange={(value) => {
                setField("bank_account_name", value);
              }}
              placeholder="Account holder name"
            />

            {(!profile || editingSensitiveDetails) && (
              <Field
                label="Account Number"
                value={form.bank_account_number}
                onChange={(value) => {
                  setField("bank_account_number", value);
                }}
                placeholder="Account number"
              />
            )}
          </PaymentSection>
        )}

        <div className="dashboard-card p-6">
          <h3 className="mb-4 flex items-center gap-2 font-semibold">
            <Banknote className="h-5 w-5 text-green-400" />
            Revenue Settlement
          </h3>

          <label className="mb-1 block text-sm font-medium">
            Where hotspot revenue should be received
          </label>

          <select
            value={form.settlement_method}
            onChange={(event) => {
              setField("settlement_method", event.target.value);
            }}
            disabled={Boolean(profile && !editingSensitiveDetails)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 disabled:opacity-60"
          >
            {SETTLEMENT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium">
              Profile Status
            </label>

            <select
              value={form.status}
              onChange={(event) => setField("status", event.target.value)}
              className="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
            </select>
          </div>
        </div>

        <Button
          type="submit"
          disabled={saving}
          className="w-full"
        >
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              {profile ? "Update Payment Profile" : "Create Payment Profile"}
            </>
          )}
        </Button>
      </form>
    </div>
  );
};


const MethodToggle = ({
  label,
  description,
  checked,
  onChange,
}) => (
  <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-neutral-700 p-4">
    <input
      type="checkbox"
      checked={checked}
      onChange={(event) => onChange(event.target.checked)}
      className="mt-1"
    />

    <div>
      <p className="font-medium">{label}</p>
      <p className="mt-1 text-xs text-neutral-400">{description}</p>
    </div>
  </label>
);


const PaymentSection = ({ icon: Icon, title, children }) => (
  <div className="dashboard-card p-6">
    <h3 className="mb-4 flex items-center gap-2 font-semibold">
      <Icon className="h-5 w-5 text-blue-400" />
      {title}
    </h3>

    <div className="grid gap-4 md:grid-cols-2">
      {children}
    </div>
  </div>
);


const Field = ({
  label,
  value,
  onChange,
  placeholder,
}) => (
  <div>
    <label className="mb-1 block text-sm font-medium">{label}</label>

    <Input
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
    />
  </div>
);


export default PaymentSettings;
