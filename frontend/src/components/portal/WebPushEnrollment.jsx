import { useEffect, useState } from "react";
import axios from "axios";
import {
  BellOff,
  BellRing,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";

import { API_URL } from "../../lib/utils";


const toApplicationServerKey = (value) => {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding)
    .replace(/-/g, "+")
    .replace(/_/g, "/");
  const raw = window.atob(base64);

  return Uint8Array.from(
    [...raw].map((character) => character.charCodeAt(0))
  );
};

const isStandalone = () =>
  window.matchMedia?.("(display-mode: standalone)").matches ||
  window.navigator.standalone === true;

const isIosDevice = () =>
  /iphone|ipad|ipod/i.test(window.navigator.userAgent);

const supportsWebPush = () =>
  "serviceWorker" in navigator &&
  "PushManager" in window &&
  "Notification" in window;

const registerWorker = async () =>
  navigator.serviceWorker.register(
    "/service-worker.js",
    { scope: "/" }
  );

const sendSubscription = async (
  subscription,
  hotspotId
) => {
  const serialized = subscription.toJSON();

  await axios.post(
    `${API_URL}/notifications/push/subscribe`,
    {
      endpoint: serialized.endpoint,
      keys: {
        p256dh: serialized.keys?.p256dh,
        auth: serialized.keys?.auth,
      },
      hotspot_id: hotspotId,
      preferences: {
        campaign: true,
        live_stream: true,
        announcement: true,
        marketplace: false,
      },
    }
  );
};

export default function WebPushEnrollment({ hotspotId }) {
  const [configuration, setConfiguration] = useState(null);
  const [status, setStatus] = useState("loading");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!hotspotId) return undefined;

    let cancelled = false;

    const prepare = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/notifications/push/config`
        );
        const config = response.data || {};

        if (cancelled) return;

        setConfiguration(config);

        const manifestLink =
          document.querySelector('link[rel="manifest"]') ||
          document.createElement("link");

        manifestLink.rel = "manifest";
        manifestLink.href =
          `${API_URL}/notifications/push/manifest` +
          `?hotspot_id=${encodeURIComponent(hotspotId)}`;

        if (!manifestLink.parentNode) {
          document.head.appendChild(manifestLink);
        }

        if (!config.enabled || !config.public_key) {
          setStatus("unavailable");
          return;
        }

        if (isIosDevice() && !isStandalone()) {
          setStatus("install-required");
          return;
        }

        if (!supportsWebPush()) {
          setStatus("unsupported");
          return;
        }

        if (Notification.permission === "denied") {
          setStatus("denied");
          return;
        }

        const registration = await registerWorker();
        const existing =
          await registration.pushManager.getSubscription();

        if (cancelled) return;

        if (
          existing &&
          Notification.permission === "granted"
        ) {
          await sendSubscription(existing, hotspotId);

          if (!cancelled) {
            setStatus("enabled");
          }
          return;
        }

        setStatus("idle");
      } catch (error) {
        console.error(
          "Failed to prepare CAIWAVE updates:",
          error
        );

        if (!cancelled) {
          setStatus("error");
        }
      }
    };

    prepare();

    return () => {
      cancelled = true;
    };
  }, [hotspotId]);

  const enableNotifications = async () => {
    if (!configuration?.public_key || !hotspotId) return;

    setBusy(true);

    try {
      const permission =
        await Notification.requestPermission();

      if (permission !== "granted") {
        setStatus(
          permission === "denied" ? "denied" : "idle"
        );
        return;
      }

      const registration = await registerWorker();
      let subscription =
        await registration.pushManager.getSubscription();

      if (!subscription) {
        subscription =
          await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: toApplicationServerKey(
              configuration.public_key
            ),
          });
      }

      await sendSubscription(subscription, hotspotId);
      setStatus("enabled");
    } catch (error) {
      console.error(
        "Failed to enable CAIWAVE updates:",
        error
      );
      setStatus("error");
    } finally {
      setBusy(false);
    }
  };

  const disableNotifications = async () => {
    setBusy(true);

    try {
      const registration =
        await navigator.serviceWorker.ready;
      const subscription =
        await registration.pushManager.getSubscription();

      if (subscription) {
        await axios.delete(
          `${API_URL}/notifications/push/unsubscribe`,
          {
            data: {
              endpoint: subscription.endpoint,
            },
          }
        );
        await subscription.unsubscribe();
      }

      setStatus("idle");
    } catch (error) {
      console.error(
        "Failed to disable CAIWAVE updates:",
        error
      );
      setStatus("error");
    } finally {
      setBusy(false);
    }
  };

  if (
    status === "loading" ||
    status === "unavailable"
  ) {
    return null;
  }

  return (
    <section className="rounded-xl border border-blue-500/25 bg-gradient-to-br from-blue-950/70 via-neutral-950 to-cyan-950/40 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-blue-300">
          {status === "enabled" ? (
            <CheckCircle2 className="h-5 w-5" />
          ) : (
            <BellRing className="h-5 w-5" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-white">
            {status === "enabled"
              ? "CAIWAVE updates enabled"
              : "Never miss an important update"}
          </h2>

          {status === "enabled" ? (
            <p className="mt-1 text-sm text-neutral-400">
              You can receive targeted campaign and live-stream
              alerts. CAIWAVE limits background alerts to two per
              day.
            </p>
          ) : status === "install-required" ? (
            <p className="mt-1 text-sm text-neutral-400">
              On iPhone or iPad, add this CAIWAVE portal to your
              Home Screen, open it there, then enable updates.
            </p>
          ) : status === "unsupported" ? (
            <p className="mt-1 text-sm text-neutral-400">
              This browser cannot receive background alerts. You
              will still see updates whenever this portal is open.
            </p>
          ) : status === "denied" ? (
            <p className="mt-1 text-sm text-neutral-400">
              Notifications are blocked in your browser settings.
              Internet access and portal updates still work.
            </p>
          ) : (
            <p className="mt-1 text-sm text-neutral-400">
              Receive important campaign and CAIWAVE TV alerts.
              Permission is optional and does not affect internet
              access.
            </p>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-3">
            {(status === "idle" || status === "error") && (
              <button
                type="button"
                onClick={enableNotifications}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:opacity-60"
              >
                <BellRing className="h-4 w-4" />
                {busy ? "Enabling…" : "Enable updates"}
              </button>
            )}

            {status === "enabled" && (
              <button
                type="button"
                onClick={disableNotifications}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-lg border border-neutral-700 px-4 py-2 text-sm font-semibold text-neutral-300 transition hover:bg-white/5 disabled:opacity-60"
              >
                <BellOff className="h-4 w-4" />
                {busy ? "Disabling…" : "Turn off"}
              </button>
            )}

            <span className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
              <ShieldCheck className="h-3.5 w-3.5" />
              Optional and non-disruptive
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
