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
		NavItem
	} from '@sveltestrap/sveltestrap';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<Navbar class="mb-3 fixed-top bg-primary navbar-blur" style="border: none;">
	<NavbarBrand href={resolve('/')}>
		<img src={favicon} alt="" height="30" class="d-inline-block ms-2 me-2" />
		TARMAC - MEGAFON
	</NavbarBrand>
	<Nav navbar>
		<NavItem class="float-end">
			<Button color="warning" class="fs-4"><Icon name="chat-square-text-fill"></Icon></Button>
		</NavItem>
	</Nav>
</Navbar>

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
