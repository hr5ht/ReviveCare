// ReViveCare service worker: an offline app shell.
// Pages always come from the network (they hold patient data, so they are never cached);
// when offline, navigations get the offline page. Static assets are network-first with a cached fallback,
// so a deploy is picked up straight away and the shell still loads offline.
// Exercise demo videos and the exercise library pages (generic instructions, no health data) are kept for offline use.
const CACHE = 'revivecare-shell-v1';
const VIDEOS = 'revivecare-videos-v1';
const VIDEO_PATH = '/static/Patients/videos/';
const EXERCISE_PAGES = /^\/patient\/exercises\//;
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
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('revivecare-') && ![CACHE, VIDEOS].includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  if (request.mode === 'navigate') {
    if (EXERCISE_PAGES.test(url.pathname)) {
      event.respondWith(
        fetch(request)
          .then((response) => {
            if (response.ok && !response.redirected) {
              const copy = response.clone();
              caches.open(VIDEOS).then((cache) => cache.put(url.pathname, copy));
            }
            return response;
          })
          .catch(() => caches.match(url.pathname).then((cached) => cached || caches.match('/offline/'))),
      );
      return;
    }
    event.respondWith(fetch(request).catch(() => caches.match('/offline/')));
    return;
  }
  if (url.pathname.startsWith(VIDEO_PATH)) {
    event.respondWith(serveVideo(request, url.pathname));
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

// Video players ask for byte ranges, and a partial (206) response can't be cached. So the first play streams from
// the network while the whole file is saved in the background; later plays (and offline ones) slice the saved copy.
async function serveVideo(request, path) {
  const cache = await caches.open(VIDEOS);
  const cached = await cache.match(path);
  if (!cached) {
    fetch(path).then((full) => full.ok && cache.put(path, full)).catch(() => {});
    return fetch(request);
  }
  const range = /bytes=(\d*)-(\d*)/.exec(request.headers.get('Range') || '');
  if (!range) return cached;
  const blob = await cached.blob();
  const start = range[1] ? Number(range[1]) : Math.max(0, blob.size - Number(range[2]));
  const end = range[1] && range[2] ? Math.min(Number(range[2]), blob.size - 1) : blob.size - 1;
  return new Response(blob.slice(start, end + 1), {
    status: 206,
    headers: {
      'Content-Type': cached.headers.get('Content-Type') || 'video/mp4',
      'Content-Range': `bytes ${start}-${end}/${blob.size}`,
      'Content-Length': String(end - start + 1),
      'Accept-Ranges': 'bytes',
    },
  });
}
