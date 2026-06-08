<script lang="ts">
	import {
		voteApiV1PostsVotePost,
		deletePostApiV1PostsPostIdDelete,
		type Post,
		type PostWithChildren
	} from '../client';
	import { all_votes, refreshPosts, refreshVotes, user_info } from '../sharedState.svelte';
	import { push_api_error } from '../messageService.svelte';
	import { scale } from 'svelte/transition';
	import {
		AnnotationOutline,
		CalendarMonthOutline,
		ChevronDownOutline,
		ChevronUpOutline,
		ClockOutline,
		EditOutline,
		FlagOutline,
		ThumbsDownOutline,
		ThumbsDownSolid,
		ThumbsUpOutline,
		ThumbsUpSolid,
		TrashBinOutline
	} from 'flowbite-svelte-icons';
	import Flag from './flag.svelte';
	import EditPost from './editPost.svelte';
	import { base } from '$app/paths';
	import { avatarUrl } from '$lib/avatar';

	const {
		post,
		isParent = false,
		onchange,
		ondelete,
		showPreview = false
	}: {
		post: Post | PostWithChildren;
		isParent?: boolean;
		// Called after a successful edit (reload in place).
		onchange?: () => void;
		// Called after a successful delete; defaults to `onchange`.
		ondelete?: () => void;
		// Feed only: show a flush, collapsible preview of the top replies.
		showPreview?: boolean;
	} = $props();

	let flagOpen = $state(false);
	let editOpen = $state(false);
	let previewOpen = $state(true);

	// The feed payload (Post) carries `top_comments`; the thread tree does not.
	const topComments = $derived(
		showPreview ? (('top_comments' in post && post.top_comments) || []) : []
	);
	const hasPreview = $derived(topComments.length > 0);

	const isOwner = $derived(!!user_info.val && post.created_by_id === user_info.val.id);

	const handleDelete = async () => {
		if (!confirm('Beitrag und alle Kommentare wirklich löschen?')) return;
		const { error } = await deletePostApiV1PostsPostIdDelete({
			credentials: 'include',
			path: { post_id: post.id! }
		});
		if (error) {
			push_api_error(error, 'Fehler beim Löschen des Posts!');
			return;
		}
		(ondelete ?? onchange)?.();
	};
	// Brief "pop" animation key, bumped on each successful vote.
	let popUp = $state(false);
	let popDown = $state(false);

	const created_at_date = $derived(new Date(post.created_at!).toLocaleDateString());
	const created_at_time = $derived(new Date(post.created_at!).toLocaleTimeString());

	const voted = $derived(all_votes.val?.find((v) => v.post_id == post.id));

	const setVote = async (v: 0 | 1 | -1) => {
		await voteApiV1PostsVotePost({
			credentials: 'include',
			body: {
				post: post!.id!,
				value: v
			}
		}).catch(() => {});
		refreshVotes();
		refreshPosts();
		// In a thread `onchange` reloads the tree so nested vote counts update
		// immediately (the feed's are covered by refreshPosts above).
		onchange?.();
	};

	const voteUp = async (e: Event) => {
		e.preventDefault();
		popUp = true;
		setTimeout(() => (popUp = false), 350);
		if (voted?.value === 1) {
			await setVote(0);
			return;
		}
		await setVote(1);
	};

	const voteDown = async (e: Event) => {
		e.preventDefault();
		popDown = true;
		setTimeout(() => (popDown = false), 350);
		if (voted?.value === -1) {
			await setVote(0);
			return;
		}
		await setVote(-1);
	};
</script>

<div
	transition:scale={{ start: 0.96, duration: 200 }}
	class="{hasPreview ? 'mb-0 rounded-b-none' : 'mb-3'}
		rounded-card border bg-white/85 p-4 shadow-pop backdrop-blur-sm transition-transform duration-200 hover:-translate-y-0.5 dark:bg-gray-800/85 dark:text-gray-100
		{isParent
		? 'border-primary-300 ring-2 ring-primary-200/60 dark:border-primary-700 dark:ring-primary-900/60'
		: 'border-secondary-200 dark:border-secondary-900/70'}"
