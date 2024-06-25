<!--
  Copyright (c) 2024 Intel Corporation

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

<script lang="ts">
	import ChatMessage from "$lib/modules/chat/chat-message.svelte";

	// icon
	import ArrowPathIcon from "$lib/assets/icons/svelte/arrow-path-icon.svelte";
	// tool
	import {
		MESSAGE_ROLE,
		type Message,
	} from "$lib/components/shared/shared.type";
	import { scrollToBottom } from "$lib/components/shared/shared-utils";
	import {
		fetchAudioStream,
		fetchAudioText,
		fetchTextResponse,
	} from "$lib/modules/chat/network";
	import VoiceButton from "$lib/components/talkbot/voice-button.svelte";
	import LoadingButtonSpinnerIcon from "$lib/assets/icons/svelte/loading-button-spinner-icon.svelte";

	let loading: boolean = false;
	let enableRegenerate: boolean = false;
	let scrollToDiv: HTMLDivElement;

	let chatMessages: Message[] = [];

	$: enableRegenerateMessage = !loading && chatMessages.length > 2;
	console.log("chatMessages", chatMessages);

	function convertBlobToBase64(blob) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onloadend = () => resolve(reader.result.split(",")[1]); // Extract the base64 part from the result
			reader.onerror = reject;
			reader.readAsDataURL(blob);
		});
	}

	function base64ToBlob(base64Data) {
		const binaryData = atob(base64Data);
		const arrayBuffer = new ArrayBuffer(binaryData.length);
		const uint8Array = new Uint8Array(arrayBuffer);

		for (let i = 0; i < binaryData.length; i++) {
			uint8Array[i] = binaryData.charCodeAt(i);
		}

		return new Blob([uint8Array], { type: "audio/mpeg" });
	}

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

		const blob = await fetch(content)
			.then((r) => r.blob())
			.then(convertBlobToBase64);
		const res = await fetchAudioText(blob);
		console.log("res", res);

		if (res) {
			const audioBlob = base64ToBlob(res);
			chatMessages = [
				...chatMessages,
				{
					role: MESSAGE_ROLE.ASSISTANT,
					content: URL.createObjectURL(audioBlob),
				},
			];
			scrollToBottom(scrollToDiv);
			loading = false;
		}
	};
</script>

<svelte:head>
	<title>Neural Chat</title>
	<meta name="description" content="Neural Chat" />
</svelte:head>

<div
	class="mx-auto h-full w-full rounded-3xl bg-white px-6 shadow sm:w-full xl:w-2/3"
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
				<ChatMessage type={message.role} message={message.content} />
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
				<VoiceButton
					bind:chatMessages
					on:done={() => {
						handleSubmit();
					}}
				/>
			</div>
		</div>
	</div>
</div>
