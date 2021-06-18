const CACHE_NAME = 'static-cache';

const FILES_TO_CACHE = [
  '/static/offline.html',
];

self.addEventListener('install', (evt) => {
    console.log('[ServiceWorker] Install');
    evt.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[ServiceWorker] Pre-caching offline page');
        return cache.addAll(FILES_TO_CACHE);
      })
    );
  
    self.skipWaiting();
  });