<script lang="ts">
	import { Button, Icon } from '@sveltestrap/sveltestrap';
	import { voteApiV1PostsVotePost, type Post } from '../client';
	import { all_votes, refreshPosts, refreshVotes } from '../sharedState.svelte';
	import { slide } from 'svelte/transition';
	import Flag from './flag.svelte';

	const { post }: { post: Post } = $props();

	let flagOpen = $state(false);

	const created_at_date = $derived(new Date(post.created_at!).toLocaleDateString());
	const created_at_time = $derived(new Date(post.created_at!).toLocaleTimeString());

	const voted = $derived(all_votes.val?.find((v) => v.post_id == post.id));

	const setVote = async (v: 0 | 1 | -1) => {
		console.log(post.id, v);
		await voteApiV1PostsVotePost({
			credentials: 'include',
			body: {
				post: post!.id!,
				value: v
			}
		}).catch(console.log);
		refreshVotes();
		refreshPosts();
	};

	const voteUp = async (e: Event) => {
		e.preventDefault();
		if (voted?.value === 1) {
			await setVote(0);
			return;
		}
		await setVote(1);
	};

	const voteDown = async (e: Event) => {
		e.preventDefault();
		if (voted?.value === -1) {
			await setVote(0);
			return;
		}
		await setVote(-1);
	};
</script>

<div class="card bg-success mb-2" transition:slide>
	<div class="card-body">
		<span class="d-flex w-100 justify-content-between mb-3">
			<h4 class="card-title">{post.created_by_name}</h4>
			<div class="fs-5">
				<Button onclick={voteUp} size="sm" color={voted?.value === 1 ? 'info' : 'success'}>
					<Icon name="hand-thumbs-up-fill"></Icon>
					{post.upvotes}
				</Button>
				<Button
					onclick={voteDown}
					size="sm"
					color={voted?.value === -1 ? 'info' : 'success'}
					class="ms-2"
				>
					<Icon name="hand-thumbs-down-fill"></Icon>
					{post.downvotes}
				</Button>
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
		<a
			href={null}
			onclick={() => {
				flagOpen = true;
			}}
		>
			<Icon name="flag-fill" style="color: #60a060"></Icon>
		</a>
	</div>
</div>

{#if flagOpen}
	<Flag bind:isOpen={flagOpen} post_id={post.id} />
{/if}

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
