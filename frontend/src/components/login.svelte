<script lang="ts">
	import { Button, Helper, Input, Label, Modal, Radio } from 'flowbite-svelte';
	import { ArrowRightOutline } from 'flowbite-svelte-icons';
	import { push_api_error, push_message } from '../messageService.svelte';
	import {
		getVapidPublicKeyApiV1NotifyVapidPublicKeyGet,
		initSessionApiV1UserPost,
		subscribeApiV1NotifySubscribePost
	} from '../client';
	import { user_info } from '../sharedState.svelte';

	let { open = $bindable() } = $props();

	let notify = $state<'none' | 'global' | 'all' | 'user'>('all');
	let value = $state('');

	const isIos = () =>
		/ip(hone|ad|od)/i.test(navigator.userAgent) ||
		// iPadOS reports as "MacIntel" but has a touch screen.
		(navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

	const isStandalone = () =>
		window.matchMedia?.('(display-mode: standalone)').matches ||
		// iOS Safari exposes its own standalone flag.
		(navigator as unknown as { standalone?: boolean }).standalone === true;

	const enableNotifications = async () => {
		const supported =
			'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;

		if (!supported) {
			// Work out *why* push is unavailable and give an actionable hint, rather
			// than a blanket "not supported".
			if (!window.isSecureContext) {
				// Over plain HTTP the SW/Push APIs don't exist in any browser.
				push_message({
					color: 'danger',
					title: 'Nicht möglich',
					message: 'Benachrichtigungen brauchen eine sichere HTTPS-Verbindung.'
				});
			} else if (isIos() && !isStandalone()) {
				// iOS only exposes Web Push to an installed (Home-Screen) PWA.
				push_message({
					color: 'danger',
					title: 'Erst installieren',
					message:
						'Auf dem iPhone: über das Teilen-Menü „Zum Home-Bildschirm“ hinzufügen, dann erneut anmelden.'
				});
			} else {
				push_message({
					color: 'danger',
					title: 'Fehler!',
					message: 'Dein Browser unterstützt dieses Feature nicht :,('
				});
			}
			return;
		}

		// The worker is registered on app load (see +layout.svelte); reuse the
		// active registration here instead of registering a second time.
		const reg = await navigator.serviceWorker.ready;

		const permission = await Notification.requestPermission();
		if (permission !== 'granted') {
			push_message({
				title: 'Nicht Erlaubt!',
				message: 'Benachrichtigungen sind nicht erlaubt!',
				color: 'danger'
			});
			return;
		}
		push_message({
			title: 'Erlaubt!',
			message: 'Benachrichtigungen sind erlaubt!',
			color: 'success'
		});

		const { data, error } = await getVapidPublicKeyApiV1NotifyVapidPublicKeyGet({
			credentials: 'include'
		});

		if (error || !data) {
			push_api_error(error, 'Schlüsselabfrage fehlgeschlagen!');
			return;
		}

		const { publicKey } = data as { publicKey: string };
		const sub = await reg.pushManager.subscribe({
			userVisibleOnly: true,
			applicationServerKey: urlBase64ToUint8Array(publicKey)
		});

		const result = await subscribeApiV1NotifySubscribePost({
			credentials: 'include',
			body: {
				subscription: JSON.stringify(sub),
				mode: notify
			}
		});
		if (result.error) {
			push_api_error(result.error, 'Fehler beim Subscribe!');
		}
	};

	function urlBase64ToUint8Array(base64String: string) {
		const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
		const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
		const rawData = atob(base64);
		return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
	}

	const handleLogin = async (e: SubmitEvent) => {
		e.preventDefault();
		value = value.trim();

		if (value.length < 1) {
			push_message({ color: 'danger', title: 'Fehler!', message: 'Nutzername ist nicht gültig!' });
			return;
		}

		const { data, error } = await initSessionApiV1UserPost({
			credentials: 'include',
			body: {
				username: value
			}
		});

		if (!!error || !data) {
			push_api_error(error, 'Fehler beim Anmelden! Bitte probiere die Seite neu zu laden :)');
			return;
		}

		if (notify !== 'none') {
			enableNotifications();
		}

		// Mark the session as established so the feed/votes start loading.
		user_info.val = data;

		push_message({ color: 'success', title: 'Hey!', message: `Willkommen ${data.name} 👋` });
		open = false;
		value = '';
	};
</script>

<Modal
	title="Hallo {value.trim() || 'Du'}! 👋"
	bind:open
	dismissable={false}
	outsideclose={false}
	size="sm"
	class="w-[calc(100%-2rem)]"
>
	<form onsubmit={handleLogin} class="flex flex-col gap-4">
		<div>
			<Label for="username" class="mb-1">Bitte gib deinen Namen ein</Label>
			<Input id="username" bind:value required placeholder="Dein Name" />
			<Helper class="mt-1 text-xs">Achtung, du kannst den Namen später nicht mehr ändern!</Helper>
		</div>

		<fieldset class="flex flex-col gap-2">
			<legend class="mb-1 font-semibold text-gray-900 dark:text-white">Benachrichtigungen</legend>
			<Radio bind:group={notify} value="none">Niemals</Radio>
			<Radio bind:group={notify} value="user">
				Bei '{value.trim() || 'du'}' im Nachrichtentext
			</Radio>
			<Radio bind:group={notify} value="all">
				Bei '@all' und '{value.trim() || 'du'}' im Nachrichtentext
			</Radio>
			<Radio bind:group={notify} value="global">Bei jedem neuen Post</Radio>
		</fieldset>

		<Button type="submit" color="primary" class="self-end gap-2 font-bold">
			Los gehts! <ArrowRightOutline class="h-4 w-4" />
		</Button>
	</form>
</Modal>
