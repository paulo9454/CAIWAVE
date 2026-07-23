self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let payload = {};

  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = {
      title: "CAIWAVE update",
      body: "Open CAIWAVE to view this update.",
    };
  }

  const title = payload.title || "CAIWAVE update";
  const options = {
    body:
      payload.body ||
      "Open CAIWAVE to view this update.",
    icon: payload.icon || "/logo-192.svg",
    badge: payload.badge || "/logo-192.svg",
    image: payload.image || undefined,
    tag: payload.tag || "caiwave:update",
    renotify: Boolean(payload.renotify),
    data: {
      url: payload.url || "/",
      notificationId:
        payload.notification_id || null,
      sourceType: payload.source_type || null,
    },
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const destination = new URL(
    event.notification.data?.url || "/",
    self.location.origin
  ).href;

  event.waitUntil(
    self.clients
      .matchAll({
        type: "window",
        includeUncontrolled: true,
      })
      .then(async (windows) => {
        for (const client of windows) {
          if (
            "navigate" in client &&
            new URL(client.url).origin ===
              self.location.origin
          ) {
            await client.navigate(destination);
            return client.focus();
          }
        }

        return self.clients.openWindow(destination);
      })
  );
});
