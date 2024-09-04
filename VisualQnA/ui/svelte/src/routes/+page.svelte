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
	export let data;
	import {
		ifStoreMsg,
		isCheckedStore,
		knowledge1,
	} from "$lib/shared/stores/common/Store";
	import { onMount } from "svelte";
	import Header from "$lib/shared/components/header/header.svelte";
	import {
		LOCAL_STORAGE_KEY,
		MessageRole,
		MessageType,
		type Message,
	} from "$lib/shared/constant/Interface";
	import {
		getCurrentTimeStamp,
		scrollToBottom,
		scrollToTop,
	} from "$lib/shared/Utils";
	import { fetchTextStream } from "$lib/network/chat/Network";
	import LoadingAnimation from "$lib/shared/components/loading/Loading.svelte";
	import "driver.js/dist/driver.css";
	import "$lib/assets/layout/css/driver.css";
	import PaperAirplane from "$lib/assets/chat/svelte/PaperAirplane.svelte";
	import Scrollbar from "$lib/shared/components/scrollbar/Scrollbar.svelte";
	import ChatMessage from "$lib/modules/chat/ChatMessage.svelte";
	import Upload from "$lib/modules/upload/upload.svelte";

	let query: string = "";
	let loading: boolean = false;
	let scrollToDiv: HTMLDivElement;
	// ·········
	let chatMessages: Message[] = data.chatMsg ? data.chatMsg : [];
	console.log("chatMessages", chatMessages);

	// ··············

	$: knowledge_1 = $knowledge1?.id ? $knowledge1.id : "default";

	onMount(async () => {
		scrollToDiv = document
			.querySelector(".chat-scrollbar")
			?.querySelector(".svlr-viewport")!;
	});

	function handleTop() {
		scrollToTop(scrollToDiv);
	}

	function storeMessages() {
		localStorage.setItem(
			LOCAL_STORAGE_KEY.STORAGE_CHAT_KEY,
			JSON.stringify(chatMessages)
		);
	}

	function decodeEscapedBytes(str: string): string {
		const byteArray = str
			.split("\\x")
			.slice(1)
			.map((byte) => parseInt(byte, 16));
		return new TextDecoder("utf-8").decode(new Uint8Array(byteArray));
	}

	function decodeUnicode(str: string): string {
		return str.replace(/\\u[\dA-Fa-f]{4}/g, (match) => {
			return String.fromCharCode(parseInt(match.replace(/\\u/g, ""), 16));
		});
	}

	const callTextStream = async (query: string) => {
		const eventSource = await fetchTextStream(
			query,
			knowledge_1,
			$isCheckedStore
		);

		eventSource.addEventListener("message", (e: any) => {
			let Msg = e.data;
			if (Msg.startsWith("b")) {
				let trimmedData = Msg.slice(2, -1);

				if (/\\x[\dA-Fa-f]{2}/.test(trimmedData)) {
					trimmedData = decodeEscapedBytes(trimmedData);
				} else if (/\\u[\dA-Fa-f]{4}/.test(trimmedData)) {
					trimmedData = decodeUnicode(trimmedData);
				}

				if (trimmedData !== "</s>") {
				        trimmedData = trimmedData.replace(/\\n/g, "\n");
				}
				if (chatMessages[chatMessages.length - 1].role == MessageRole.User) {

					chatMessages = [
						...chatMessages,
						{
							role: MessageRole.Assistant,
							type: MessageType.Text,
							content: trimmedData,
							time: getCurrentTimeStamp(),
						},
					];
					console.log("? chatMessages", chatMessages);
				} else {
					let content = chatMessages[chatMessages.length - 1].content as string;
					chatMessages[chatMessages.length - 1].content = content + trimmedData;
				}
				scrollToBottom(scrollToDiv);
			} else if (Msg === "[DONE]") {
				let startTime = chatMessages[chatMessages.length - 1].time;

				loading = false;
				let totalTime = parseFloat(
					((getCurrentTimeStamp() - startTime) / 1000).toFixed(2)
				);
				if (chatMessages.length - 1 !== -1) {
					chatMessages[chatMessages.length - 1].time = totalTime;
				}
				storeMessages();
			}
		});
		eventSource.stream();
	};

	const handleTextSubmit = async () => {
		loading = true;
		const newMessage = {
			role: MessageRole.User,
			type: MessageType.Text,
			content: query,
			time: 0,
		};
		chatMessages = [...chatMessages, newMessage];
		scrollToBottom(scrollToDiv);
		storeMessages();
		query = "";

		await callTextStream(newMessage.content);

		scrollToBottom(scrollToDiv);
		storeMessages();
	};

	function handelClearHistory() {
		localStorage.removeItem(LOCAL_STORAGE_KEY.STORAGE_CHAT_KEY);
		chatMessages = [];
	}

	function isEmptyObject(obj: any): boolean {
		for (let key in obj) {
			if (obj.hasOwnProperty(key)) {
				return false;
			}
		}
		return true;
	}


