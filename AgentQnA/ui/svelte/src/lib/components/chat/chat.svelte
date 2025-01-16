<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	export let chatId = "";
	export let selectedContent = "";

	import { onMount } from "svelte";

	// tool
	import type { Message, Chat } from "$lib/components/shared/shared.type";
	import {
		chats$,
		netError,
	} from "$lib/components/shared/shared.store";
	import {
		upsertChat,
		scrollToBottom,
	} from "$lib/components/shared/shared-utils";
	import HOME from "$lib/components/home.svelte"; // Adjust the import path as necessary
	import CreateGoal from "$lib/components/create.svelte"; // Adjust the import path as necessary
	import LoadingAnimation from "./loadingAnimation.svelte";
	import TimeLine from "$lib/components/timeline.svelte";
	import GenerateGoal from "$lib/components/generateGoal.svelte";
	import { getNotificationsContext } from "svelte-notifications";
	import { fetchAgentExecute } from "$lib/modules/network";
	import LoadingStatic from "../agent/loadingStatic.svelte";
	import Summary from "$lib/assets/Agent/summary.svelte";

	const { addNotification } = getNotificationsContext();

	let query: string = "";
	let answer: string = "";
	let loading: boolean = false;
	let scrollToDiv: HTMLDivElement;

	const chat = chatId && $chats$?.[chatId];
	let chatMessages: Message[] = (chat as Chat)?.messages?.filter(Boolean) || [];
	console.log('chatMessages', chatMessages);

	let tool: string;
	let content: any[] = [];
	let name: string;
	let summaryList: any[] = [];
	let selectedGoalIndex: number | null = null; // Stores the selected goal index

	let summary = (chat as Chat)?.summary || "";
	let agentName = (chat as Chat)?.agentName || "";
	let agentDescripe = (chat as Chat)?.agentDescripe || "";
	let source: any[] = [];
	let goals: any[] = [];
	let showAgent: boolean = false;
	let currentGoalIdx = 0;
	let currentTool: string = "";
	let currentGoal: string = "";
	let currentSearch: string = "";
	let currentContent: any;
	let isDrawerOpen = false;

	onMount(async () => {
		scrollToDiv = document?.querySelector(".chat-scrollbar")!;
		console.log("scrollToDiv", scrollToDiv);
	});

	function insertChat() {
		let title =
			chatMessages.length > 0
				? agentName !== ""
					? agentName
					: "New Agent"
				: "New Agent";
		chatId = upsertChat(
			chatId,
			chatMessages,
			title,
			agentName,
			agentDescripe,
		);
	}

	function handleError<T>(err: T) {
		console.log("coming");
		netError.set(true);

		loading = false;
		query = "";
		answer = "";
	}

	function filterBase64Images(summaryList: string[]): string[] {
		const base64ImagePrefix = "iVBOR";

		return summaryList.filter((item) => !item.startsWith(base64ImagePrefix));
	}

	async function handleCreate(event: CustomEvent) {
		showAgent = true;
		query = event.detail;

		agentDescripe = event.detail;
		loading = true;

		await fetchGoals(event.detail);
	}

	async function fetchGoals(query: string): Promise<void> {
		return new Promise<void>((resolve, reject) => {
			fetchAgentExecute(query)
				.then((eventSource) => {
					eventSource.addEventListener("error", (e: any) => {
						console.error("Stream error:", e);
						reject(e);
					});

					eventSource.addEventListener("message", (e: any) => {
						const msg = e.data;
						currentTool = "start";

						if (msg === "[DONE]") {
							console.log("Done", content[content.length - 1]);
							summaryList.push(content[content.length - 1]);

							chatMessages = [
								...chatMessages,
								{ tool, content, goal: query, source },
							];
							scrollToBottom(scrollToDiv);

							console.log("chatMessages", chatMessages);
							currentSearch = "end";
							currentTool = "";
							currentContent = "";
							source = [];
							loading = false;
							insertChat();

							resolve(); // Resolve when parsing is complete
						} else {
							try {
								// Try parsing JSON
								const currentMsg = JSON.parse(msg);
								console.log("currentMsg", currentMsg);

								if (currentMsg.tool) {
									currentTool = currentMsg.tool;
									console.log("currentTool", currentTool);
									tool = currentMsg.tool;
									currentSearch = "start";
								}

								if (currentMsg.source) {
									currentSearch = "finish";
									source = currentMsg.source;
								}

								if (currentMsg.content) {
									content = [...content, ...currentMsg.content];
									scrollToBottom(scrollToDiv);
									currentContent = currentMsg.content;
								}

								console.log("currentMsg.content", currentMsg.content);
							} catch (error) {
								// Handle non-JSON data as image content
								console.log("Non-JSON format, possibly image content:", msg);
							}
						}
					});

					eventSource.stream();
				})
				.catch((error) => {
					console.error("Error:", error);
					reject(error); // Reject on fetch error
				});
		});
	}
</script>

<svelte:head>
	<title>AI Agent</title>
	<meta name="description" content="AI Agent" />
</svelte:head>

<!-- <button on:click={scrollToBottom}>scrollToBottom</button> -->
<div class="flex h-full w-full flex-col">
	{#if chatMessages.length === 0 && query === ""}
		<HOME on:submit={handleCreate} />
	{:else if showAgent || chatMessages.length > 0}
		<div class="h-full rounded-2xl bg-white">
			<main class="mx-auto flex h-full flex-col">
				<div
					class="h-1/8 flex flex-shrink-0 items-center gap-3 border-b border-gray-200 px-4 pb-6 pt-10"
				>
					<Summary />
					<div>
						<h1 class="text-4xl font-bold tracking-tight text-gray-900">
							{agentName}
						</h1>

						<p class="mt-1 max-w-2xl text-sm/6 text-gray-500">
							{agentDescripe}
						</p>
					</div>
				</div>
				<div
					class={`flex w-full flex-grow overflow-hidden transition-all duration-300 ${
						isDrawerOpen ? "h-auto" : "h-0"
					}`}
				>
					<div class="chat-scrollbar relative overflow-auto bg-white p-0 px-10">
						<div class="p-2">
							{#if loading}
								<div class="flex gap-5">
									<LoadingAnimation />
								</div>
							{:else}
								<LoadingStatic />
							{/if}
						</div>

						<!-- current loading status -->

						<GenerateGoal
							{selectedGoalIndex}
							{chatMessages}
							{currentTool}
							{currentSearch}
							{currentContent}
							{scrollToDiv}
						/>
					</div>
				</div>
			</main>
		</div>
	{/if}
</div>
