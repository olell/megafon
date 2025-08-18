<script lang="ts">
	import { resolve } from '$app/paths';
	import favicon from '$lib/assets/favicon.svg';
	import {
		Button,
		Container,
		Icon,
		Nav,
		Navbar,
		NavbarBrand,
		Toast,
		ToastBody,
		ToastHeader
	} from '@sveltestrap/sveltestrap';
	import { getSessionApiV1UserGet } from '../client';
	import Login from '../components/login.svelte';
	import { messages, push_message } from '../messageService.svelte';
	import { fade } from 'svelte/transition';
	import { postOrder, user_info } from '../sharedState.svelte';
	import { onMount } from 'svelte';
	import { dev } from '$app/environment';
	import { client } from '../client/client.gen';

	if (!dev) {
		client.setConfig({ ...client.getConfig(), baseUrl: '/' });
	}

	let { children } = $props();

	let loginOpen = $state(false);

	$effect(() => {
		getSessionApiV1UserGet({ credentials: 'include' }).then(({ data, error }) => {
			if (!!error) {
				// create session
				loginOpen = true;
				return;
			}
			push_message({
				color: 'success',
				title: 'Hello!',
				message: `Willkommen zurück, ${data!.name} 👋`
			});
			user_info.val = data!;
		});
	});

	// ==== slop ====

	const enableNotifications = async () => {
		if ('serviceWorker' in navigator && 'PushManager' in window) {
			console.log('HERE?');
			const reg = await navigator.serviceWorker.register('/app/service-worker.js');

			// Request permission
			const permission = await Notification.requestPermission();
			if (permission !== 'granted') return;

			// Get VAPID public key from server
			const res = await fetch('/api/v1/notify/vapid_public_key');
			const { publicKey } = await res.json();

			const sub = await reg.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: urlBase64ToUint8Array(publicKey)
			});

			// Send subscription to backend
			await fetch('/api/v1/notify/subscribe', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(sub)
			});
		} else {
			push_message({
				color: 'danger',
				title: 'Fehler!',
				message: 'Dein Browser unterstütz dieses Feature nicht :,('
			});
		}
	};

	function urlBase64ToUint8Array(base64String: string) {
		const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
		const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
		const rawData = atob(base64);
		return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<Navbar class="mb-3 fixed-top bg-primary navbar-blur" style="border: none;">
	<NavbarBrand href={resolve('/')}>
		<p class="fw-bold">
			<img src={favicon} alt="" height="30" class="d-inline-block ms-2 me-2" />
			TARMAC - MEGAFON
		</p>
	</NavbarBrand>
	<Nav navbar>
		<Button
			color="link"
			size="md"
			onclick={() => {
				postOrder.val = postOrder.val === 'newest' ? 'votes' : 'newest';
			}}
		>
			<Icon name={postOrder.val === 'newest' ? 'clock-fill' : 'star-fill'}></Icon>
		</Button>
		<Button onclick={enableNotifications}>Enable Notify</Button>
	</Nav>
</Navbar>

<Login bind:isOpen={loginOpen} />

<div style="bottom: 0; right: 0; position: fixed; z-index: 9001;">
	{#each messages as message (message.key)}
		<div class="p-3 mb-1" transition:fade>
			<Toast class="me-1">
				<ToastHeader icon={message.color}>{message.title}</ToastHeader>
				<ToastBody>{message.message}</ToastBody>
			</Toast>
		</div>
	{/each}
</div>

<Container style="padding-top: 6rem">
	{@render children?.()}
</Container>

<style>
	:global(.navbar-blur) {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 1000;
	}

	:global(.navbar-blur::after) {
		content: '';
		position: absolute;
		left: 0;
		right: 0;
		bottom: -15px;
		height: 500px;
		pointer-events: none;
		z-index: -1;

		backdrop-filter: blur(100px);
		-webkit-backdrop-filter: blur(15px);

		-webkit-mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, black 100%);
		mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, black 100%);
	}
</style>
