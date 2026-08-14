const CACHE_NAME = 'wordbible-cache-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/style.css',
    '/js/app.js',
    '/js/reader.js',
    '/js/navigator.js',
    '/js/strong.js',
    '/js/cross_ref.js',
    '/js/card_generator.js',
    '/js/reading_tracker.js',
    '/js/search.js',
    '/manifest.json'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
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

self.addEventListener('fetch', (e) => {
    // API 요청은 네트워크 우선
    if (e.request.url.includes('/api/')) {
        e.respondWith(
            fetch(e.request).catch(() => {
                return caches.match(e.request);
            })
        );
    } else {
        // 정적 에셋은 캐시 우선
        e.respondWith(
            caches.match(e.request).then((res) => {
                return res || fetch(e.request);
            })
        );
    }
});
