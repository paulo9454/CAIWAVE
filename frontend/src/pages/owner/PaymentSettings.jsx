import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  ChevronDown,
  CreditCard,
  Loader2,
  LockKeyhole,
  Save,
  ShieldCheck,
  Smartphone,
} from "lucide-react";

import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { API_URL } from "../../lib/utils";
import { getAuthToken } from "../../lib/auth";


const GATEWAYS = [
  {
    value: "paystack",
    label: "Paystack",
    description: "Automated checkout, verification and owner settlement.",
    icon: CreditCard,
    available: true,
  },
  {
    value: "mpesa_daraja",
    label: "Safaricom M-Pesa API",
    description: "Direct STK Push through the owner's Daraja account.",
    icon: Smartphone,
    available: false,
  },
  {
    value: "kopokopo",
    label: "Kopo Kopo",
    description: "Automated M-Pesa collections through Kopo Kopo.",
    icon: Smartphone,
    available: false,
  },
  {
    value: "bank_paybill_api",
    label: "Bank Paybill API",
    description: "Automated bank Paybill through a supported bank API.",
    icon: Building2,
    available: false,
  },
];


const EMPTY_FORM = {
  gateway: "paystack",
  business_name: "",
  contact_email: "",
  contact_phone: "",
  uses_caiwave_platform_account: true,
  paystack_subaccount_code: "",
  settlement_bank_name: "",
  settlement_account_last4: "",
};


