import { getPostsApiV1PostsGet, type Post, type User, type Vote } from './client';

export const user_info = $state<{ val: User | null }>({ val: null });
export const all_posts = $state<{ val: Post[] }>({ val: [] });

export const refreshPosts = () => {
	getPostsApiV1PostsGet({ query: { order: 'newest' } }).then(({ data, error }) => {
		if (error) {
			// handle TODO
		}
		all_posts.val = data!;
	});
};
