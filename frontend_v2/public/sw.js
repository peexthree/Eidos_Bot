const CACHE_NAME = 'eidos-cache-v1';
const ASSETS_TO_CACHE = [
  '/video/DOLL.mp4',
  '/video/back.mp4',
  '/video/nadpis.png',
  '/video/signa.png',
  '/video/sinxr.png',
  '/video/_nul.png',
  '/video/shop.png',
  '/video/invent.png',
  '/video/dnecvnik.png',
  '/video/sindi.png',
  '/video/reiting.png',
  '/video/guid.png',
  '/video/shadow_b.png',
  '/video/admin.png',
  '/video/frame.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Cache strictly visual assets in public
  if (ASSETS_TO_CACHE.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        return cachedResponse || fetch(event.request).then(response => {
          return caches.open(CACHE_NAME).then(cache => {
             cache.put(event.request, response.clone());
             return response;
          });
        });
      })
    );
  } else {
    event.respondWith(fetch(event.request));
  }
});
