<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import {
		Badge,
		Button,
		Input,
		Modal,
		Select,
		Spinner,
		TabItem,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Tabs,
		Toggle
	} from 'flowbite-svelte';
	import {
		adminBanUserApiV1AdminUsersUserIdBanPost,
		adminDeletePostApiV1AdminPostsPostIdDelete,
		adminDismissFlagsApiV1AdminFlagsPostIdDismissPost,
		adminFlagsApiV1AdminFlagsGet,
		adminHidePostApiV1AdminPostsPostIdHidePost,
		adminLogoutApiV1AdminLogoutPost,
		adminPostsApiV1AdminPostsGet,
		adminSessionApiV1AdminSessionGet,
		adminSetModeratorApiV1AdminUsersUserIdModeratorPost,
		adminStatsApiV1AdminStatsGet,
		adminUnhidePostApiV1AdminPostsPostIdUnhidePost,
		adminUsersApiV1AdminUsersGet,
		type AdminFlagItem,
		type AdminPostItem,
		type AdminStats,
		type AdminUserItem,
		type BanMode
	} from '../../client';
	import { push_api_error, push_message } from '../../messageService.svelte';
	import { admin_info } from '../../sharedState.svelte';

	let ready = $state(false);
	let role = $state<'admin' | 'moderator'>('moderator');
	const isAdmin = $derived(role === 'admin');

	let flags = $state<AdminFlagItem[]>([]);
	let users = $state<AdminUserItem[]>([]);
	let stats = $state<AdminStats | null>(null);
	let history = $state<AdminPostItem[]>([]);

	// History controls.
	let historySearch = $state('');
	let includeHidden = $state(true);
	let offset = $state(0);
	const PAGE = 50;

	// Delete confirmation.
	let confirmOpen = $state(false);
	let pendingDelete = $state<{ id: string; content: string } | null>(null);

	const banOptions: { value: BanMode; name: string }[] = [
		{ value: 'none', name: 'Aktiv' },
		{ value: 'blocked', name: 'Gesperrt' },
		{ value: 'blocked_hidden', name: 'Gesperrt + versteckt' },
		{ value: 'shadow', name: 'Shadow-Ban' }
	];

	const banBadge = (m: BanMode) =>
		m === 'none' ? 'green' : m === 'shadow' ? 'purple' : 'red';

	const fmt = (iso: string) => new Date(iso).toLocaleString('de-DE');

	const loadFlags = async () => {
		const { data, error } = await adminFlagsApiV1AdminFlagsGet({ credentials: 'include' });
		if (error) return push_api_error(error, 'Fehler beim Laden der Meldungen!');
		flags = data!;
	};

	const loadUsers = async () => {
		const { data, error } = await adminUsersApiV1AdminUsersGet({ credentials: 'include' });
		if (error) return push_api_error(error, 'Fehler beim Laden der Nutzer!');
		users = data!;
	};

	const loadStats = async () => {
		const { data, error } = await adminStatsApiV1AdminStatsGet({ credentials: 'include' });
		if (error) return push_api_error(error, 'Fehler beim Laden der Statistik!');
		stats = data!;
	};

	const loadHistory = async () => {
		const { data, error } = await adminPostsApiV1AdminPostsGet({
			credentials: 'include',
			query: {
				limit: PAGE,
				offset,
				include_hidden: includeHidden,
				search: historySearch.trim() || undefined
			}
		});
		if (error) return push_api_error(error, 'Fehler beim Laden des Verlaufs!');
		history = data!;
	};

	const dismissFlags = async (postId: string) => {
		const { error } = await adminDismissFlagsApiV1AdminFlagsPostIdDismissPost({
			credentials: 'include',
			path: { post_id: postId }
		});
		if (error) return push_api_error(error, 'Fehler!');
		push_message({ color: 'success', title: 'OK', message: 'Meldungen verworfen.' });
		loadFlags();
	};

	const hidePost = async (postId: string, hidden: boolean) => {
		const fn = hidden
			? adminHidePostApiV1AdminPostsPostIdHidePost
			: adminUnhidePostApiV1AdminPostsPostIdUnhidePost;
		const { error } = await fn({ credentials: 'include', path: { post_id: postId } });
		if (error) return push_api_error(error, 'Fehler!');
		push_message({ color: 'success', title: 'OK', message: hidden ? 'Versteckt.' : 'Sichtbar.' });
		loadFlags();
		loadHistory();
	};

	const askDelete = (id: string, content: string) => {
		pendingDelete = { id, content };
		confirmOpen = true;
	};

	const confirmDelete = async () => {
		if (!pendingDelete) return;
		const { error } = await adminDeletePostApiV1AdminPostsPostIdDelete({
			credentials: 'include',
			path: { post_id: pendingDelete.id }
		});
		confirmOpen = false;
		pendingDelete = null;
		if (error) return push_api_error(error, 'Fehler beim Löschen!');
		push_message({ color: 'success', title: 'OK', message: 'Post gelöscht.' });
		loadFlags();
		loadHistory();
		loadStats();
	};

	const setBan = async (userId: string, mode: BanMode) => {
		const { error } = await adminBanUserApiV1AdminUsersUserIdBanPost({
			credentials: 'include',
			path: { user_id: userId },
			body: { mode }
		});
		if (error) return push_api_error(error, 'Fehler!');
		push_message({ color: 'success', title: 'OK', message: 'Nutzerstatus aktualisiert.' });
		loadUsers();
	};

	const setModerator = async (userId: string, value: boolean) => {
		const { error } = await adminSetModeratorApiV1AdminUsersUserIdModeratorPost({
			credentials: 'include',
			path: { user_id: userId },
			body: { is_moderator: value }
		});
		if (error) return push_api_error(error, 'Fehler!');
		push_message({
			color: 'success',
			title: 'OK',
			message: value ? 'Moderator ernannt.' : 'Moderatorrechte entzogen.'
		});
		loadUsers();
	};

	const logout = async () => {
		await adminLogoutApiV1AdminLogoutPost({ credentials: 'include' });
		admin_info.val = false;
		goto(`${base}/post/top`);
	};

	const prevPage = () => {
		if (offset === 0) return;
		offset = Math.max(0, offset - PAGE);
		loadHistory();
	};
	const nextPage = () => {
		if (history.length < PAGE) return;
		offset += PAGE;
		loadHistory();
	};

	$effect(() => {
		adminSessionApiV1AdminSessionGet({ credentials: 'include' }).then(({ data, error }) => {
			if (error || !data) {
				push_message({
					color: 'warning',
					title: 'Kein Zugriff',
					message: 'Bitte als Admin anmelden.'
				});
				goto(`${base}/post/top`);
				return;
			}
			role = data.role === 'admin' ? 'admin' : 'moderator';
			admin_info.val = true;
			ready = true;
			// Everyone sees the flag queue; the rest is root-admin only.
			loadFlags();
			if (isAdmin) {
				loadUsers();
				loadStats();
				loadHistory();
			}
		});
	});
