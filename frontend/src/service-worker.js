self.addEventListener('push', (event) => {
	const data = event.data?.text() || 'New notification';
	event.waitUntil(
		self.registration.showNotification('New message!', {
			body: data,
			icon: '/icon.png'
		})
	);
});