const PaymentSettings = () => {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [replacingConfiguration, setReplacingConfiguration] = useState(false);

  const headers = useMemo(
    () => ({
      Authorization: `Bearer ${getAuthToken()}`,
    }),
    [],
  );

  useEffect(() => {
    loadGateway();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedGateway = GATEWAYS.find(
    (gateway) => gateway.value === form.gateway,
  );

  const setField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const loadGateway = async () => {
    setLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/owner/payment-gateway`,
        { headers },
      );

      const data = response.data;
      const configuration = data.configuration || {};

      setProfile(data);

      setForm({
        gateway: configuration.gateway || "paystack",
        business_name: configuration.business_name || "",
        contact_email: configuration.contact_email || "",
        contact_phone: "",
        uses_caiwave_platform_account:
          configuration.uses_caiwave_platform_account !== false,
        paystack_subaccount_code: "",
        settlement_bank_name: configuration.settlement_bank_name || "",
        settlement_account_last4:
          configuration.settlement_account_last4 || "",
      });
    } catch (error) {
      if (error.response?.status === 404) {
        setProfile(null);
        setForm(EMPTY_FORM);
      } else {
        toast.error(
          error.response?.data?.detail
          || "Failed to load payment gateway settings",
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const validatePaystack = () => {
    if (!form.business_name.trim()) {
      return "Enter the business name.";
    }

    if (!form.contact_email.trim()) {
      return "Enter the contact email.";
    }

    if ((!profile || replacingConfiguration) && !form.contact_phone.trim()) {
      return "Enter the contact phone number.";
    }

    if (
      !form.uses_caiwave_platform_account
      && (!profile || replacingConfiguration)
      && !form.paystack_subaccount_code.trim()
    ) {
      return "Enter the Paystack subaccount code.";
    }

    return null;
  };

  const buildPaystackConfiguration = () => ({
    gateway: "paystack",
    business_name: form.business_name.trim(),
    contact_email: form.contact_email.trim(),
    contact_phone: form.contact_phone.trim(),
    uses_caiwave_platform_account:
      form.uses_caiwave_platform_account,
    paystack_subaccount_code:
      form.uses_caiwave_platform_account
        ? null
        : form.paystack_subaccount_code.trim(),
    settlement_bank_name:
      form.settlement_bank_name.trim() || null,
    settlement_account_last4:
      form.settlement_account_last4.trim() || null,
  });

  const saveGateway = async (event) => {
    event.preventDefault();

    if (!selectedGateway?.available) {
      toast.error(
        "This gateway requires the secure credential setup module, "
        + "which is not enabled yet.",
      );
      return;
    }

    const validationError = validatePaystack();

    if (validationError) {
      toast.error(validationError);
      return;
    }

    if (profile && !replacingConfiguration) {
      toast.error(
        "Choose Replace gateway configuration before changing "
        + "gateway credentials.",
      );
      return;
    }

    const payload = {
      configuration: buildPaystackConfiguration(),
    };

    try {
      setSaving(true);

      const response = profile
        ? await axios.put(
          `${API_URL}/owner/payment-gateway`,
          payload,
          { headers },
        )
        : await axios.post(
          `${API_URL}/owner/payment-gateway`,
          payload,
          { headers },
        );

      setProfile(response.data);
      setReplacingConfiguration(false);

      toast.success(
        profile
          ? "Gateway configuration updated. Verification is required."
          : "Payment gateway saved as draft.",
      );

      await loadGateway();
    } catch (error) {
      const detail = error.response?.data?.detail;

      if (Array.isArray(detail)) {
        toast.error(
          detail
            .map((item) => item.msg)
            .filter(Boolean)
            .join(", "),
        );
      } else {
        toast.error(detail || "Failed to save payment gateway");
      }
    } finally {
      setSaving(false);
    }
  };

  const suspendGateway = async () => {
    try {
      setSaving(true);

      const response = await axios.put(
        `${API_URL}/owner/payment-gateway`,
        { status: "suspended" },
        { headers },
      );

      setProfile(response.data);
      toast.success("Payment gateway suspended.");
    } catch (error) {
      toast.error(
        error.response?.data?.detail
        || "Failed to suspend payment gateway",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">
          Payment Gateway Settings
        </h1>

        <p className="mt-1 text-neutral-400">
          Choose how CAIWAVE processes customer payments and settles
          hotspot revenue to your account.
        </p>
      </div>

      <CustomerExperienceNotice />

      {profile && (
        <GatewayStatusCard
          profile={profile}
          onReplace={() => setReplacingConfiguration(true)}
          onCancelReplace={() => setReplacingConfiguration(false)}
          replacingConfiguration={replacingConfiguration}
          onSuspend={suspendGateway}
          saving={saving}
        />
      )}

      <form onSubmit={saveGateway} className="space-y-6">
        <div className="dashboard-card p-6">
          <label className="mb-2 block text-sm font-medium">
            Payment Gateway
          </label>

          <div className="relative">
            <select
              value={form.gateway}
              disabled={Boolean(profile && !replacingConfiguration)}
              onChange={(event) => {
                const gateway = GATEWAYS.find(
                  (item) => item.value === event.target.value,
                );

                if (!gateway?.available) {
                  toast.info(
                    `${gateway?.label} requires secure API credential `
                    + "storage before it can be enabled.",
                  );
                }

                setField("gateway", event.target.value);
              }}
              className="w-full appearance-none rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-3 pr-10 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {GATEWAYS.map((gateway) => (
                <option
                  key={gateway.value}
                  value={gateway.value}
                >
                  {gateway.label}
                  {gateway.available ? "" : " — Secure setup pending"}
                </option>
              ))}
            </select>

            <ChevronDown className="pointer-events-none absolute right-3 top-3.5 h-5 w-5 text-neutral-500" />
          </div>

          <GatewayDescription gateway={selectedGateway} />
        </div>

        {form.gateway === "paystack" && (
          <PaystackForm
            form={form}
            setField={setField}
            profile={profile}
            replacingConfiguration={replacingConfiguration}
          />
        )}

        {form.gateway !== "paystack" && (
          <SecureSetupPending gateway={selectedGateway} />
        )}

        {(!profile || replacingConfiguration) && (
          <Button
            type="submit"
            className="w-full"
            disabled={saving || !selectedGateway?.available}
          >
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {profile
                  ? "Replace Gateway Configuration"
                  : "Save Gateway as Draft"}
              </>
            )}
          </Button>
        )}
      </form>
    </div>
  );
};


const CustomerExperienceNotice = () => (
  <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-5">
    <div className="flex items-start gap-3">
      <Smartphone className="mt-0.5 h-6 w-6 text-blue-400" />

      <div>
        <h3 className="font-semibold">
          Simple customer payment experience
        </h3>

        <p className="mt-1 text-sm text-neutral-300">
          Customers only choose a package, enter their phone number and
          click Pay. CAIWAVE starts the STK prompt automatically using
          the gateway configured here.
        </p>
      </div>
    </div>
  </div>
);


const GatewayStatusCard = ({
  profile,
  onReplace,
  onCancelReplace,
  replacingConfiguration,
  onSuspend,
  saving,
}) => {
  const isVerified = profile.verification_status === "verified";
  const isActive = profile.status === "active";

  return (
    <div className={`rounded-xl border p-5 ${
      isVerified
        ? "border-green-500/30 bg-green-500/10"
        : "border-yellow-500/30 bg-yellow-500/10"
    }`}>
      <div className="flex flex-col justify-between gap-4 md:flex-row">
        <div className="flex items-start gap-3">
          {isVerified ? (
            <CheckCircle2 className="mt-0.5 h-6 w-6 text-green-400" />
          ) : (
            <AlertCircle className="mt-0.5 h-6 w-6 text-yellow-400" />
          )}

          <div>
            <h3 className="font-semibold">
              {profile.configuration?.business_name || "Payment Gateway"}
            </h3>

            <p className="mt-1 text-sm text-neutral-300">
              Gateway: {profile.configuration?.gateway}
            </p>

            <p className="text-sm text-neutral-400">
              Status: {profile.status} · Verification:{" "}
              {profile.verification_status}
            </p>

            {profile.verification_message && (
              <p className="mt-2 text-sm text-neutral-400">
                {profile.verification_message}
              </p>
            )}

            {isActive && (
              <p className="mt-2 text-sm text-green-300">
                This gateway is ready to process hotspot payments.
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={
              replacingConfiguration
                ? onCancelReplace
                : onReplace
            }
          >
            {replacingConfiguration
              ? "Cancel replacement"
              : "Replace configuration"}
          </Button>

          {profile.status !== "suspended" && (
            <Button
              type="button"
              variant="outline"
              disabled={saving}
              onClick={onSuspend}
            >
              Suspend
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};


const GatewayDescription = ({ gateway }) => {
  if (!gateway) return null;

  const Icon = gateway.icon;

  return (
    <div className="mt-4 flex items-start gap-3 rounded-lg border border-neutral-800 bg-neutral-950/40 p-4">
      <Icon className="mt-0.5 h-5 w-5 text-blue-400" />

      <div>
        <p className="font-medium">{gateway.label}</p>
        <p className="mt-1 text-sm text-neutral-400">
          {gateway.description}
        </p>

        {!gateway.available && (
          <p className="mt-2 flex items-center gap-2 text-xs text-yellow-400">
            <LockKeyhole className="h-4 w-4" />
            Secure API credential storage must be completed first.
          </p>
        )}
      </div>
    </div>
  );
};


const PaystackForm = ({
  form,
  setField,
  profile,
  replacingConfiguration,
}) => {
  const showSensitiveFields = !profile || replacingConfiguration;

  return (
    <div className="dashboard-card p-6">
      <h3 className="mb-5 flex items-center gap-2 font-semibold">
        <ShieldCheck className="h-5 w-5 text-green-400" />
        Paystack Gateway Details
      </h3>

      <div className="grid gap-4 md:grid-cols-2">
        <Field
          label="Business Name"
          value={form.business_name}
          onChange={(value) => setField("business_name", value)}
          placeholder="Your business name"
          disabled={Boolean(profile && !replacingConfiguration)}
        />

        <Field
          label="Contact Email"
          type="email"
          value={form.contact_email}
          onChange={(value) => setField("contact_email", value)}
          placeholder="owner@example.com"
          disabled={Boolean(profile && !replacingConfiguration)}
        />

        {showSensitiveFields && (
          <Field
            label="Contact Phone"
            value={form.contact_phone}
            onChange={(value) => setField("contact_phone", value)}
            placeholder="2547XXXXXXXX"
          />
        )}

        <Field
          label="Settlement Bank"
          value={form.settlement_bank_name}
          onChange={(value) => {
            setField("settlement_bank_name", value);
          }}
          placeholder="Optional bank name"
          disabled={Boolean(profile && !replacingConfiguration)}
        />

        <Field
          label="Settlement Account Last 4 Digits"
          value={form.settlement_account_last4}
          onChange={(value) => {
            setField("settlement_account_last4", value);
          }}
          placeholder="1234"
          maxLength={4}
          disabled={Boolean(profile && !replacingConfiguration)}
        />
      </div>

      <label className="mt-5 flex items-start gap-3 rounded-lg border border-neutral-700 p-4">
        <input
          type="checkbox"
          checked={form.uses_caiwave_platform_account}
          disabled={Boolean(profile && !replacingConfiguration)}
          onChange={(event) => {
            setField(
              "uses_caiwave_platform_account",
              event.target.checked,
            );
          }}
          className="mt-1"
        />

        <div>
          <p className="font-medium">
            Use CAIWAVE Paystack processing
          </p>

          <p className="mt-1 text-sm text-neutral-400">
            CAIWAVE processes the STK payment and settles the owner's
            revenue through an approved Paystack arrangement.
          </p>
        </div>
      </label>

      {!form.uses_caiwave_platform_account && showSensitiveFields && (
        <div className="mt-4">
          <Field
            label="Paystack Subaccount Code"
            value={form.paystack_subaccount_code}
            onChange={(value) => {
              setField("paystack_subaccount_code", value);
            }}
            placeholder="ACCT_xxxxxxxxx"
          />
        </div>
      )}

      <p className="mt-5 text-xs text-neutral-500">
        Saving creates a draft gateway. CAIWAVE must verify the gateway
        before it can become active.
      </p>
    </div>
  );
};


const SecureSetupPending = ({ gateway }) => (
  <div className="dashboard-card p-6">
    <div className="flex items-start gap-3">
      <LockKeyhole className="mt-0.5 h-6 w-6 text-yellow-400" />

      <div>
        <h3 className="font-semibold">
          {gateway?.label} secure setup is not enabled yet
        </h3>

        <p className="mt-2 text-sm text-neutral-400">
          This provider requires encrypted credential storage, gateway
          verification and signed callback handling. CAIWAVE will not
          accept raw API secrets through this page until that security
          layer is complete.
        </p>
      </div>
    </div>
  </div>
);


const Field = ({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  maxLength,
  disabled = false,
}) => (
  <div>
    <label className="mb-1 block text-sm font-medium">{label}</label>

    <Input
      type={type}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      maxLength={maxLength}
      disabled={disabled}
    />
  </div>
);


export default PaymentSettings;
