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
		base64ImageStore,
		stepValueStore,
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
	import { fetchGuardRail, fetchTextStream } from "$lib/network/chat/Network";
	import LoadingAnimation from "$lib/shared/components/loading/Loading.svelte";
	import "driver.js/dist/driver.css";
	import "$lib/assets/layout/css/driver.css";
	import PaperAirplane from "$lib/assets/chat/svelte/PaperAirplane.svelte";
	import Scrollbar from "$lib/shared/components/scrollbar/Scrollbar.svelte";
	import ChatMessage from "$lib/modules/chat/ChatMessage.svelte";
	import Upload from "$lib/modules/upload/upload.svelte";
	import ImagePrompt from "$lib/modules/upload/imagePrompt.svelte";
	import { Toast } from "flowbite-svelte";
	import { ExclamationCircleSolid, FireOutline } from "flowbite-svelte-icons";
	import GenerateImg from "$lib/modules/imageList/GenerateImg.svelte";

	let query: string = "";
	let loading: boolean = false;
	let scrollToDiv: HTMLDivElement;
	let chatMessages: Message[] = data.chatMsg ? data.chatMsg : [];
	let showToast = false;

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
		const res = await fetchGuardRail(query, $stepValueStore, $base64ImageStore);
		console.log('res', res);


		const lastSegment = res.text.split("[/INST]").pop().trim();

		if (lastSegment === "unsafe") {
			loading = false;

			showToast = true;
			setTimeout(() => {
				showToast = false;
			}, 3000);

			chatMessages = [
				...chatMessages,
				{
					role: MessageRole.Assistant,
					type: MessageType.Text,
					content: "unsafe",
					time: getCurrentTimeStamp(),
					imgSrc: null, // Add the imgSrc property here
				},
			];

			return;
		} else {
			const chatRes = await fetchTextStream(
				query,
				$stepValueStore,
				$base64ImageStore
			);
			if (chatRes.text) {
				loading = false;
				chatMessages = [
					...chatMessages,
					{
						role: MessageRole.Assistant,
						type: MessageType.Text,
						content: chatRes.text,
						time: getCurrentTimeStamp(),
						imgSrc: null, // Add the imgSrc property here
					},
				];
				storeMessages();
			}
		}
	};

	const handleTextSubmit = async () => {
		loading = true;

		const newMessage = {
			role: MessageRole.User,
			type: MessageType.Text,
			content: query,
			imgSrc: $base64ImageStore,
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

	function handleUpdateQuery(event) {
		if (event.detail && event.detail.content) {
			query = event.detail.content;
			handleTextSubmit();
		}
	}
</script>

<div class="bg-gray-200 w-full h-full">
	<Header />

	<div class="bg-white mt-[2%] mx-auto h-[85%] w-[90%] rounded-3xl p-8">
		<p class="text-3xl">AI Image Generator</p>
		<div class="relative w-full my-6">
			<span class="absolute p-2 text-xs text-gray">Description prompt</span>
			<input
				class="block w-full border-gray-300 px-2 py-10 text-gray-900  rounded-xl"
				type="text"
				data-testid="chat-input"
				placeholder="What do you want to see?"
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

	<GenerateImg />
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
