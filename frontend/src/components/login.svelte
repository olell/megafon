<script lang="ts">
	import { Button, Helper, Input, Label, Modal, Radio } from 'flowbite-svelte';
	import { ArrowRightOutline } from 'flowbite-svelte-icons';
	import { push_api_error, push_message } from '../messageService.svelte';
	import {
		getVapidPublicKeyApiV1NotifyVapidPublicKeyGet,
		initSessionApiV1UserPost,
		subscribeApiV1NotifySubscribePost
	} from '../client';

	let { open = $bindable() } = $props();

	let notify = $state<'none' | 'global' | 'all' | 'user'>('all');
	let value = $state('');

	const enableNotifications = async () => {
		if ('serviceWorker' in navigator && 'PushManager' in window) {
			const reg = await navigator.serviceWorker.register('/app/service-worker.js');

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
		} else {
			push_message({
				color: 'danger',
				title: 'Fehler!',
				message: 'Dein Browser unterstütz dieses Feature nicht :,('
			});
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
