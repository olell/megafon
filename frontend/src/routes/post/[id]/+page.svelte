<script lang="ts">
	import { ArrowLeftOutline, EditOutline, MessageDotsOutline } from 'flowbite-svelte-icons';
	import { getPostApiV1PostsInfoPostIdGet, type PostWithChildren } from '../../../client';
	import CreatePost from '../../../components/createPost.svelte';
	import PostComponent from '../../../components/post.svelte';
	import PullToRefresh from '../../../components/pullToRefresh.svelte';
	import {
		all_posts,
		connectFeedStream,
		refreshPosts,
		refreshVotes,
		user_info
	} from '../../../sharedState.svelte';
	import { page } from '$app/state';
	import { push_api_error } from '../../../messageService.svelte';
	import { base } from '$app/paths';

	let createPostOpen = $state(false);

	let id = $derived(page.params.id);

	let parent = $state<PostWithChildren>();

	const loadThread = (postId: string) =>
		getPostApiV1PostsInfoPostIdGet({ credentials: 'include', path: { post_id: postId } }).then(
			({ data, error }) => {
				if (error) {
					push_api_error(error, 'Fehler beim laden des Posts!');
					return;
				}
				parent = data!;
			}
		);

	// Manual refresh (pull-to-refresh): reload whatever this view shows.
	const doRefresh = async () => {
		if (!user_info.val) return;
		if (id === 'top' || !id) {
			await Promise.all([refreshPosts(), refreshVotes()]);
		} else {
			await Promise.all([loadThread(id), refreshVotes()]);
		}
	};

	// All feed/thread data requires an authenticated session. Hold off until the
	// user has a session (returning user via cookie, or after entering a name) so
	// we don't fire requests that 403 and surface "not authenticated" on load.
	$effect(() => {
		if (user_info.val) {
			refreshPosts();
		}
	});
	$effect(() => {
		if (all_posts.val.length) {
			refreshVotes();
		}
	});

	$effect(() => {
		if (!user_info.val) return;
		if (id === 'top' || !id) {
			// Live updates via SSE; the slow poll is just a fallback in case the
			// stream drops silently (proxy timeout, device sleep/wake).
			const disconnect = connectFeedStream();
			const fallback = setInterval(refreshPosts, 60000);
			return () => {
				disconnect();
				clearInterval(fallback);
			};
		} else {
			loadThread(id);
		}
	});
</script>

<CreatePost bind:open={createPostOpen} {parent} />

<PullToRefresh onrefresh={doRefresh}>
	{#if parent}
		<div class="mb-4">
			{#if parent.parent_id}
				<a
					href="{base}/post/{parent.parent_id}"
					class="inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1.5 text-sm font-semibold text-primary-700 shadow-sm transition-colors hover:bg-white dark:bg-gray-800/70 dark:text-primary-300"
				>
					<ArrowLeftOutline class="h-4 w-4" /> Zurück
				</a>
			{:else}
				<a
					href="{base}/"
					class="inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1.5 text-sm font-semibold text-primary-700 shadow-sm transition-colors hover:bg-white dark:bg-gray-800/70 dark:text-primary-300"
				>
					<ArrowLeftOutline class="h-4 w-4" /> Zur Startseite
				</a>
			{/if}
		</div>
		<PostComponent post={parent} isParent={true} />

		<div>
			{#each parent.children ?? [] as post (post.id)}
				<PostComponent {post} isParent={false} />
			{/each}
		</div>
	{:else if all_posts.val.length}
		<div>
			{#each all_posts.val as post (post.id)}
				<PostComponent {post} isParent={false} />
			{/each}
		</div>
	{:else}
		<div
			class="flex flex-col items-center gap-3 py-20 text-center text-gray-500 dark:text-gray-400"
		>
			<MessageDotsOutline class="h-14 w-14 text-primary-300" />
			<p class="text-lg font-semibold">Noch nichts los hier …</p>
			<p class="text-sm">Sei der Erste und schreib etwas! 🎉</p>
		</div>
	{/if}
</PullToRefresh>

<button
	type="button"
	aria-label="Neuer Beitrag"
	class="fixed right-[5vw] bottom-[5vw] z-40 flex h-14 w-14 items-center justify-center rounded-full bg-secondary-200 text-secondary-700 shadow-pop transition-transform hover:scale-110 hover:bg-secondary-300 active:scale-95 dark:bg-secondary-900 dark:text-secondary-200"
	onclick={() => (createPostOpen = true)}
>
	<EditOutline class="h-6 w-6" />
</button>
