import {
	getPostsApiV1PostsGet,
	getVotesApiV1PostsVotesGet,
	type Post,
	type User,
	type Vote
} from './client';
import { push_api_error } from './messageService.svelte';

export const user_info = $state<{ val: User | null }>({ val: null });
export const all_posts = $state<{ val: Post[] }>({ val: [] });

export const postOrder = $state<{ val: 'newest' | 'votes' }>({ val: 'newest' });

export const refreshPosts = () => {
	getPostsApiV1PostsGet({ query: { order: postOrder.val } }).then(({ data, error }) => {
		if (error) {
			push_api_error(error, 'Fehler beim laden der Posts!');
		}
		all_posts.val = data!;
	});
};

export const all_votes = $state<{ val: Vote[] }>({ val: [] });

export const refreshVotes = () => {
	if (user_info.val) {
		getVotesApiV1PostsVotesGet({ credentials: 'include' }).then(({ data, error }) => {
			if (error) {
				push_api_error(error, 'Fehler beim laden der Votes!');
			}
			all_votes.val = data!;
		});
	}
};
