<script lang="ts">
	import {
		Button,
		Form,
		FormGroup,
		FormText,
		Input,
		Modal,
		ModalBody
	} from '@sveltestrap/sveltestrap';
	import { push_api_error, push_message } from '../messageService.svelte';
	import { initSessionApiV1UserPost } from '../client';

	let { isOpen = $bindable() } = $props();
	const toggle = () => (isOpen = !isOpen);

	let value = $state('');

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
			<Button class="btn-warning float-end">Los gehts!</Button>
		</Form>
	</ModalBody>
</Modal>
