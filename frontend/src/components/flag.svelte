<script lang="ts">
	import { Button, Label, Modal, Textarea } from 'flowbite-svelte';
	import { FlagOutline } from 'flowbite-svelte-icons';
	import { flagApiV1PostsFlagPost } from '../client';
	import { push_api_error } from '../messageService.svelte';
	import { refreshPosts } from '../sharedState.svelte';

	let { open = $bindable(), post_id } = $props();

	let value = $state('');

	const handleFlag = async (e: SubmitEvent) => {
		e.preventDefault();
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

		open = false;
		refreshPosts();
	};
</script>

<Modal title="Post melden" bind:open size="sm" class="w-[calc(100%-2rem)]">
	<form onsubmit={handleFlag} class="flex flex-col gap-3">
		<div>
			<Label for="flag-reason" class="mb-1">Bitte beschreibe kurz den Grund</Label>
			<Textarea id="flag-reason" rows={3} bind:value required class="w-full resize-none" />
		</div>
		<Button type="submit" color="red" class="self-end gap-2 font-bold">
			<FlagOutline class="h-4 w-4" /> Melden!
		</Button>
	</form>
</Modal>
