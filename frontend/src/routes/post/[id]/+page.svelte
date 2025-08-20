<script lang="ts">
	import { Button, Icon } from '@sveltestrap/sveltestrap';
	import {
		getPostApiV1PostsInfoPostIdGet,
		getPostsApiV1PostsGet,
		type PostWithChildren,
		type Post
	} from '../../../client';
	import CreatePost from '../../../components/createPost.svelte';
	import PostComponent from '../../../components/post.svelte';
	import { all_posts, refreshPosts, refreshVotes } from '../../../sharedState.svelte';
	import { page } from '$app/state';
	import { push_api_error } from '../../../messageService.svelte';

	let createPostOpen = $state(false);

	let id = $derived(page.params.id);

	let parent = $state<PostWithChildren>();

	$effect(refreshPosts);
	$effect(() => {
		if (all_posts.val.length) {
			refreshVotes();
		}
	});

	$effect(() => {
		if (id === 'top' || !id) {
			const interval = setInterval(refreshPosts, 10000);
			return () => {
				clearInterval(interval);
			};
		} else {
			if (all_posts.val.length) {
				getPostApiV1PostsInfoPostIdGet({ credentials: 'include', path: { post_id: id! } }).then(
					({ data, error }) => {
						if (error) {
							push_api_error(error, 'Fehler beim laden des Posts!');
							return;
						}
						parent = data!;
					}
				);
			}
		}
	});
</script>

<CreatePost bind:isOpen={createPostOpen} {parent} />

{#if parent}
	<div class="mb-3 fs-5">
		{#if parent.parent_id}
			<a href="/app/post/{parent.parent_id}" class="text-decoration-none"
				><Icon name="arrow-left-circle-fill"></Icon> Zurück</a
			>
		{:else}
			<a href="/" class="text-decoration-none"
				><Icon name="arrow-left-circle-fill"></Icon> Zur Startseite</a
			>
		{/if}
	</div>
	<PostComponent post={parent} isParent={true} />

	<div style="padding-bottom: 100px;">
		{#each parent?.children as post (post.id)}
			<PostComponent {post} isParent={false} />
		{/each}
	</div>
{:else}
	<div style="padding-bottom: 100px;">
		{#each all_posts.val as post (post.id)}
			<PostComponent {post} isParent={false} />
		{/each}
	</div>
{/if}

<Button color="warning" class="fs-4 fab" onclick={() => (createPostOpen = true)}>
	<Icon name="chat-square-text-fill"></Icon>
</Button>

<style>
	:global(.fab) {
		right: 5vw;
		bottom: 5vw;
		position: fixed;
		z-index: 800;
	}
</style>
