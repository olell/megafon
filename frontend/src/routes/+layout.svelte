<script lang="ts">
	import { browser, dev } from '$app/environment';
	import { resolve } from '$app/paths';
	import favicon from '$lib/assets/favicon.svg';
	import { initTheme, theme, toggleTheme } from '$lib/theme.svelte';
	import { Navbar, NavBrand, Toast } from 'flowbite-svelte';
	import { BullhornSolid, ClockSolid, FireSolid, MoonSolid, SunSolid } from 'flowbite-svelte-icons';
	import { fade, fly } from 'svelte/transition';
	import '../app.css';
	import { getSessionApiV1UserGet } from '../client';
	import { client } from '../client/client.gen';
	import Login from '../components/login.svelte';
	import { messages } from '../messageService.svelte';
	import { postOrder, user_info } from '../sharedState.svelte';

	if (!dev) {
		client.setConfig({ ...client.getConfig(), baseUrl: '/' });
	}

	let { children } = $props();

	let loginOpen = $state(false);

	initTheme();

	// Register the service worker so the app is installable and works offline —
	// independent of whether the user opts into notifications. Skipped in dev to
	// avoid the network-first cache interfering with Vite HMR.
	if (browser && !dev && 'serviceWorker' in navigator) {
		navigator.serviceWorker.register('/app/service-worker.js').catch(() => {});
	}

	// Map message service colours -> Flowbite Toast colours.
	const toastColor = {
		primary: 'primary',
		success: 'green',
		warning: 'yellow',
		danger: 'red'
	} as const;

	$effect(() => {
		getSessionApiV1UserGet({ credentials: 'include' }).then(({ data, error }) => {
			if (error) {
				// create session
				loginOpen = true;
				return;
			}
			user_info.val = data!;
		});
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="apple-touch-icon" href="/app/apple-touch-icon.png" />
	<link rel="manifest" href="/app/manifest.json" />
	<title>MEGAFON</title>
</svelte:head>

<Navbar
	fluid
	class="fixed top-0 right-0 left-0 z-50 border-none bg-primary-600/80 pt-[calc(0.625rem+env(safe-area-inset-top))] text-white shadow-pop backdrop-blur-md dark:bg-primary-800/80"
>
	<NavBrand href={resolve('/')} class="gap-2">
		<img src={favicon} alt="" height="32" class="h-8 w-8" />
		<span class="self-center text-lg font-extrabold tracking-tight whitespace-nowrap text-white">
			TARMAC - MEGAFON
		</span>
	</NavBrand>

	<div class="flex items-center gap-1">
		<button
			type="button"
			aria-label="Sortierung umschalten"
			title={postOrder.val === 'newest' ? 'Neueste zuerst' : 'Beliebteste zuerst'}
			class="rounded-full p-2 text-white transition-transform hover:scale-110 hover:bg-white/15 active:scale-95"
			onclick={() => {
				postOrder.val = postOrder.val === 'newest' ? 'votes' : 'newest';
			}}
		>
			{#if postOrder.val === 'newest'}
				<ClockSolid class="h-6 w-6" />
			{:else}
				<FireSolid class="h-6 w-6" />
			{/if}
		</button>

		<button
			type="button"
			aria-label="Farbschema umschalten"
			title={theme.dark ? 'Hell' : 'Dunkel'}
			class="rounded-full p-2 text-white transition-transform hover:scale-110 hover:bg-white/15 active:scale-95"
			onclick={toggleTheme}
		>
			{#if theme.dark}
				<SunSolid class="h-6 w-6" />
			{:else}
				<MoonSolid class="h-6 w-6" />
			{/if}
		</button>

		<BullhornSolid class="ms-1 h-6 w-6 text-secondary-300" />
	</div>
</Navbar>

<Login bind:open={loginOpen} />

<div class="fixed bottom-0 left-0 z-[9001] flex flex-col gap-2 p-3">
	{#each messages as message (message.key)}
		<div transition:fade>
			<Toast color={toastColor[message.color]} transition={fly} params={{ x: -200 }}>
				<span class="font-semibold">{message.title}</span>
				<span class="ms-1">{message.message}</span>
			</Toast>
		</div>
	{/each}
</div>

<main class="mx-auto w-full max-w-2xl px-3 pb-28 pt-[calc(6rem+env(safe-area-inset-top))]">
	{@render children?.()}
</main>
