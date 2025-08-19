<script lang="ts">
	import {
		Button,
		Form,
		FormGroup,
		FormText,
		Input,
		Label,
		Modal,
		ModalBody
	} from '@sveltestrap/sveltestrap';
	import { push_api_error, push_message } from '../messageService.svelte';
	import {
		getVapidPublicKeyApiV1NotifyVapidPublicKeyGet,
		initSessionApiV1UserPost,
		subscribeApiV1NotifySubscribePost
	} from '../client';

	let { isOpen = $bindable() } = $props();
	const toggle = () => (isOpen = !isOpen);

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

			if (error) {
				push_api_error(error, 'Schlüsselabfrage fehlgeschlagen!');
				return;
			}

			const sub = await reg.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: urlBase64ToUint8Array(data.publicKey)
			});

			const result = await subscribeApiV1NotifySubscribePost({
				credentials: 'include',
				body: {
					subscription: JSON.stringify(sub),
					mode: notify
				}
			});
			if (result.error) {
				push_api_error(error, 'Fehler beim Subscribe!');
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

		if (!!error) {
			push_api_error(error, 'Fehler beim Anmelden! Bitte probiere die Seite neu zu laden :)');
			return;
		}

		if (notify !== 'none') {
			enableNotifications();
		}

		push_message({ color: 'success', title: 'Hey!', message: `Willkommen ${data.name} 👋` });
		isOpen = false;
		value = '';
	};
</script>

<Modal autoFocus centered backdrop="static" header="Hallo {value.trim() || 'Du'}!" {isOpen}>
	<ModalBody>
		<Form onsubmit={handleLogin}>
			<FormGroup floating label="Bitte gib deinen Namen ein">
				<Input bind:value required />
				<FormText autofocus class="small"
					>Achtung, du kannst den Namen später nicht mehr ändern!</FormText
				>
			</FormGroup>
			<Label>Benachrichtigungen</Label>
			<Input type="radio" bind:group={notify} value="none" label="Niemals" />
			<Input
				type="radio"
				bind:group={notify}
				value="user"
				label="Bei '{value.trim() || 'du'}' im Nachrichtentext"
			/>
			<Input
				type="radio"
				bind:group={notify}
				value="all"
				label="Bei '@all' und '{value.trim() || 'du'}' im Nachrichtentext"
			/>
			<Input type="radio" bind:group={notify} value="global" label="Bei jedem neuen Post" />
			<Button class="btn-warning float-end">Los gehts!</Button>
		</Form>
	</ModalBody>
</Modal>
