<script lang="ts">
	import { getPostsApiV1PostsGet, type Post } from '../client';
	import PostComponent from '../components/post.svelte';

	let posts = $state<Post[]>([]);

	$effect(() => {
		getPostsApiV1PostsGet({ query: { order: 'newest' } }).then(({ data, error }) => {
			if (!!error) {
				// handle TODO
			}
			posts = data!;
		});
	});
</script>

{#each posts as post (post.id)}
	<PostComponent {post} />
{/each}