</script>

{#if !ready}
	<div class="flex justify-center py-20"><Spinner /></div>
{:else}
	<div class="mb-4 flex items-center justify-between">
		<h1 class="text-2xl font-extrabold text-primary-700 dark:text-primary-300">
			{isAdmin ? 'Admin' : 'Moderation'}
		</h1>
		<Button color="alternative" size="sm" onclick={logout}>Abmelden</Button>
	</div>

	<Tabs tabStyle="underline">
		<!-- ============================ FLAGGED ============================ -->
		<TabItem open title="Gemeldet ({flags.length})">
			{#if flags.length === 0}
				<p class="py-6 text-center text-gray-500">Keine offenen Meldungen 🎉</p>
			{:else}
				<div class="flex flex-col gap-3">
					{#each flags as f (f.id)}
						<div class="rounded-card border border-gray-200 p-3 text-gray-800 dark:border-gray-700 dark:text-gray-200">
							<div class="mb-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
								<span class="font-semibold">{f.created_by_name}</span>
								<span>{fmt(f.created_at)}</span>
								{#if f.hidden}<Badge color="red">versteckt</Badge>{/if}
								<span class="ms-auto">▲ {f.upvotes} ▼ {f.downvotes}</span>
							</div>
							<p class="mb-2 whitespace-pre-wrap break-words">{f.content}</p>
							<div class="mb-2 rounded bg-gray-50 p-2 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
								<span class="font-semibold">{f.reports.length} Meldung(en):</span>
								<ul class="ms-4 list-disc">
									{#each f.reports as r}
										<li>{r.reporter}{r.notice ? `: ${r.notice}` : ''}</li>
									{/each}
								</ul>
							</div>
							<div class="flex flex-wrap gap-2">
								<Button size="xs" color="green" onclick={() => dismissFlags(f.id)}>
									Verwerfen
								</Button>
								{#if f.hidden}
									<Button size="xs" color="yellow" onclick={() => hidePost(f.id, false)}>
										Einblenden
									</Button>
								{:else}
									<Button size="xs" color="yellow" onclick={() => hidePost(f.id, true)}>
										Verstecken
									</Button>
								{/if}
								<Button size="xs" color="red" onclick={() => askDelete(f.id, f.content)}>
									Löschen
								</Button>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</TabItem>

		<!-- ============================ USERS (admin only) ============================ -->
		{#if isAdmin}
			<TabItem title="Nutzer ({users.length})">
				<Table>
					<TableHead>
						<TableHeadCell>Name</TableHeadCell>
						<TableHeadCell>Posts</TableHeadCell>
						<TableHeadCell>Meldungen</TableHeadCell>
						<TableHeadCell>Status</TableHeadCell>
						<TableHeadCell>Sperre</TableHeadCell>
						<TableHeadCell>Moderator</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each users as u (u.id)}
							<TableBodyRow>
								<TableBodyCell>
									{u.name}
									{#if u.is_moderator}<Badge color="indigo" class="ms-1">Mod</Badge>{/if}
								</TableBodyCell>
								<TableBodyCell>{u.post_count}</TableBodyCell>
								<TableBodyCell>{u.flags_received}</TableBodyCell>
								<TableBodyCell><Badge color={banBadge(u.ban_mode)}>{u.ban_mode}</Badge></TableBodyCell>
								<TableBodyCell>
									<Select
										size="sm"
										value={u.ban_mode}
										items={banOptions}
										onchange={(e) => setBan(u.id, (e.target as HTMLSelectElement).value as BanMode)}
									/>
								</TableBodyCell>
								<TableBodyCell>
									{#if u.is_moderator}
										<Button size="xs" color="alternative" onclick={() => setModerator(u.id, false)}>
											Entziehen
										</Button>
									{:else}
										<Button size="xs" color="purple" onclick={() => setModerator(u.id, true)}>
											Ernennen
										</Button>
									{/if}
								</TableBodyCell>
							</TableBodyRow>
						{/each}
					</TableBody>
				</Table>
			</TabItem>
		{/if}

		<!-- ============================ STATS (admin only) ============================ -->
		{#if isAdmin}
			<TabItem title="Statistik">
				{#if stats}
				<div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
					{#each [['Nutzer', stats.total_users], ['Posts', stats.total_posts], ['Antworten', stats.total_replies], ['Votes', stats.total_votes], ['Offene Flags', stats.active_flags], ['Versteckt', stats.hidden_posts], ['Gesperrt', stats.banned_users]] as [label, value]}
						<div class="rounded-card border border-gray-200 p-3 text-center dark:border-gray-700">
							<div class="text-2xl font-extrabold text-primary-700 dark:text-primary-300">{value}</div>
							<div class="text-xs text-gray-500">{label}</div>
						</div>
					{/each}
				</div>

				<h3 class="mb-2 mt-4 font-bold text-gray-900 dark:text-white">Top-Autoren</h3>
				<Table>
					<TableHead>
						<TableHeadCell>Name</TableHeadCell>
						<TableHeadCell>Posts</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each stats.top_posters as p}
							<TableBodyRow>
								<TableBodyCell>{p.name}</TableBodyCell>
								<TableBodyCell>{p.post_count}</TableBodyCell>
							</TableBodyRow>
						{/each}
					</TableBody>
				</Table>

				<h3 class="mb-2 mt-4 font-bold text-gray-900 dark:text-white">Top-Posts (Score)</h3>
				<Table>
					<TableHead>
						<TableHeadCell>Inhalt</TableHeadCell>
						<TableHeadCell>Autor</TableHeadCell>
						<TableHeadCell>Score</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each stats.top_posts as p}
							<TableBodyRow>
								<TableBodyCell class="max-w-xs truncate">{p.content}</TableBodyCell>
								<TableBodyCell>{p.created_by_name}</TableBodyCell>
								<TableBodyCell>{p.score}</TableBodyCell>
							</TableBodyRow>
						{/each}
					</TableBody>
				</Table>

				<h3 class="mb-2 mt-4 font-bold text-gray-900 dark:text-white">Aktivität (letzte 30 Tage)</h3>
				<Table>
					<TableHead>
						<TableHeadCell>Tag</TableHeadCell>
						<TableHeadCell>Posts</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each stats.activity as a}
							<TableBodyRow>
								<TableBodyCell>{a.day}</TableBodyCell>
								<TableBodyCell>{a.posts}</TableBodyCell>
							</TableBodyRow>
						{/each}
					</TableBody>
				</Table>
			{/if}
		</TabItem>

		<!-- ============================ HISTORY ============================ -->
		<TabItem title="Verlauf">
			<div class="mb-3 flex flex-wrap items-center gap-3">
				<Input
					placeholder="Suche…"
					bind:value={historySearch}
					class="max-w-xs"
					onkeydown={(e) => {
						if (e.key === 'Enter') {
							offset = 0;
							loadHistory();
						}
					}}
				/>
				<Toggle bind:checked={includeHidden} onchange={() => { offset = 0; loadHistory(); }}>
					inkl. versteckte
				</Toggle>
				<Button size="xs" color="alternative" onclick={() => { offset = 0; loadHistory(); }}>
					Filtern
				</Button>
			</div>
			<Table>
				<TableHead>
					<TableHeadCell>Zeit</TableHeadCell>
					<TableHeadCell>Autor</TableHeadCell>
					<TableHeadCell>Inhalt</TableHeadCell>
					<TableHeadCell>▲▼</TableHeadCell>
					<TableHeadCell>Flags</TableHeadCell>
					<TableHeadCell></TableHeadCell>
				</TableHead>
				<TableBody>
					{#each history as p (p.id)}
						<TableBodyRow>
							<TableBodyCell class="whitespace-nowrap text-xs">{fmt(p.created_at)}</TableBodyCell>
							<TableBodyCell>{p.created_by_name}</TableBodyCell>
							<TableBodyCell class="max-w-xs truncate">
								{#if p.parent_id}<span class="text-gray-400">↳ </span>{/if}{p.content}
								{#if p.hidden}<Badge color="red" class="ms-1">versteckt</Badge>{/if}
							</TableBodyCell>
							<TableBodyCell class="whitespace-nowrap text-xs">{p.upvotes}/{p.downvotes}</TableBodyCell>
							<TableBodyCell>{p.flag_count}</TableBodyCell>
							<TableBodyCell>
								<div class="flex gap-1">
									{#if p.hidden}
										<Button size="xs" color="yellow" onclick={() => hidePost(p.id, false)}>👁</Button>
									{:else}
										<Button size="xs" color="yellow" onclick={() => hidePost(p.id, true)}>🚫</Button>
									{/if}
									<Button size="xs" color="red" onclick={() => askDelete(p.id, p.content)}>🗑</Button>
								</div>
							</TableBodyCell>
						</TableBodyRow>
					{/each}
				</TableBody>
			</Table>
			<div class="mt-3 flex items-center justify-between">
				<Button size="xs" color="alternative" disabled={offset === 0} onclick={prevPage}>
					← Zurück
				</Button>
				<span class="text-xs text-gray-500">{offset + 1}–{offset + history.length}</span>
				<Button size="xs" color="alternative" disabled={history.length < PAGE} onclick={nextPage}>
					Weiter →
				</Button>
			</div>
		</TabItem>
		{/if}
	</Tabs>

	<Modal title="Wirklich löschen?" bind:open={confirmOpen} size="xs">
		<p class="text-sm text-gray-700 dark:text-gray-300">
			Dieser Post (und Antworten/Votes/Meldungen) wird endgültig gelöscht.
		</p>
		<p class="mt-2 max-h-24 overflow-auto rounded bg-gray-50 p-2 text-xs dark:bg-gray-800">
			{pendingDelete?.content}
		</p>
		{#snippet footer()}
			<Button color="alternative" onclick={() => (confirmOpen = false)}>Abbrechen</Button>
			<Button color="red" onclick={confirmDelete}>Löschen</Button>
		{/snippet}
	</Modal>
{/if}
