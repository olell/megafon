<script lang="ts">
	import { ArrowDownOutline, ArrowUpOutline, RefreshOutline } from 'flowbite-svelte-icons';
	import type { Snippet } from 'svelte';

	let { onrefresh, children }: { onrefresh: () => Promise<unknown> | unknown; children: Snippet } =
		$props();

	const THRESHOLD = 70; // px of pull needed to trigger
	const MAX = 110; // px the indicator can travel
	const RESISTANCE = 0.5; // drag feels heavier than 1:1

	let pull = $state(0); // current visible pull distance (px)
	let refreshing = $state(false);
	let tracking = $state(false); // a valid top-pull is in progress
	let startY = 0;

	const ready = $derived(pull >= THRESHOLD);

	const onTouchStart = (e: TouchEvent) => {
		// Only start a pull when the page is scrolled to the very top.
		if (refreshing || window.scrollY > 0 || e.touches.length !== 1) return;
		tracking = true;
		startY = e.touches[0].clientY;
	};

	const onTouchMove = (e: TouchEvent) => {
		if (!tracking) return;
		const dy = e.touches[0].clientY - startY;
		if (dy <= 0 || window.scrollY > 0) {
			// Pulling up or no longer at top — abandon.
			tracking = false;
			pull = 0;
			return;
		}
		// Take over the gesture: stop native scroll/refresh while pulling.
		e.preventDefault();
		pull = Math.min(MAX, dy * RESISTANCE);
	};

	const onTouchEnd = async () => {
		if (!tracking) return;
		tracking = false;
		if (pull < THRESHOLD) {
			pull = 0;
			return;
		}
		// Snap to the "loading" position and run the refresh.
		refreshing = true;
		pull = THRESHOLD;
		try {
			await onrefresh();
		} finally {
			refreshing = false;
			pull = 0;
		}
	};
</script>

<svelte:window
	ontouchstart={onTouchStart}
	ontouchmove={onTouchMove}
	ontouchend={onTouchEnd}
	ontouchcancel={onTouchEnd}
/>

<!-- Pull indicator: sits just under the navbar, follows the finger. -->
<div
	class="pointer-events-none fixed top-[calc(4rem+env(safe-area-inset-top))] right-0 left-0 z-30 flex justify-center"
	style="opacity: {pull > 0 || refreshing ? 1 : 0}; transform: translateY({pull - 50}px);"
>
	<div
		class="flex h-10 w-10 items-center justify-center rounded-full bg-white text-primary-700 shadow-pop dark:bg-gray-800 dark:text-primary-300"
	>
		{#if refreshing}
			<RefreshOutline class="h-5 w-5 animate-spin" />
		{:else if ready}
			<ArrowUpOutline class="h-5 w-5" />
		{:else}
			<ArrowDownOutline class="h-5 w-5" />
		{/if}
	</div>
</div>

<!-- Content follows the pull a little for tactile feedback. -->
<div
	style="transform: translateY({pull}px); transition: {tracking ? 'none' : 'transform 0.2s ease'};"
>
	{@render children()}
</div>
