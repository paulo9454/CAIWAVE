import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import {
  AlertCircle,
  CheckCircle,
  Loader2,
  RefreshCw,
} from "lucide-react";

import { Button } from "../../components/ui/button";
import { CaiwaveLogo } from "../../components/CaiwaveLogo";
import { API_URL } from "../../lib/utils";

const MAX_VERIFICATION_ATTEMPTS = 6;
const RETRY_DELAY_MS = 2500;

const sleep = (milliseconds) =>
  new Promise((resolve) => window.setTimeout(resolve, milliseconds));

const AdvertiserPaymentReturn = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const reference =
    searchParams.get("reference") ||
    searchParams.get("trxref");

  const [status, setStatus] = useState("verifying");
  const [message, setMessage] = useState(
    "Confirming your payment with Paystack..."
  );

  useEffect(() => {
    let cancelled = false;
    let redirectTimer;

    const verifyPayment = async () => {
      if (!reference) {
        setStatus("failed");
        setMessage(
          "The payment reference is missing. Return to your dashboard and try again."
        );
        return;
      }

      for (
        let attempt = 1;
        attempt <= MAX_VERIFICATION_ATTEMPTS;
        attempt += 1
      ) {
        try {
          const response = await axios.post(
            `${API_URL}/paystack/verify/${encodeURIComponent(reference)}`
          );

          if (cancelled) return;

          if (
            response.data?.success &&
            response.data?.status === "completed"
          ) {
            setStatus("success");
            setMessage(
              "Payment verified successfully. Your advert is now active."
            );

            redirectTimer = window.setTimeout(() => {
              navigate("/advertiser/ads", { replace: true });
            }, 3000);

            return;
          }

          if (response.data?.status === "pending") {
            setMessage(
              attempt < MAX_VERIFICATION_ATTEMPTS
                ? "Payment is still being confirmed. Checking again..."
                : "Payment is still pending. You can retry verification."
            );

            if (attempt < MAX_VERIFICATION_ATTEMPTS) {
              await sleep(RETRY_DELAY_MS);
              continue;
            }

            setStatus("pending");
            return;
          }

          setStatus("failed");
          setMessage(
            response.data?.message ||
              "Payment could not be verified."
          );
          return;
        } catch (error) {
          if (cancelled) return;

          const detail =
            error.response?.data?.detail ||
            error.response?.data?.message ||
            error.message;

          if (
            attempt < MAX_VERIFICATION_ATTEMPTS &&
            (!error.response || error.response.status >= 500)
          ) {
            setMessage(
              "Verification is temporarily unavailable. Trying again..."
            );
            await sleep(RETRY_DELAY_MS);
            continue;
          }

          setStatus("failed");
          setMessage(
            detail ||
              "Payment verification failed. Please retry."
          );
          return;
        }
      }
    };

    verifyPayment();

    return () => {
      cancelled = true;

      if (redirectTimer) {
        window.clearTimeout(redirectTimer);
      }
    };
  }, [navigate, reference]);

  const retryVerification = () => {
    const query = new URLSearchParams();

    if (reference) {
      query.set("reference", reference);
    }

    window.location.assign(
      `/advertiser/payment-return?${query.toString()}`
    );
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center p-4">
      <div className="w-full max-w-lg rounded-2xl border border-neutral-800 bg-neutral-900 p-8 text-center shadow-2xl">
        <div className="flex justify-center mb-6">
          <CaiwaveLogo size={48} />
        </div>

        {status === "verifying" && (
          <Loader2 className="mx-auto mb-5 h-14 w-14 animate-spin text-blue-400" />
        )}

        {status === "success" && (
          <CheckCircle className="mx-auto mb-5 h-14 w-14 text-green-400" />
        )}

        {(status === "failed" || status === "pending") && (
          <AlertCircle className="mx-auto mb-5 h-14 w-14 text-amber-400" />
        )}

        <h1 className="text-2xl font-semibold">
          {status === "verifying" && "Verifying payment"}
          {status === "success" && "Payment verified"}
          {status === "pending" && "Payment pending"}
          {status === "failed" && "Verification unsuccessful"}
        </h1>

        <p className="mt-3 text-neutral-400">
          {message}
        </p>

        {reference && (
          <p className="mt-4 break-all text-xs text-neutral-600">
            Reference: {reference}
          </p>
        )}

        {status === "success" && (
          <p className="mt-5 text-sm text-neutral-500">
            Returning you to your advertiser dashboard...
          </p>
        )}

        {(status === "failed" || status === "pending") && (
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <Button
              type="button"
              onClick={retryVerification}
              className="flex-1"
              disabled={!reference}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry verification
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() =>
                navigate("/advertiser/ads", { replace: true })
              }
              className="flex-1 border-neutral-700"
            >
              Return to dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvertiserPaymentReturn;
