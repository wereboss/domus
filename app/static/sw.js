const CACHE_NAME = "domus-v2";
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
  console.log("[ServiceWorker] Installing version:", CACHE_NAME);
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  console.log("[ServiceWorker] Activating version:", CACHE_NAME);
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[ServiceWorker] Removing obsolete cache:", key);
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

  const url = new URL(event.request.url);

  // Network-first for navigation / HTML documents (offline fallback to cache)
  if (event.request.mode === "navigate" || url.pathname === "/") {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return networkResponse;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Network-first strategy for APIs, cache fallback for assets
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
