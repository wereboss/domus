const CACHE_NAME = "domus-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/manifest.json",
  "/static/vendor/pico.min.css",
  "/static/vendor/alpine.min.js",
  "/static/vendor/dexie.min.js",
  "/static/css/app.css",
  "/static/js/db.js",
  "/static/js/api.js",
  "/static/js/app.js",
  "/static/icons/icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Pass through non-GET requests directly
  if (event.request.method !== "GET") {
    return;
  }

  // Network-first strategy for APIs, cache fallback for assets
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() => {
        // Return 503 so client-side Dexie.js interceptor handles offline data
        return new Response(JSON.stringify({ offline: true }), {
          status: 503,
          headers: { "Content-Type": "application/json" }
        });
      })
    );
  } else {
    // Cache-first strategy for app shell assets
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        return (
          cachedResponse ||
          fetch(event.request).then((networkResponse) => {
            if (networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseClone);
              });
            }
            return networkResponse;
          })
        );
      })
    );
  }
});