>
	<div class="mb-3 flex w-full items-start justify-between gap-3">
		<div class="flex min-w-0 items-center gap-2">
			<img
				src={avatarUrl(post.created_by_id, post.created_by_name)}
				alt=""
				width="36"
				height="36"
				class="h-9 w-9 shrink-0 rounded-full bg-gray-100 dark:bg-gray-700"
			/>
			<h4 class="truncate text-lg font-bold break-words text-primary-700 dark:text-primary-300">
				{post.created_by_name}
			</h4>
		</div>
		<div class="flex shrink-0 items-center gap-2">
			<button
				type="button"
				onclick={voteUp}
				aria-label="Hochstimmen"
				class="flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-semibold transition-all duration-150 active:scale-90
					{voted?.value === 1
					? 'bg-green-500 text-white shadow'
					: 'bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-700 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-green-900/50'}"
			>
				{#if voted?.value === 1}
					<ThumbsUpSolid class="h-4 w-4" />
				{:else}
					<ThumbsUpOutline class="h-4 w-4" />
				{/if}
				<span class:animate-vote-pop={popUp}>{post.upvotes}</span>
			</button>
			<button
				type="button"
				onclick={voteDown}
				aria-label="Runterstimmen"
				class="flex items-center gap-1 rounded-full px-3 py-1.5 text-sm font-semibold transition-all duration-150 active:scale-90
					{voted?.value === -1
					? 'bg-red-500 text-white shadow'
					: 'bg-gray-100 text-gray-600 hover:bg-red-100 hover:text-red-700 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-red-900/50'}"
			>
				{#if voted?.value === -1}
					<ThumbsDownSolid class="h-4 w-4" />
				{:else}
					<ThumbsDownOutline class="h-4 w-4" />
				{/if}
				<span class:animate-vote-pop={popDown}>{post.downvotes}</span>
			</button>
		</div>
	</div>

	<div
		class="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400"
	>
		<span class="flex items-center gap-1">
			<CalendarMonthOutline class="h-4 w-4" />{created_at_date}
		</span>
		<span class="flex items-center gap-1">
			<ClockOutline class="h-4 w-4" />{created_at_time}
		</span>
		<span class="flex items-center gap-1">
			<AnnotationOutline class="h-4 w-4" />{post.children_count}
		</span>
		{#if post.edited_at}
			<span class="italic">(bearbeitet)</span>
		{/if}
	</div>

	<p
		class="line-clamp-5 text-justify break-words whitespace-pre-line text-gray-800 dark:text-gray-200"
	>
		{post.content}
	</p>

	<div class="mt-3 flex items-center justify-between">
		<div class="flex items-center gap-1">
			<button
				type="button"
				aria-label="Post melden"
				class="rounded-full p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/40"
				onclick={() => {
					flagOpen = true;
				}}
			>
				<FlagOutline class="h-4 w-4" />
			</button>
			{#if isOwner}
				<button
					type="button"
					aria-label="Beitrag bearbeiten"
					class="rounded-full p-1.5 text-gray-400 transition-colors hover:bg-primary-50 hover:text-primary-600 dark:hover:bg-primary-900/40"
					onclick={() => {
						editOpen = true;
					}}
				>
					<EditOutline class="h-4 w-4" />
				</button>
				<button
					type="button"
					aria-label="Beitrag löschen"
					class="rounded-full p-1.5 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/40"
					onclick={handleDelete}
				>
					<TrashBinOutline class="h-4 w-4" />
				</button>
			{/if}
		</div>
		{#if !isParent}
			<a
				href="{base}/post/{post.id}"
				class="inline-flex items-center gap-1 rounded-full bg-secondary-100 px-3 py-1 text-sm font-semibold text-secondary-700 transition-colors hover:bg-secondary-200 dark:bg-secondary-900/50 dark:text-secondary-300"
			>
				<AnnotationOutline class="h-4 w-4" /> Kommentare
			</a>
		{/if}
	</div>
</div>

{#if hasPreview}
	<div
		class="mb-3 rounded-b-card border border-t-0 bg-white/70 backdrop-blur-sm dark:bg-gray-800/70
			{isParent
			? 'border-primary-300 dark:border-primary-700'
			: 'border-secondary-200 dark:border-secondary-900/70'}"
	>
		<button
			type="button"
			onclick={() => (previewOpen = !previewOpen)}
			class="flex w-full items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-gray-500 transition-colors hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-300"
		>
			<AnnotationOutline class="h-3.5 w-3.5" />
			Top-Kommentare
			{#if previewOpen}
				<ChevronUpOutline class="ml-auto h-3.5 w-3.5" />
			{:else}
				<ChevronDownOutline class="ml-auto h-3.5 w-3.5" />
			{/if}
		</button>
		{#if previewOpen}
			<ul class="divide-y divide-gray-100 dark:divide-gray-700">
				{#each topComments as comment (comment.id)}
					<li>
						<a
							href="{base}/post/{post.id}"
							class="flex items-center gap-2 px-4 py-1.5 text-xs transition-colors hover:bg-primary-50/60 dark:hover:bg-primary-900/20"
						>
							<img
								src={avatarUrl(comment.created_by_id, comment.created_by_name)}
								alt=""
								width="20"
								height="20"
								class="h-5 w-5 shrink-0 rounded-full bg-gray-100 dark:bg-gray-700"
							/>
							<span class="shrink-0 font-semibold text-primary-700 dark:text-primary-300">
								{comment.created_by_name}
							</span>
							<span class="truncate text-gray-600 dark:text-gray-300">{comment.content}</span>
							<span class="ml-auto shrink-0 font-semibold text-gray-400 dark:text-gray-500">
								{comment.upvotes - comment.downvotes > 0 ? '+' : ''}{comment.upvotes -
									comment.downvotes}
							</span>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
{/if}

{#if flagOpen}
	<Flag bind:open={flagOpen} post_id={post.id} />
{/if}

{#if editOpen}
	<EditPost bind:open={editOpen} {post} {onchange} />
{/if}
