<script lang="ts">
	import { Button, Icon } from '@sveltestrap/sveltestrap';
	import { getPostsApiV1PostsGet, type Post } from '../client';
	import CreatePost from '../components/createPost.svelte';
	import PostComponent from '../components/post.svelte';

	let createPostOpen = $state(false);

	let posts = $state<Post[]>([]);

	const refreshPosts = () => {
		getPostsApiV1PostsGet({ query: { order: 'newest' } }).then(({ data, error }) => {
			if (!!error) {
				// handle TODO
			}
			posts = data!;
		});
	};
	$effect(refreshPosts);
</script>

<CreatePost {refreshPosts} bind:isOpen={createPostOpen} parent={null} />

{#each posts as post (post.id)}
	<PostComponent {post} />
{/each}

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
