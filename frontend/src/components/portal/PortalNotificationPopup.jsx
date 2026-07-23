import { useEffect, useRef, useState } from "react";
import axios from "axios";
import {
  BellRing,
  ExternalLink,
  X,
} from "lucide-react";

import { API_URL } from "../../lib/utils";

const storageKey = (hotspotId) =>
  `caiwave:seen-notifications:${hotspotId}`;

const readSeenNotifications = (hotspotId) => {
  try {
    const stored = JSON.parse(
      window.localStorage.getItem(storageKey(hotspotId)) || "[]"
    );
    return new Set(Array.isArray(stored) ? stored : []);
  } catch {
    return new Set();
  }
};

const rememberNotification = (hotspotId, notificationId) => {
  const seen = readSeenNotifications(hotspotId);
  seen.add(notificationId);

  try {
    window.localStorage.setItem(
      storageKey(hotspotId),
      JSON.stringify(Array.from(seen).slice(-100))
    );
  } catch {
    // Private browsing or storage restrictions must not break the portal.
  }
};

const resolveMediaUrl = (path) => {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;

  const baseUrl = API_URL.replace(/\/api\/?$/, "");
  return `${baseUrl}${path}`;
};

const sourceLabels = {
  campaign: "Campaign update",
  live_stream: "Live now",
  announcement: "CAIWAVE announcement",
  marketplace: "CAIMART offer",
};

export default function PortalNotificationPopup({
  hotspotId,
}) {
  const [notification, setNotification] = useState(null);
  const openNotificationIdRef = useRef(null);
  const memorySeenRef = useRef(new Set());

  useEffect(() => {
    if (!hotspotId) return undefined;

    let cancelled = false;
    let timerId;

    const poll = async () => {
      let nextPollSeconds = 60;

      try {
        const response = await axios.get(
          `${API_URL}/notifications/latest`,
          {
            params: {
              hotspot_id: hotspotId,
            },
          }
        );

        nextPollSeconds = Math.max(
          30,
          Number(response.data?.poll_after_seconds || 60)
        );

        const latest = response.data?.notification || null;

        if (latest?.id) {
          const persistedSeen =
            readSeenNotifications(hotspotId);
          const alreadySeen =
            persistedSeen.has(latest.id) ||
            memorySeenRef.current.has(latest.id);

          if (
            !alreadySeen &&
            openNotificationIdRef.current !== latest.id &&
            !cancelled
          ) {
            openNotificationIdRef.current = latest.id;
            setNotification(latest);
          }
        }
      } catch (error) {
        if (error.response?.status !== 404) {
          console.error(
            "Failed to poll portal notifications:",
            error
          );
        }
      }

      if (!cancelled) {
        timerId = window.setTimeout(
          poll,
          nextPollSeconds * 1000
        );
      }
    };

    poll();

    return () => {
      cancelled = true;
      window.clearTimeout(timerId);
    };
  }, [hotspotId]);

  useEffect(() => {
    if (!notification) return undefined;

    const handleEscape = (event) => {
      if (event.key === "Escape") {
        dismiss();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("keydown", handleEscape);
    };
  });

  const markAsSeen = () => {
    if (!notification?.id || !hotspotId) return;

    memorySeenRef.current.add(notification.id);
    rememberNotification(hotspotId, notification.id);
  };

  const dismiss = () => {
    markAsSeen();
    openNotificationIdRef.current = null;
    setNotification(null);
  };

  const followAction = () => {
    markAsSeen();
    openNotificationIdRef.current = null;
    setNotification(null);
  };

  if (!notification) {
    return null;
  }

  const imageUrl = resolveMediaUrl(notification.image_url);
  const sourceLabel =
    sourceLabels[notification.source_type] ||
    "CAIWAVE update";

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          dismiss();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="portal-notification-title"
        aria-describedby="portal-notification-message"
        className="relative max-h-[calc(100vh-2rem)] w-full max-w-md overflow-y-auto rounded-2xl border border-blue-400/30 bg-gradient-to-br from-blue-950 via-neutral-950 to-purple-950 shadow-2xl shadow-blue-950/60"
      >
        <button
          type="button"
          onClick={dismiss}
          aria-label="Dismiss notification"
          className="absolute right-3 top-3 z-10 flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-black/60 text-white transition hover:bg-black/80"
        >
          <X className="h-4 w-4" />
        </button>

        {imageUrl && (
          <div className="max-h-[260px] overflow-hidden bg-black/30">
            <img
              src={imageUrl}
              alt=""
              className="max-h-[260px] w-full object-contain"
            />
          </div>
        )}

        <div className="p-5">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-200">
            <BellRing className="h-3.5 w-3.5" />
            {sourceLabel}
          </div>

          <h2
            id="portal-notification-title"
            className="mt-4 text-xl font-bold text-white"
          >
            {notification.title}
          </h2>

          <p
            id="portal-notification-message"
            className="mt-2 leading-relaxed text-neutral-300"
          >
            {notification.message}
          </p>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={dismiss}
              className="rounded-lg border border-neutral-700 px-4 py-2.5 text-sm font-semibold text-neutral-300 transition hover:bg-white/5"
            >
              Not now
            </button>

            <a
              href={notification.action_path}
              onClick={followAction}
              className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500"
            >
              {notification.action_label}
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          <p className="mt-4 text-center text-xs text-neutral-500">
            This notification will only be shown once on this device.
          </p>
        </div>
      </section>
    </div>
  );
}
