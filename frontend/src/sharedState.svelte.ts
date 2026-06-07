import { dev } from '$app/environment';
import {
	getPostsApiV1PostsGet,
	getVotesApiV1PostsVotesGet,
	type Post,
	type UserPublic,
	type Vote
} from './client';
import { push_api_error } from './messageService.svelte';

export const user_info = $state<{ val: UserPublic | null }>({ val: null });
export const admin_info = $state<{ val: boolean }>({ val: false });
export const all_posts = $state<{ val: Post[] }>({ val: [] });

export const postOrder = $state<{ val: 'newest' | 'votes' }>({ val: 'newest' });

export const refreshPosts = () =>
	getPostsApiV1PostsGet({ query: { order: postOrder.val } }).then(({ data, error }) => {
		if (error) {
			push_api_error(error, 'Fehler beim laden der Posts!');
			return;
		}
		all_posts.val = data!;
	});

export const all_votes = $state<{ val: Vote[] }>({ val: [] });

export const refreshVotes = () => {
	if (!user_info.val) return Promise.resolve();
	return getVotesApiV1PostsVotesGet({ credentials: 'include' }).then(({ data, error }) => {
		if (error) {
			push_api_error(error, 'Fehler beim laden der Votes!');
			return;
		}
		all_votes.val = data!;
	});
};

// SSE base: cross-origin to the backend in dev, same-origin in prod (matches the
// generated client's baseUrl handling). EventSource sends the `auth` cookie with
// withCredentials; the backend CORS already allows credentials.
const SSE_BASE = dev ? 'http://localhost:8000' : '';

// Open a Server-Sent Events stream that pushes new post/vote/flag events, and
// refetch (debounced) when one arrives. Returns a disconnect function.
export function connectFeedStream(): () => void {
	const es = new EventSource(`${SSE_BASE}/api/v1/posts/stream`, { withCredentials: true });
	let timer: ReturnType<typeof setTimeout> | undefined;
	const refresh = () => {
		clearTimeout(timer);
		timer = setTimeout(() => {
			refreshPosts();
			refreshVotes();
		}, 250);
	};
	es.onmessage = refresh; // default (unnamed) events
	for (const kind of ['post', 'vote', 'flag']) es.addEventListener(kind, refresh);
	return () => {
		clearTimeout(timer);
		es.close();
	};
}
