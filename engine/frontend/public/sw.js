self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  return self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  // Pass-through for now
});

self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || "Notificación de Violett Pilates";
  const options = {
    body: data.body || "Tienes un nuevo aviso.",
    icon: "/favicon.svg",
    badge: "/favicon.svg",
    data: data.data || { url: "/" },
    vibrate: [100, 50, 100],
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const urlToOpen = event.notification.data.url || "/";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windowClients) => {
      let matchingClient = null;
      for (let i = 0; i < windowClients.length; i++) {
        const windowClient = windowClients[i];
        if (windowClient.url.includes(urlToOpen)) {
          matchingClient = windowClient;
          break;
        }
      }
      if (matchingClient) {
        return matchingClient.focus();
      } else {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});