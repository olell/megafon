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
		NavItem,
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
			user_info.val = data!;
		});
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="manifest" href="/app/manifest.json" />
	<title>MEGAFON</title>
</svelte:head>

<Navbar class="mb-3 fixed-top bg-primary navbar-blur" style="border: none;">
	<NavbarBrand href={resolve('/')}>
		<p class="fw-bold">
			<img src={favicon} alt="" height="30" class="d-inline-block ms-2 me-2" />
			TARMAC - MEGAFON
		</p>
	</NavbarBrand>
	<Nav navbar class="d-inline">
		<NavItem>
			<Button
				color="link"
				size="md"
				onclick={() => {
					postOrder.val = postOrder.val === 'newest' ? 'votes' : 'newest';
				}}
			>
				<Icon name={postOrder.val === 'newest' ? 'clock-fill' : 'star-fill'}></Icon>
			</Button>
		</NavItem>
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
