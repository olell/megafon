<script lang="ts">
	import {
		Button,
		Form,
		FormGroup,
		FormText,
		Input,
		Modal,
		ModalBody
	} from '@sveltestrap/sveltestrap';
	import { push_api_error, push_message } from '../messageService.svelte';
	import {
		createPostApiV1PostsPost,
		initSessionApiV1UserPost,
		type Post,
		type PostWithChildren
	} from '../client';
	import { refreshPosts } from '../sharedState.svelte';

	let { isOpen = $bindable(), parent }: { isOpen: boolean; parent: Post | PostWithChildren } =
		$props();
	let value = $state('');
	const toggle = () => {
		isOpen = !isOpen;
		value = '';
	};

	$effect(() => {
		if (isOpen && parent) {
			value = `@${parent.created_by_name} `;
		} else {
			value = '';
		}
	});

	const handlePost = async (e: SubmitEvent) => {
		e.preventDefault();
		value = value.trim();
		if (value.length < 5) {
			push_message({ color: 'danger', title: 'Fehler!', message: 'Nachricht zu kurz!' });
			return;
		}
		if (value.length > 500) {
			push_message({
				color: 'danger',
				title: 'Fehler!',
				message: 'Nachricht zu lang!'
			});
			return;
		}

		const { data, error } = await createPostApiV1PostsPost({
			credentials: 'include',
			body: {
				parent: parent.id,
				content: value
			}
		});

		if (!!error) {
			push_api_error(error, 'Fehler beim erstellen des Posts!');
			return;
		}

		toggle();
		refreshPosts();
	};

	let inner = $state<HTMLElement>();

	const resize = () => {
		inner!.style.height = 'auto';
		inner!.style.height = 4 + inner!.scrollHeight + 'px';
	};
</script>

<Modal
	autoFocus
	centered
	backdrop="static"
	header="Neuer {parent ? 'Kommentar' : 'Post'}"
	{isOpen}
	{toggle}
>
	<ModalBody>
		<Form onsubmit={handlePost}>
			<FormGroup floating label="Was möchtest du sagen?">
				<Input maxlength={500} bind:inner on:input={resize} type="textarea" bind:value required />
				<FormText>
					{value.length} / 500
				</FormText>
			</FormGroup>
			<Button class="btn-warning float-end">Posten!</Button>
		</Form>
	</ModalBody>
</Modal>
