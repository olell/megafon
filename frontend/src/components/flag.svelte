<script lang="ts">
	import { Button, Form, FormGroup, Input, Modal, ModalBody } from '@sveltestrap/sveltestrap';
	import { flagApiV1PostsFlagPost } from '../client';
	import { push_api_error } from '../messageService.svelte';
	import { refreshPosts } from '../sharedState.svelte';

	let { isOpen = $bindable(), post_id } = $props();
	const toggle = () => (isOpen = !isOpen);

	let value = $state('');

	const handleFlag = async () => {
		const { error } = await flagApiV1PostsFlagPost({
			credentials: 'include',
			body: {
				notice: value,
				post: post_id
			}
		});

		if (error) {
			push_api_error(error, 'Fehler beim Speichern!');
		}

		toggle();
		refreshPosts();
	};
</script>

<Modal autoFocus centered header="Post melden" {isOpen} {toggle}>
	<ModalBody>
		<Form onsubmit={handleFlag}>
			<FormGroup floating label="Bitte beschreibe kurz den Grund">
				<Input bind:value required />
			</FormGroup>
			<Button class="btn-warning float-end">Melden!</Button>
		</Form>
	</ModalBody>
</Modal>
