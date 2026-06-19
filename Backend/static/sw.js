// ReViveCare service worker: an offline app shell.
// Pages always come from the network (they hold patient data, so they are never cached);
// when offline, navigations get the offline page. Static assets are network-first with a cached fallback,
// so a deploy is picked up straight away and the shell still loads offline.
const CACHE = 'revivecare-shell-v1';
const SHELL = [
  '/offline/',
  '/static/css/app.css',
  '/static/js/lucide.min.js',
  '/static/favicon.svg',
  '/static/icons/icon-192.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('revivecare-shell-') && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/offline/')));
    return;
  }
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok && SHELL.includes(url.pathname)) {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || Response.error())),
    );
  }
});
