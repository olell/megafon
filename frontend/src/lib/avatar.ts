import { dev } from '$app/environment';
import { theme } from '$lib/theme.svelte';

// Cross-origin to the backend in dev, same-origin in prod — mirrors the SSE
// base in sharedState. Avatars are plain <img> tags hitting the public,
// immutably-cached /user/avatar endpoint.
const AVATAR_BASE = dev ? 'http://localhost:8000' : '';

/** URL of the deterministic identicon for a user. Prefers the stable user id
 *  (unique per account); falls back to the name, then a constant for anon.
 *  Reads `theme.dark` so the colours follow light/dark mode (the <img> refetches
 *  the dark/light variant when the theme is toggled). */
export const avatarUrl = (seed: string | null | undefined, name?: string | null) =>
	`${AVATAR_BASE}/api/v1/user/avatar/${encodeURIComponent(seed || name || 'anon')}` +
	`?theme=${theme.dark ? 'dark' : 'light'}`;
