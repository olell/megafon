import type { User } from './client';

export const user_info = $state<{ val: User | null }>({ val: null });
