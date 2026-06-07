<script lang="ts">
	import { Button, Helper, Modal, Textarea } from 'flowbite-svelte';
	import { BullhornSolid } from 'flowbite-svelte-icons';
	import { push_api_error, push_message } from '../messageService.svelte';
	import { editPostApiV1PostsPostIdPut, type Post, type PostWithChildren } from '../client';

	let {
		open = $bindable(),
		post,
		onchange
	}: {
		open: boolean;
		post: Post | PostWithChildren;
		onchange?: () => void;
	} = $props();

	let value = $state('');

	// Seed the textarea with the current content each time the modal opens.
	$effect(() => {
		if (open) {
			value = post.content;
		}
	});

	const handleEdit = async (e: SubmitEvent) => {
		e.preventDefault();
		value = value.trim();
		if (value.length < 5) {
			push_message({ color: 'danger', title: 'Fehler!', message: 'Nachricht zu kurz!' });
			return;
		}
		if (value.length > 500) {
			push_message({ color: 'danger', title: 'Fehler!', message: 'Nachricht zu lang!' });
			return;
		}

		const { error } = await editPostApiV1PostsPostIdPut({
			credentials: 'include',
			path: { post_id: post.id! },
			body: { content: value }
		});

		if (error) {
			push_api_error(error, 'Fehler beim Bearbeiten des Posts!');
			return;
		}

		open = false;
		onchange?.();
	};
</script>

<Modal title="Beitrag bearbeiten" bind:open outsideclose={false} size="sm" class="w-[calc(100%-2rem)]">
	<form onsubmit={handleEdit} class="flex flex-col gap-3">
		<Textarea
			rows={4}
			maxlength={500}
			placeholder="Was möchtest du sagen?"
			bind:value
			required
			class="w-full resize-none"
		/>
		<Helper class="text-right">{value.length} / 500</Helper>
		<Button type="submit" color="primary" class="self-end gap-2 font-bold">
			<BullhornSolid class="h-4 w-4" /> Speichern
		</Button>
	</form>
</Modal>
