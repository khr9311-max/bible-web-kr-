const CACHE_NAME = 'wordbible-cache-v3';
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

// API 요청(/api/*)은 Service Worker의 개입 없이 100% 브라우저 네이티브 네트워크로 직접 통과!
self.addEventListener('fetch', (e) => {
    if (e.request.method !== 'GET') return;

    // API 요청은 Service Worker 가로채기 완전 제외 (안드로이드 Cache Quota 및 Reject 방지)
    if (e.request.url.includes('/api/')) {
        return;
    }

    // 정적 파일(HTML, CSS, JS)만 Network-First 처리
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