</script>

<Header />
<div
	class="h-full gap-5 bg-white sm:flex sm:pb-2 lg:rounded-tl-3xl"
>
<div class="w-1/5 bg-gray-200 p-4">
    <Upload />
  </div>
  <div class="flex-1 bg-gray-100 p-4">
    <div class="mx-auto flex h-full w-full flex-col sm:mt-0 sm:w-[80%] bg-white px-10">
		<div
			class="fixed relative flex w-full flex-col items-center justify-between bg-white p-2 pb-0"
		>
			<div class="relative my-4 flex w-full flex-row justify-center">
				<div class="relative w-full focus:border-none">
					<input
						class="text-md block w-full border-0 border-b-2 border-gray-300 px-1 py-4
						text-gray-900 focus:border-gray-300 focus:ring-0 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500"
						type="text"
						data-testid="chat-input"
						placeholder="Enter prompt here"
						disabled={loading}
						maxlength="1200"
						bind:value={query}
						on:keydown={(event) => {
							if (event.key === "Enter" && !event.shiftKey && query) {
								event.preventDefault();
								handleTextSubmit();
							}
						}}
					/>
					<button
						on:click={() => {
							if (query) {
								handleTextSubmit();
							}
						}}
						type="submit"
						class="absolute bottom-2.5 end-2.5 px-4 py-2 text-sm font-medium text-white dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
						><PaperAirplane /></button
					>
				</div>
			</div>
		</div>

		<!-- clear -->
		{#if Array.isArray(chatMessages) && chatMessages.length > 0 && !loading}
			<div class="flex w-full justify-between pr-5">
				<div class="flex items-center">
					<button
						class="bg-primary text-primary-foreground hover:bg-primary/90 group flex items-center justify-center space-x-2 p-2"
						type="button"
						on:click={() => handelClearHistory()}
						><svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							width="24"
							height="24"
							class="fill-[#0597ff] group-hover:fill-[#0597ff]"
							><path
								d="M12.6 12 10 9.4 7.4 12 6 10.6 8.6 8 6 5.4 7.4 4 10 6.6 12.6 4 14 5.4 11.4 8l2.6 2.6zm7.4 8V2q0-.824-.587-1.412A1.93 1.93 0 0 0 18 0H2Q1.176 0 .588.588A1.93 1.93 0 0 0 0 2v12q0 .825.588 1.412Q1.175 16 2 16h14zm-3.15-6H2V2h16v13.125z"
							/></svg
						><span class="font-medium text-[#0597ff]">CLEAR</span></button
					>
				</div>
			</div>
		{/if}
		<!-- clear -->

		<div class="mx-auto flex h-full w-full flex-col">
			<Scrollbar
				classLayout="flex flex-col gap-1 mr-4"
				className="chat-scrollbar h-0 w-full grow px-2 pt-2 mt-3 mr-5"
			>
				{#each chatMessages as message, i}
					<ChatMessage
						on:scrollTop={() => handleTop()}
						msg={message}
						time={i === 0 || (message.time > 0 && message.time < 100)
							? message.time
							: ""}
					/>
				{/each}
			</Scrollbar>
			<!-- Loading text -->
			{#if loading}
				<LoadingAnimation />
			{/if}
		</div>
		<!-- gallery -->
	</div>
  </div>

</div>

<style>
	.row::-webkit-scrollbar {
		display: none;
	}

	.row {
		scrollbar-width: none;
	}

	.row {
		-ms-overflow-style: none;
	}
</style>
