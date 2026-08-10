import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import {
  BadgeDollarSign,
  BellRing,
  CheckCircle2,
  Gift,
  Megaphone,
  Radio,
  ShieldCheck,
  Trophy,
} from "lucide-react";

import { API_URL } from "../../lib/utils";

const DISMISSAL_DURATION_MS = 24 * 60 * 60 * 1000;

const getDismissalStorageKey = (hotspotId) =>
  `caiwave:web-push-dismissed:${hotspotId}`;

const hasActiveDismissal = (hotspotId) => {
  if (!hotspotId) return false;

  try {
    const storedValue = window.localStorage.getItem(
      getDismissalStorageKey(hotspotId)
    );

    if (!storedValue) return false;

    const dismissedAt = Number(storedValue);

    if (!Number.isFinite(dismissedAt)) {
      window.localStorage.removeItem(
        getDismissalStorageKey(hotspotId)
      );
      return false;
    }

    const dismissalIsActive =
      Date.now() - dismissedAt < DISMISSAL_DURATION_MS;

    if (!dismissalIsActive) {
      window.localStorage.removeItem(
        getDismissalStorageKey(hotspotId)
      );
    }

    return dismissalIsActive;
  } catch {
    return false;
  }
};

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
  navigator.serviceWorker.register("/service-worker.js", {
    scope: "/",
  });

