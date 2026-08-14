const CACHE_NAME = 'wordbible-cache-v2';
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

// Network-First 전략: 항상 최신 배포 코드를 가져오고, 오프라인일 때만 캐시를 사용
self.addEventListener('fetch', (e) => {
    if (e.request.method !== 'GET') return;

    e.respondWith(
        fetch(e.request)
            .then((networkRes) => {
                if (networkRes && networkRes.status === 200 && e.request.url.startsWith(self.location.origin)) {
                    const resClone = networkRes.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(e.request, resClone);
                    });
                }
                return networkRes;
            })
            .catch(() => {
                return caches.match(e.request);
            })
    );
});

