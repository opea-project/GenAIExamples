<script lang="ts">
	import ChatMessage from "$lib/modules/chat/chat-message.svelte";

	// icon
	import ArrowPathIcon from "$lib/assets/icons/svelte/arrow-path-icon.svelte";

	// tool
	import { MESSAGE_ROLE, type Message } from "$lib/components/shared/shared.type";
	import { scrollToBottom } from "$lib/components/shared/shared-utils";
	import { fetchAudioStream, fetchAudioText, fetchTextResponse } from "$lib/modules/chat/network";
	import VoiceButton from "$lib/components/talkbot/voice-button.svelte";
	import LoadingButtonSpinnerIcon from "$lib/assets/icons/svelte/loading-button-spinner-icon.svelte";

	let loading: boolean = false;
	let enableRegenerate: boolean = false;
	let scrollToDiv: HTMLDivElement;

	let chatMessages: Message[] = [];

	$: enableRegenerateMessage = !loading && chatMessages.length > 2;
	console.log('chatMessages', chatMessages);


	const handleSubmit = async (enableRegenerate = false): Promise<void> => {
		scrollToBottom(scrollToDiv);
		loading = true;
		if (enableRegenerate) {
			let lastRole = chatMessages[chatMessages.length - 1];
			if (lastRole.role === "assistant") {
				chatMessages = chatMessages.filter(
					(_, i: number) => i !== chatMessages.length - 1
				);
			}
		}

		const content = chatMessages[chatMessages.length - 1].content;

		const blob = await fetch(content).then(r => r.blob());

		const res = await fetchAudioText(blob);
		// fetchTextResponse
		const textRes = await fetchTextResponse(res.asr_result);

		// fetch audio stream
		const eventSource = await fetchAudioStream(textRes)

		eventSource.addEventListener("message", async (e) => {
			let currentMsg = e.data;
			if (currentMsg.startsWith("b'")) {
				const audioUrl = "data:audio/wav;base64," + currentMsg.slice(2, -1)
				const blob = await fetch(audioUrl).then(r => r.blob());
				chatMessages = [
					...chatMessages,
					{ role: MESSAGE_ROLE.ASSISTANT, content: URL.createObjectURL(blob) },
				];
				scrollToBottom(scrollToDiv);
			} else if (currentMsg === '[DONE]') {
				loading = false;
				enableRegenerate = true;
			}
		});

		eventSource.stream();
	};

</script>

<svelte:head>
	<title>Neural Chat</title>
	<meta name="description" content="Neural Chat" />
</svelte:head>

<div
		class="h-full w-full rounded-3xl bg-white px-6 shadow sm:w-full xl:w-2/3 mx-auto"
	>
<div class="flex h-full w-full flex-col p-10 py-4">
	<div
		class="carousel carousel-vertical flex h-0 flex-grow flex-col overflow-auto p-4"
		bind:this={scrollToDiv}
	>
		<ChatMessage
			type="Assistant"
			message={`Welcome to AudioQnA! 😊`}
			displayTimer={false}
		/>
		{#each chatMessages as message}
			<ChatMessage
				type={message.role}
				message={message.content}
			/>
		{/each}
	</div>

	<div class="mx-auto w-10/12 pb-5">
		<!-- Loading text -->
		{#if loading}
			<div
				class="mb-6 flex items-center justify-center self-center text-sm text-gray-500"
			>
				<div class="inset-y-0 left-0 pl-2">
					<LoadingButtonSpinnerIcon />
				</div>

				<div class="ml-3">AudioQnA is thinking...</div>
			</div>
		{/if}

		<!-- regenerate -->
		{#if enableRegenerateMessage && enableRegenerate}
			<button
				on:click={() => {
					handleSubmit((enableRegenerate = true));
				}}
				type="button"
				class="mx-auto mb-1 flex w-48 items-center justify-center gap-2 self-center whitespace-nowrap rounded-md bg-white px-3 py-2 text-sm text-gray-700 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
			>
				<ArrowPathIcon />
				Regenerate response
			</button>
		{/if}

		<!-- Input -->
		<div class="flex flex-col items-center">
			<VoiceButton bind:chatMessages on:done={() => {handleSubmit()}} />
		</div>
	</div>
</div>
</div>