const sendSubscription = async (subscription, hotspotId) => {
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

const notificationBenefits = [
  {
    icon: Gift,
    text: "Free WiFi offers",
    iconClassName: "bg-pink-500/20 text-pink-300",
  },
  {
    icon: BadgeDollarSign,
    text: "Discounted internet packages",
    iconClassName: "bg-emerald-500/20 text-emerald-300",
  },
  {
    icon: Megaphone,
    text: "Local announcements and campaigns",
    iconClassName: "bg-amber-500/20 text-amber-300",
  },
  {
    icon: Trophy,
    text: "Live events and CAIWAVE TV",
    iconClassName: "bg-orange-500/20 text-orange-300",
  },
  {
    icon: Radio,
    text: "Hotspot updates and service alerts",
    iconClassName: "bg-cyan-500/20 text-cyan-300",
  },
];

export default function WebPushEnrollment({
  hotspotId,
  clientMac,
  clientIp,
  onRewardGranted,
}) {
  const [configuration, setConfiguration] = useState(null);
  const [status, setStatus] = useState("loading");
  const [busy, setBusy] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [rewardStatus, setRewardStatus] = useState("idle");
  const [rewardMessage, setRewardMessage] = useState("");
  const installPromptRef = useRef(null);
  const [installAvailable, setInstallAvailable] = useState(false);
  const [appInstalled, setAppInstalled] = useState(() => isStandalone());

  useEffect(() => {
    const handleBeforeInstallPrompt = (event) => {
      event.preventDefault();
      installPromptRef.current = event;
      setInstallAvailable(true);
    };

    const handleAppInstalled = () => {
      installPromptRef.current = null;
      setInstallAvailable(false);
      setAppInstalled(true);
      setRewardMessage(
        "CAIWAVE is installed. Open the app and enable notifications to activate your free session."
      );
    };

    window.addEventListener(
      "beforeinstallprompt",
      handleBeforeInstallPrompt
    );
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const claimNotificationReward = useCallback(
    async (subscription) => {
      const serialized = subscription?.toJSON?.();

      if (!serialized?.endpoint || !hotspotId) {
        return null;
      }

      setRewardStatus("claiming");
      setRewardMessage("");

      try {
        const response = await axios.post(
          `${API_URL}/portal/notification-reward`,
          {
            endpoint: serialized.endpoint,
            hotspot_id: hotspotId,
            user_mac: clientMac || null,
            user_ip: clientIp || null,
          }
        );

        const credentials = response.data;

        if (!credentials?.username || !credentials?.password) {
          throw new Error(
            "Notification reward credentials were not returned."
          );
        }

        setRewardStatus("granted");
        setRewardMessage(
          response.data?.message ||
            "Your free WiFi session is ready."
        );

        if (typeof onRewardGranted === "function") {
          onRewardGranted(credentials);
        }

        return response.data;
      } catch (error) {
        if (error?.response?.status === 409) {
          const detail = error.response?.data?.detail;
          const message =
            typeof detail === "string"
              ? detail
              : detail?.message;

          setRewardStatus("cooldown");
          setRewardMessage(
            message ||
              "This device has already received its notification reward."
          );

          return null;
        }

        console.error(
          "Failed to claim CAIWAVE notification reward:",
          error
        );

        setRewardStatus("error");
        setRewardMessage(
          error?.response?.data?.detail?.message ||
            error?.response?.data?.detail ||
            "Notifications were enabled, but the free WiFi session could not be issued."
        );

        return null;
      }
    },
    [clientIp, clientMac, hotspotId, onRewardGranted]
  );

  useEffect(() => {
    setDismissed(hasActiveDismissal(hotspotId));
  }, [hotspotId]);

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
            await claimNotificationReward(existing);
          }

          return;
        }

        setStatus("idle");
      } catch (error) {
        console.error(
          "Failed to prepare CAIWAVE notifications:",
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
  }, [hotspotId, claimNotificationReward]);

  const installCaiwaveApp = async () => {
    const installPrompt = installPromptRef.current;

    if (!installPrompt) {
      setRewardStatus("error");
      setRewardMessage(
        "Open your browser menu and choose Install app or Add to Home screen."
      );
      return;
    }

    setBusy(true);
    setRewardMessage("Opening the CAIWAVE installation prompt…");

    try {
      await installPrompt.prompt();
      const choice = await installPrompt.userChoice;

      installPromptRef.current = null;
      setInstallAvailable(false);

      if (choice?.outcome === "accepted") {
        setAppInstalled(true);
        setRewardMessage(
          "CAIWAVE is installed. Open the app and enable notifications to activate your free session."
        );
      } else {
        setRewardMessage(
          "Install CAIWAVE when you are ready to activate your free session."
        );
      }
    } catch (error) {
      console.error("Failed to install CAIWAVE:", error);
      setRewardStatus("error");
      setRewardMessage(
        "The installation prompt could not open. Use your browser menu and choose Install app."
      );
    } finally {
      setBusy(false);
    }
  };

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

      try {
        window.localStorage.removeItem(
          getDismissalStorageKey(hotspotId)
        );
      } catch {
        // Notification enrollment must still work when storage is blocked.
      }

      setDismissed(false);
      setStatus("enabled");

      await claimNotificationReward(subscription);
    } catch (error) {
      console.error(
        "Failed to enable CAIWAVE notifications:",
        error
      );

      const details = {
        name: error?.name,
        message: error?.message,
        stack: error?.stack,
        response: error?.response?.data,
      };

      console.error(
        "CAIWAVE notification failure details:",
        details
      );

      setRewardStatus("error");
      setRewardMessage(
        details.response?.detail?.message ||
          details.response?.detail ||
          details.message ||
          "Notification setup failed."
      );

      setStatus("error");
    } finally {
      setBusy(false);
    }
  };

  const dismissPrompt = () => {
    try {
      window.localStorage.setItem(
        getDismissalStorageKey(hotspotId),
        String(Date.now())
      );
    } catch {
      // The prompt can still be dismissed for this page visit.
    }

    setDismissed(true);
  };

  if (
    status === "loading" ||
    status === "unavailable"
  ) {
    return null;
  }

  if (status === "enabled") {
    return (
      <section
        id="notifications"
        className="scroll-mt-5 overflow-hidden rounded-xl border border-emerald-400/25 bg-gradient-to-r from-emerald-950/90 via-neutral-950 to-cyan-950/80 shadow-lg shadow-emerald-950/20"
      >
        <div className="relative px-4 py-3.5 sm:px-5 sm:py-4">
          <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full bg-emerald-400/10 blur-3xl" />

          <div className="relative flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-400/15 text-emerald-300 ring-1 ring-emerald-300/20">
              <CheckCircle2 className="h-5 w-5" />
            </div>

            <div>
              <h2 className="text-base font-bold text-white">
                {rewardStatus === "granted"
                  ? "Free WiFi Session Activated"
                  : "Daily Free WiFi Activated"}
              </h2>

              <p className="mt-0.5 text-xs leading-5 text-neutral-300 sm:text-sm">
                {rewardStatus === "claiming"
                  ? "Notifications are enabled. Preparing your free WiFi session…"
                  : rewardMessage ||
                    "You will now receive free offers, announcements, live-event alerts and important CAIWAVE hotspot updates."}
              </p>

              <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-emerald-400/10 px-2.5 py-1 text-[11px] font-medium text-emerald-200">
                <ShieldCheck className="h-3.5 w-3.5" />
                {rewardStatus === "granted"
                  ? "Connecting your free WiFi session"
                  : rewardStatus === "cooldown"
                    ? "Your next free session will be available when eligible"
                    : rewardStatus === "error"
                      ? "Notifications remain enabled"
                      : "Important updates only — no spam"}
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (dismissed && (status === "idle" || status === "error")) {
    return null;
  }

  if (
    status === "install-required" ||
    status === "unsupported" ||
    status === "denied"
  ) {
    const message =
      status === "install-required"
        ? "On iPhone or iPad, add this CAIWAVE portal to your Home Screen, open it from there, then enable notifications."
        : status === "unsupported"
          ? "This WiFi sign-in window cannot install the CAIWAVE app. Start app setup, then continue in Chrome to install CAIWAVE and enable notifications."
          : "Notifications are blocked in your browser settings. You can enable them later from your browser's site settings.";

    return (
      <section
        id="notifications"
        className="scroll-mt-5 rounded-2xl border border-white/10 bg-neutral-950/90 p-5 shadow-lg"
      >
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300">
            <BellRing className="h-6 w-6" />
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-white">
              CAIWAVE Notifications
            </h2>

            <p className="mt-1 text-sm leading-6 text-neutral-400">
              {message}
            </p>

            {status === "unsupported" && (
          <p className="mt-2 text-sm leading-6 text-neutral-400">
            This browser cannot enable CAIWAVE notifications from the WiFi sign-in window.
            You can install CAIWAVE from a supported browser and enable notifications there.
          </p>
        )}

        {status !== "unsupported" && (
              <p className="mt-2 text-xs text-neutral-500">
                This does not affect WiFi access.
              </p>
            )}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section
      id="notifications"
      className="scroll-mt-5 relative overflow-hidden rounded-2xl border border-blue-300/25 bg-gradient-to-r from-blue-800 via-indigo-800 to-purple-900 shadow-xl shadow-indigo-950/40"
    >
      <div className="absolute -left-16 -top-20 h-48 w-48 rounded-full bg-cyan-300/15 blur-3xl" />
      <div className="absolute -bottom-24 -right-12 h-56 w-56 rounded-full bg-fuchsia-400/20 blur-3xl" />

      <div className="relative px-4 py-5 sm:px-6 sm:py-6">
        <div className="mx-auto flex max-w-xl flex-col items-center text-center">
          <div className="relative mb-3">
            <div className="absolute inset-0 rounded-full bg-yellow-300/30 blur-xl" />

            <div className="relative flex h-12 w-12 items-center justify-center rounded-full border border-yellow-200/30 bg-yellow-300 text-indigo-950 shadow-lg shadow-yellow-400/20">
              <BellRing className="h-6 w-6" />
            </div>
          </div>

          <h2 className="text-xl font-extrabold tracking-tight text-white sm:text-2xl">
            Install CAIWAVE App & Get Free WiFi
          </h2>

          <p className="mt-2 text-sm font-medium text-blue-100 sm:text-base">
            Be the first to know about:
          </p>

          <div className="mt-4 grid w-full gap-2 text-left sm:grid-cols-2">
            {notificationBenefits.map(
              ({ icon: Icon, text, iconClassName }) => (
                <div
                  key={text}
                  className="flex items-center gap-2.5 rounded-lg border border-white/10 bg-white/10 px-3 py-2 backdrop-blur-sm"
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>

                  <span className="text-sm font-medium text-white">
                    {text}
                  </span>
                </div>
              )
            )}
          </div>

          <p className="mt-4 text-sm leading-5 text-blue-100">
            Install CAIWAVE and enable notifications to receive a free WiFi session when eligible.
          </p>

          {status === "error" && (
            <p className="mt-3 rounded-lg border border-red-300/20 bg-red-950/30 px-3 py-2 text-xs text-red-100">
              {rewardMessage ||
                "We could not enable notifications. Please try again."}
            </p>
          )}

          <button
            type="button"
            onClick={
                !appInstalled && installAvailable
                  ? installCaiwaveApp
                  : enableNotifications
              }
            disabled={busy}
            className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-blue-950/30 transition duration-200 hover:-translate-y-0.5 hover:from-cyan-300 hover:to-blue-400 focus:outline-none focus:ring-2 focus:ring-cyan-200 focus:ring-offset-2 focus:ring-offset-indigo-900 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:min-w-64"
          >
            <BellRing className="h-5 w-5" />
            {busy
                ? !appInstalled && installAvailable
                  ? "Opening Installation…"
                  : "Preparing Free Session…"
                : !appInstalled && installAvailable
                  ? "Install CAIWAVE App"
                  : "Enable Notifications & Get Free Session"}
          </button>

          <button
            type="button"
            onClick={dismissPrompt}
            disabled={busy}
            className="mt-3 rounded-lg px-4 py-2 text-sm font-medium text-blue-100 transition hover:bg-white/10 hover:text-white disabled:opacity-60"
          >
            Maybe Later
          </button>

          <div className="mt-4 flex items-center gap-1.5 text-xs text-blue-200">
            <ShieldCheck className="h-3.5 w-3.5" />
            Optional and does not affect internet access
          </div>
        </div>
      </div>
    </section>
  );
}
