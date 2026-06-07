<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { Button, Input, Label, Modal } from 'flowbite-svelte';
	import { LockSolid } from 'flowbite-svelte-icons';
	import { adminLoginApiV1AdminLoginPost } from '../client';
	import { push_api_error, push_message } from '../messageService.svelte';
	import { admin_info } from '../sharedState.svelte';

	let { open = $bindable() } = $props();

	let username = $state('');
	let password = $state('');

	const handleLogin = async (e: SubmitEvent) => {
		e.preventDefault();

		const { error } = await adminLoginApiV1AdminLoginPost({
			credentials: 'include',
			body: { username: username.trim(), password }
		});

		if (error) {
			push_api_error(error, 'Login fehlgeschlagen!');
			return;
		}

		admin_info.val = true;
		password = '';
		username = '';
		open = false;
		push_message({ color: 'success', title: 'Admin', message: 'Willkommen im Admin-Bereich.' });
		goto(`${base}/admin`);
	};
</script>

<Modal title="Admin-Login 🔒" bind:open size="sm" class="w-[calc(100%-2rem)]">
	<form onsubmit={handleLogin} class="flex flex-col gap-4">
		<div>
			<Label for="admin-user" class="mb-1">Benutzername</Label>
			<Input id="admin-user" bind:value={username} required autocomplete="username" />
		</div>
		<div>
			<Label for="admin-pass" class="mb-1">Passwort</Label>
			<Input
				id="admin-pass"
				type="password"
				bind:value={password}
				required
				autocomplete="current-password"
			/>
		</div>
		<Button type="submit" color="primary" class="self-end gap-2 font-bold">
			Anmelden <LockSolid class="h-4 w-4" />
		</Button>
	</form>
</Modal>
