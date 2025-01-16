<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import Resource from "$lib/assets/Agent/resource.svelte";
	import { onMount, afterUpdate } from "svelte";
	import { Badge, P, Spinner } from "flowbite-svelte";
	import Task from "$lib/assets/Agent/taskIcon.svelte";
	import ToolIcon from "$lib/assets/Agent/toolIcon.svelte";
	import SearchResult from "$lib/assets/Agent/searchResult.svelte";
	import TaskResult from "$lib/assets/Agent/taskResult.svelte";

	let openIndex: number = 0;

	export let selectedGoalIndex: number | null;
	export let chatMessages;
	export let currentSearch: string;
	export let currentTool: string;
	export let currentContent;
	export let scrollToDiv: HTMLDivElement;

	$: if (scrollToDiv) {
		console.log("coming", chatMessages, scrollToDiv);
		scrollToBottom(scrollToDiv);
	}

	console.log("chatMessages", chatMessages);

	export let chatContainer: HTMLElement | null = null;
	function scroll() {
		scrollToDiv = document?.querySelector(".chat-scrollbar")!;
		scrollToBottom(scrollToDiv);
	}

	// Watch for changes in chatMessages and trigger scrolling
	$: chatMessages ||
	currentSearch ||
	currentTool ||
	currentContent
		? scroll()
		: "";

	// Extract necessary data and generate download content
	function generateTxt() {
		let txtContent = chatMessages
			.map((task, index) => {
				// Extract data
				const taskNumber = `Task ${index + 1}:`;
				const goal = `Goal: ${task.goal}`;
				const tool = `Tool: ${task.tool}`;

				const contentIntro = "Search Results:";
				const content = task.content.slice(0, -1).join("\n"); // All content except the last item
				const currentResult = `Current Task Result: ${
					task.content[task.content.length - 1]
				}`;

				const sourcesIntro = "Resources:";
				const sources = task.source
					.map(([name, link]) => `- ${name}: ${link}`)
					.join("\n");

				// Format the output
				return `${taskNumber}\n${goal}\n${tool}\n${contentIntro}\n${content}\n${currentResult}\n${sourcesIntro}\n${sources}\n`;
			})
			.join("\n");

		// Create Blob and URL
		const blob = new Blob([txtContent], { type: "text/plain" });
		const url = URL.createObjectURL(blob);

		// Download the file
		const link = document.createElement("a");
		link.href = url;
		link.download = "tasks.txt";
		link.click();

		// Release the URL
		URL.revokeObjectURL(url);
	}

	import { marked } from "marked";
	import Download from "$lib/assets/Agent/download.svelte";
	import { scrollToBottom } from "./shared/shared-utils";

	const renderMarkdown = (content: string) => marked(content);

	// Watch for changes in selectedGoalIndex to update openIndex
	$: if (selectedGoalIndex !== null && selectedGoalIndex !== 100) {
		openIndex = selectedGoalIndex;
	}

	// Toggle the visibility of chat details for each goal
	const toggleOpenIndex = (index: number) => {
		openIndex = openIndex === index ? null : index;
	};

	// Scroll to the selected goal when mounted or updated
	const scrollToSelectedGoal = () => {
		if (selectedGoalIndex !== null) {
			const goalElement = document.getElementById(`goal-${selectedGoalIndex}`);
			if (goalElement) {
				goalElement.scrollIntoView({ behavior: "smooth", block: "start" });
			}
		}
	};

	onMount(scrollToSelectedGoal);
	afterUpdate(scrollToSelectedGoal);
</script>

<div
	class="chatContainer mx-auto w-full gap-4 overflow-auto p-4 pt-0"
	id="generatePDF"
