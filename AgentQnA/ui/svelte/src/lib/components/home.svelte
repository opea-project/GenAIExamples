<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import PaperAirplane from "$lib/assets/icons/paper-airplane.svelte";
	import {
		ArrowPathIcon,
		CloudArrowUpIcon,
		FingerPrintIcon,
		LockClosedIcon,
	} from "@heroicons/vue/24/outline";
	import Star from "$lib/assets/Agent/star.svelte";
	import { getNotificationsContext } from "svelte-notifications";
	import { netError } from "$lib/components/shared/shared.store";

	const { addNotification } = getNotificationsContext();

	export let query: string = "";
	import { createEventDispatcher } from "svelte";

	const dispatch = createEventDispatcher();

	function showNotification(text: string, type: string) {
		addNotification({
			text: text,
			position: "top-right",
			type: type,
			removeAfter: 3000,
		});
	}

	const features = [
        {
            name: "Chengdu Travel Plan",
            description: "Create a travel plan for visiting Chengdu",
            icon: CloudArrowUpIcon,
            goals: [
                "Best time to travel to Chengdu",
                "Must-visit attractions in Chengdu",
                // "Transportation guide for Chengdu",
                "Accommodation recommendations in Chengdu",
            ],
        },
        {
            name: "Intel Corporation",
            description: "Introduce Intel Corporation",
            icon: LockClosedIcon,
            goals: [
                "Overview of Intel Corporation",
                "History of Intel Corporation",
                "Key products of Intel Corporation",
                "Latest technological advancements by Intel Corporation",
            ],
        },
        {
            name: "Paper Contribution Summary",
            description: "Summarize the contributions of the Qwen technical paper",
            icon: ArrowPathIcon,
            goals: [
                "List the contributions of this paper, https://qianwen-res.oss-cn-beijing.aliyuncs.com/QWEN_TECHNICAL_REPORT.pdf",
                "Further introduce the Qwen model's related technologies",
            ],
        },
        {
            name: "Chengdu Panda Base Introduction",
            description: "Introduce Chengdu Panda Base and draw a picture",
            icon: FingerPrintIcon,
            goals: [
                "Overview of Chengdu Panda Base",
                "Draw a picture of a panda in Chengdu Panda Base",
            ],
        },
    ];

	function handleCreate(feature: any) {
		if (query == "" && feature == "") {
			netError.set(true);
			setTimeout(() => {
				netError.set(false);
			}, 3000);

			showNotification("Please enter project details first", "error");
		} else {
			if (feature !== "") {
				query = feature;
			}
			dispatch("submit", query);
		}
	}

</script>

<div class="mx-auto w-full max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
	<div class="mx-auto max-w-2xl lg:text-center">
		<h1
			class="bg-gradient-to-r from-purple-300 to-blue-300 bg-clip-text text-7xl font-bold uppercase text-transparent"
		>
			AI AGENT
		</h1>
	</div>

	<dl
		class="mx-auto ml-40 mt-16 grid max-w-xl grid-cols-1 gap-6 gap-x-8 lg:max-w-4xl lg:grid-cols-2"
	>
		{#each features as feature (feature.name)}
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<div
				class="relative rounded-xl bg-white p-2 py-8 pl-16"
				on:click={() => handleCreate(feature.description)}
			>
				<dt class="text-base font-semibold text-gray-900">
					<div
						class="absolute left-0 top-0 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600"
					>
						<feature.icon />
					</div>
					{feature.name}
				</dt>
				<dd class="mt-2 text-base text-gray-600">{feature.description}</dd>
			</div>
		{/each}
	</dl>

	<div class="relative mt-10 flex items-start justify-center space-x-2">
		<button
			on:click={() => handleCreate(query)}
			class="flex cursor-pointer items-center gap-3 whitespace-nowrap rounded-lg bg-blue-700 px-5 py-3 text-center text-sm font-medium text-white hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
		>
			<Star />
			Start Creating</button
		>
		<textarea
			class="textarea-bordered h-28 w-full rounded-2xl border-b-2 border-gray-200 border-b-[#00469f]"
			placeholder="Enter the details of the project to create"
			maxlength="1200"
			bind:value={query}
			on:keydown={(event) => {
				if (event.key === "Enter" && !event.shiftKey && query) {
					event.preventDefault();
					handleCreate(query);
				}
			}}
		/>
		<button
			on:click={() => query && handleCreate(query)}
			type="submit"
			class="absolute right-0 py-2 pr-3"
		>
			<PaperAirplane />
		</button>
	</div>
</div>
