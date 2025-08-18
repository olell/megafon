<script lang="ts">
	import { Icon } from '@sveltestrap/sveltestrap';
	import type { Post } from '../client';

	const { post }: { post: Post } = $props();

	const created_at_date = $derived(new Date(post.created_at!).toLocaleDateString());
	const created_at_time = $derived(new Date(post.created_at!).toLocaleTimeString());
</script>

<div class="card bg-success mb-2">
	<div class="card-body">
		<span class="d-flex w-100 justify-content-between">
			<h4 class="card-title">{post.created_by_name}</h4>
			<div class="fs-5">
				<Icon name="heart-fill"></Icon>
				{post.upvotes}
				<Icon name="heartbreak-fill" class="ms-4 text-danger"></Icon>
				{post.downvotes}
			</div>
		</span>
		<h6 class="card-subtitle mb-2 text-muted">
			<Icon name="calendar3" class="me-1" />
			{created_at_date}
			<Icon name="clock" class="ms-3 me-1" />
			{created_at_time}
			<Icon name="chat-left-dots" class="ms-3 me-1" />
			{post.children_count}
		</h6>
		<p class="card-text post-content">
			{post.content}
		</p>
	</div>
</div>

<style>
	.post-content {
		text-align: justify;
		overflow: hidden;
		text-overflow: ellipsis;
		display: -webkit-box;
		-webkit-line-clamp: 5;
		line-clamp: 4;
		-webkit-box-orient: vertical;
	}
</style>