>
	{#each chatMessages as goal, index}
		<div class="w-full border-b py-2" id={`goal-${index}`}>
			<div class="flex w-full">
				<div class="w-full">
					<h2 class="flex items-center text-sm font-semibold leading-6">
						<!-- svelte-ignore a11y-click-events-have-key-events -->
						<span
							class="flex cursor-pointer items-center gap-1 rounded bg-gray-100 px-3 py-1 text-slate-900 hover:bg-gray-100 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 {openIndex ===
							index
								? 'highlight'
								: ''}"
							on:click={() => toggleOpenIndex(index)}
						>
							<Task />
							<span
								class="max-w-[25rem] overflow-hidden text-ellipsis whitespace-nowrap"
								>{goal.goal}</span
							>
							<span class="ml-2 text-xs">{openIndex === index ? "▲" : "▼"}</span
							>
						</span>

						<span class="ml-2 h-4 w-px bg-slate-300" />
						{#if goal.tool}
							<span
								class="me-2 ms-3 flex items-center gap-2 rounded bg-blue-100 px-2.5 py-0.5 text-sm font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-300"
							>
								<ToolIcon />

								{goal.tool}
							</span>
						{/if}
					</h2>

					{#if openIndex === index}
						{#each goal.content.slice(0, -1) as msg}
							<div
								class="collapsible mt-2 max-h-[10rem] w-full overflow-auto rounded-lg border border-b bg-gray-100 p-4 text-sm dark:bg-gray-800"
							>
								<p
									class="flex items-center gap-2 border-b border-gray-900/10 pb-2 font-bold text-blue-600"
								>
									<SearchResult /> Result
								</p>
								<p>{@html renderMarkdown(msg)}</p>
							</div>
						{/each}
					{/if}

					<p
						class="my-2 mt-2 rounded-xl border border-green-600 p-2 py-2 text-sm leading-5 text-slate-600"
					>
						<!-- Display the title only when content is not an image -->
						<span class="flex items-center gap-1 py-2 font-bold text-blue-600">
							<TaskResult />
							Current Result
						</span>
						{#if goal.content[goal.content.length - 1] && goal.content[goal.content.length - 1].startsWith("iVBORw0KGgoAAAANSUhEUgAA")}
							<!-- If the last content is a base64 image string, display it as an image -->
							<img
								src="data:image/png;base64,{goal.content[
									goal.content.length - 1
								]}"
								alt="Base64 Image"
								class="h-32 w-32 cursor-pointer transition-transform duration-300 hover:scale-125"
							/>
						{:else}
							<!-- Render the content as markdown -->
							{@html renderMarkdown(goal.content[goal.content.length - 1])}
						{/if}
					</p>
				</div>
			</div>

			{#if goal.source}
				<div
					class="mb-3 mt-1 grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4"
				>
					{#each goal.source as source, idx}
						<div
							class="truncate text-ellipsis rounded-lg border border-gray-200 px-4 py-2"
						>
							<a
								href={source[1]}
								target="_blank"
								rel="noopener noreferrer"
								class="flex w-full items-center overflow-hidden bg-white text-sm font-medium text-gray-900 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:text-blue-700 focus:outline-none focus:ring-4 focus:ring-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white dark:focus:ring-gray-700"
							>
								<Resource />
								<span
									class="ml-2 overflow-hidden text-ellipsis whitespace-nowrap"
									>{source[0]}</span
								>
							</a>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/each}

</div>

<div class="mb-4 inline-flex flex-col space-y-2 px-3">
	<!-- Container with flex column layout -->
	{#if currentTool === "start" && currentSearch !== "start" && currentSearch !== "finish"}
		<Badge color="pink" border>
			<Spinner class="me-1.5 h-4 w-4" color="white" />
			Searching for the appropriate tool...
		</Badge>
	{/if}

	{#if currentTool !== "" && currentTool !== "start" && currentSearch !== "start"}
		<Badge color="yellow" border>
			{#if currentSearch !== "finish"}
				<Spinner class="me-1.5 h-4 w-4" color="white" />
			{/if}
			Currently using the tool
			<strong> {currentTool} </strong>
		</Badge>
	{/if}

	{#if currentSearch === "start"}
		{#if (currentTool) === "Image Generation"}
			<Badge color="purple" border>
				<Spinner class="me-1.5 h-4 w-4" color="white" />
				Generating an image using the
				<strong> {currentTool} </strong> tool...
			</Badge>
		{:else}
			<Badge color="purple" border>
				<Spinner class="me-1.5 h-4 w-4" color="white" />
				Searching using the
				<strong> {currentTool} </strong> tool...
			</Badge>
		{/if}
	{/if}
</div>

{#if currentContent && currentContent !== ""}
	<div
		class="mt-2 max-h-[10rem] w-full overflow-auto rounded-lg border border-b bg-gray-100 p-4 text-sm dark:bg-gray-800"
	>
		<p class="font-bold text-blue-600">-- Web Search Results --</p>
		<p>{currentContent}</p>
	</div>
{/if}
<div class="m-2 inline-flex flex-col space-y-2">
	{#if currentSearch === "finish"}
		<Badge color="green" border>
			<Spinner class="me-1.5 h-4 w-4" color="white" />
			Search completed, summarizing the current task content...
		</Badge>
	{/if}
</div>

<style>
	.highlight {
		background-color: #e0f7fa;
		border-left: 4px solid #00796b;
	}
</style>
