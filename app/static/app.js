const CACHE_NAME = 'static-cache-v1.2';
 
const FILES_TO_CACHE = [
'/static/offline.html',
];

/* Progressive Web App Register Service Worker */
if ('serviceWorker' in navigator) {
    navigator.serviceWorker
    // .register('{{url_for("static",filename="service-worker.js")}}')
    .register('/service-worker.js')
    .then(function(registration) {
        console.log('Service Worker Registered!');
        return registration;
    })
    .catch(function(err) {
        console.error('Unable to register service worker.', err);
    });
}