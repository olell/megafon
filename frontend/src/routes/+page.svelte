<script lang="ts">
	import { Button, Icon } from '@sveltestrap/sveltestrap';
	import { getPostsApiV1PostsGet, type Post } from '../client';
	import CreatePost from '../components/createPost.svelte';
	import PostComponent from '../components/post.svelte';
	import { all_posts, refreshPosts } from '../sharedState.svelte';

	let createPostOpen = $state(false);

	$effect(refreshPosts);
	$effect(() => {
		const interval = setInterval(refreshPosts, 10000);
		return () => {
			clearInterval(interval);
		};
	});
</script>

<CreatePost bind:isOpen={createPostOpen} parent={null} />

<div style="padding-bottom: 100px;">
	{#each all_posts.val as post (post.id)}
		<PostComponent {post} />
	{/each}
</div>

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
