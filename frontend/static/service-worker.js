const CACHE = 'megafon-v1';

self.addEventListener('install', () => {
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const req = event.request;
	if (req.method !== 'GET') return;

	const url = new URL(req.url);
	// Leave cross-origin requests alone.
	if (url.origin !== self.location.origin) return;
	// Never cache API calls — the feed/votes must stay live.
	if (url.pathname.startsWith('/api/')) return;

	// Network-first for the app shell/static assets, falling back to the cached
	// copy when offline so the installed PWA still loads.
	event.respondWith(
		fetch(req)
			.then((res) => {
				if (res.ok) {
					const copy = res.clone();
					caches.open(CACHE).then((cache) => cache.put(req, copy));
				}
				return res;
			})
			.catch(() => caches.match(req))
	);
});

self.addEventListener('push', (event) => {
	const data = event.data?.text() || 'Neue Nachricht!';
	event.waitUntil(
		self.registration.showNotification('Neue Nachricht - MEGAFON!', {
			body: data,
			icon: '/app/icon-192.png',
			badge: '/app/icon-192.png'
		})
	);
});

self.addEventListener('pushsubscriptionchange', (event) => {
	// The browser rotated the push subscription. Re-subscribe with the previous
	// server key so notifications keep arriving; the app re-sends the mode on its
	// next open via the normal subscribe flow.
	const applicationServerKey = event.oldSubscription?.options?.applicationServerKey;
	if (!applicationServerKey) return;
	event.waitUntil(
		self.registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey }).catch(
			() => {}
		)
	);
});
