self.addEventListener('push', (event) => {
	const data = event.data?.text() || 'Neue Nachricht!';
	event.waitUntil(
		self.registration.showNotification('Neue Nachricht - MEGAFON!', {
			body: data,
			icon: '/app/favicon.svg'
		})
	);
});
