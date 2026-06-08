<script lang="ts">
	import { Button, Helper, Modal } from 'flowbite-svelte';
	import { BullhornSolid } from 'flowbite-svelte-icons';
	import { push_api_error, push_message } from '../messageService.svelte';
	import { createPostApiV1PostsPost, type Post, type PostWithChildren } from '../client';
	import { refreshPosts } from '../sharedState.svelte';
	import MentionTextarea from './mentionTextarea.svelte';

	let {
		open = $bindable(),
		parent,
		onposted
	}: {
		open: boolean;
		parent: Post | PostWithChildren | undefined;
		// Called after a successful post; defaults to refreshing the feed. The
		// thread view passes its own reloader so nested replies show up live.
		onposted?: () => void;
	} = $props();
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
		(onposted ?? refreshPosts)();
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
		<MentionTextarea rows={4} maxlength={500} placeholder="Was möchtest du sagen?" bind:value />
		<Helper class="text-right">{value.length} / 500</Helper>
		<Button type="submit" color="primary" class="self-end gap-2 font-bold">
			<BullhornSolid class="h-4 w-4" /> Posten!
		</Button>
	</form>
</Modal>
