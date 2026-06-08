<script lang="ts">
	import { Textarea } from 'flowbite-svelte';
	import { tick } from 'svelte';
	import { searchUsersApiV1UserSearchGet } from '../client';
	import { avatarUrl } from '$lib/avatar';

	let {
		value = $bindable(),
		rows = 4,
		maxlength = 500,
		placeholder = ''
	}: {
		value: string;
		rows?: number;
		maxlength?: number;
		placeholder?: string;
	} = $props();

	let el = $state<HTMLTextAreaElement>();
	let suggestions = $state<string[]>([]);
	let open = $state(false);
	// Index of the '@' that starts the token currently being completed.
	let tokenStart = $state(-1);
	let activeIndex = $state(0);
	let debounce: ReturnType<typeof setTimeout>;

	// The @-token immediately before the caret, e.g. "hi @a|" -> { q: 'a' }.
	// Completing starts from the first character after the '@'.
	const tokenBeforeCaret = (text: string, caret: number) => {
		const m = text.slice(0, caret).match(/(?:^|\s)@(\w+)$/);
		if (!m) return null;
		return { q: m[1], start: caret - m[1].length - 1 };
	};

	const closeMenu = () => {
		open = false;
		suggestions = [];
		tokenStart = -1;
		activeIndex = 0;
	};

	const onInput = (e: Event) => {
		el = e.currentTarget as HTMLTextAreaElement;
		const caret = el.selectionStart ?? value.length;
		const token = tokenBeforeCaret(value, caret);
		clearTimeout(debounce);
		if (!token) {
			closeMenu();
			return;
		}
		tokenStart = token.start;
		debounce = setTimeout(async () => {
			const { data } = await searchUsersApiV1UserSearchGet({
				credentials: 'include',
				query: { q: token.q }
			});
			suggestions = data ?? [];
			activeIndex = 0;
			open = suggestions.length > 0;
		}, 150);
	};

	const choose = async (name: string) => {
		if (tokenStart < 0 || !el) return;
		const caret = el.selectionStart ?? value.length;
		const insert = `@${name} `;
		value = value.slice(0, tokenStart) + insert + value.slice(caret);
		const pos = tokenStart + insert.length;
		closeMenu();
		await tick();
		el.focus();
		el.setSelectionRange(pos, pos);
	};

	const onKeydown = (e: KeyboardEvent) => {
		if (!open) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			activeIndex = (activeIndex + 1) % suggestions.length;
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			activeIndex = (activeIndex - 1 + suggestions.length) % suggestions.length;
		} else if (e.key === 'Enter') {
			e.preventDefault();
			choose(suggestions[activeIndex]);
		} else if (e.key === 'Escape') {
			closeMenu();
		}
	};
</script>

<div class="relative">
	<Textarea
		{rows}
		{maxlength}
		{placeholder}
		bind:value
		required
		class="w-full resize-none"
		oninput={onInput}
		onkeydown={onKeydown}
		onblur={() => setTimeout(closeMenu, 120)}
	/>
	{#if open}
		<ul
			class="absolute z-50 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
		>
			{#each suggestions as name, i (name)}
				<li>
					<button
						type="button"
						onmousedown={(e) => {
							e.preventDefault();
							choose(name);
						}}
						class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-700 hover:bg-primary-50 dark:text-gray-200 dark:hover:bg-primary-900/30
							{i === activeIndex ? 'bg-primary-50 dark:bg-primary-900/30' : ''}"
					>
						<img
							src={avatarUrl(null, name)}
							alt=""
							width="20"
							height="20"
							class="h-5 w-5 shrink-0 rounded-full bg-gray-100 dark:bg-gray-700"
						/>
						@{name}
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
