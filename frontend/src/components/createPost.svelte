<script lang="ts">
	import { Button, Helper, Modal, Textarea } from 'flowbite-svelte';
	import { BullhornSolid } from 'flowbite-svelte-icons';
	import { push_api_error, push_message } from '../messageService.svelte';
	import { createPostApiV1PostsPost, type Post, type PostWithChildren } from '../client';
	import { refreshPosts } from '../sharedState.svelte';

	let {
		open = $bindable(),
		parent
	}: { open: boolean; parent: Post | PostWithChildren | undefined } = $props();
	let value = $state('');

	$effect(() => {
		if (open && parent) {
			value = `@${parent.created_by_name} `;
		} else {
			value = '';
		}
	});

	const handlePost = async (e: SubmitEvent) => {
		e.preventDefault();
		value = value.trim();
		if (value.length < 5) {
			push_message({ color: 'danger', title: 'Fehler!', message: 'Nachricht zu kurz!' });
			return;
		}
		if (value.length > 500) {
			push_message({
				color: 'danger',
				title: 'Fehler!',
				message: 'Nachricht zu lang!'
			});
			return;
		}

		const { error } = await createPostApiV1PostsPost({
			credentials: 'include',
			body: {
				parent: parent?.id,
				content: value
			}
		});

		if (error) {
			push_api_error(error, 'Fehler beim erstellen des Posts!');
			return;
		}

		open = false;
		value = '';
		refreshPosts();
	};
</script>

<Modal
	title="Neuer {parent ? 'Kommentar' : 'Post'}"
	bind:open
	outsideclose={false}
	size="sm"
	class="w-[calc(100%-2rem)]"
>
	<form onsubmit={handlePost} class="flex flex-col gap-3">
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
			<BullhornSolid class="h-4 w-4" /> Posten!
		</Button>
	</form>
</Modal>
