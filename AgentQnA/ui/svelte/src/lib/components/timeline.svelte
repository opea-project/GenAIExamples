<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import Time from "$lib/assets/Agent/time.svelte";
	import { createEventDispatcher } from "svelte";

	export let selectedGoals;
	let selectedIndex: number | null = null;
	console.log("selectedGoals", selectedGoals);

	const dispatch = createEventDispatcher();

	function scrollToTop() {
		window.scrollTo({ top: 0, behavior: "smooth" });
	}


	function handleGoalClick(index: number) {
		selectedIndex = index;
		dispatch("goalClick", index);
		scrollToTop(); // Scroll to the top of the page
	}
</script>

<div class="relative mt-4 h-full overflow-auto hiddenScroll p-4">
	<div
		class="absolute left-[2rem] top-0 h-full border-l border-gray-200 dark:border-gray-700"
	/>
	<ol class="relative">
		{#each selectedGoals as goal, index}
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<li
				class="mb-10 flex cursor-pointer items-start rounded-lg p-4 transition-colors duration-200 {selectedIndex ===
				index
					? 'bg-white shadow-lg'
					: 'bg-transparent'}"
				on:click={() => handleGoalClick(index)}
			>
				<span
					class="flex h-8 w-8 flex-shrink-0 -translate-x-1/2 items-center justify-center rounded-full bg-blue-100 ring-8 ring-white dark:bg-blue-900 dark:ring-gray-900"
				>
					<Time />
				</span>
				<div class="ml-4">
					<p
						class="mb-0 text-base font-normal text-gray-500 dark:text-gray-400 max-w-[6rem] overflow-hidden text-ellipsis whitespace-nowrap "
					>
						{goal}
					</p>
				</div>
			</li>
		{/each}
	</ol>
</div>

<style>
	.hiddenScroll::-webkit-scrollbar {
    display: none;
  }

  .hiddenScroll {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }
</style>
