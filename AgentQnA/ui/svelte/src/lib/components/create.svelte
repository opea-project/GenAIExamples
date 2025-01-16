<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { createEventDispatcher } from "svelte";
	import LoadingAnimation from "./chat/loadingAnimation.svelte";
	import NewAI from "$lib/assets/Agent/newAI.svelte";
	import { getNotificationsContext } from "svelte-notifications";
	import CreateSub from "$lib/assets/Agent/createSub.svelte";
	import { Badge } from "flowbite-svelte";

	// Input properties
	export let goals: string[] = [];
	export let agentDescripe: string;

	let editIndex: number | null = null; // Index of the goal being edited
	let newContent = ""; // Temporary storage for new goal input
	export let agentName = "New AI Agent";
	let editContent = ""; // Temporary storage for edited content

	const dispatch = createEventDispatcher();

	const { addNotification } = getNotificationsContext();

	// Start editing a specific goal
	function startEdit(index) {
		editIndex = index;
		editContent = goals[index];
	}

	// Save the edited content
	function saveEdit(index) {
		goals[index] = editContent;
		editIndex = null;
	}

	// Delete a goal by index
	function deleteGoal(index) {
		goals.splice(index, 1);
		goals = [...goals]; // Trigger reactivity
		editIndex = null;
	}

	// Cancel editing
	function cancelEdit() {
		editIndex = null;
		dispatch("cancelCreate");
	}

	// Show notification
	function showNotification(text: string, type: string) {
		addNotification({
			text: text,
			position: "top-right",
			type: type,
			removeAfter: 3000,
		});
	}

	// Add a new goal
	function addGoal() {
		if (newContent.trim() && goals.length < 5) {
			goals = [...goals, newContent];
			newContent = "";
		} else {
			showNotification("Exceeded maximum number of tasks", "error");
		}
	}

	// Save and send data to parent component
	function save() {
		dispatch("execute", { goals, agentName, agentDescripe });
	}
</script>

<div class="relative h-full space-y-2 rounded-2xl bg-white p-6">
	<h2
		class="flex gap-4 border-b border-gray-900/10 py-6 text-4xl font-semibold text-gray-900"
	>
		<NewAI />
		Create Agent
	</h2>

	<div class="border-b border-gray-900/10 pb-4">
		<div class="grid grid-cols-1 gap-x-6 gap-y-8 sm:grid-cols-6">
			<div class="sm:col-span-4">
				<label for="username" class="block text-sm text-gray-900">Name</label>
				<div class="mt-1">
					<div
						class="flex rounded-md shadow-sm ring-1 ring-inset ring-gray-300 focus-within:ring-2 focus-within:ring-inset focus-within:ring-indigo-600 sm:max-w-md"
					>
						<input
							bind:value={agentName}
							type="text"
							name="username"
							id="username"
							autocomplete="username"
							class="block flex-1 border-0 bg-transparent px-2 px-4 py-1.5 pl-1 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm/6"
							placeholder="A new AI project..."
						/>
					</div>
				</div>
			</div>

			<div class="col-span-full">
				<label for="about" class="block text-sm text-gray-900">Description</label>
				<div class="mt-1">
					<textarea
						bind:value={agentDescripe}
						id="about"
						name="about"
						rows="3"
						class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm/6"
					/>
				</div>
			</div>
		</div>
	</div>

	<div class="h-[28rem] w-full overflow-auto border-b border-gray-900/10">
		<h2
			class="my-2 mb-2 ml-1 flex items-center gap-3 text-base/7 font-semibold text-gray-900"
		>
			<CreateSub />
			Enter up to 5 subtasks
		</h2>

		<div class="mb-3 flex w-full gap-3">
			<div class="formkit-fields mb-3 flex w-full items-center">
				<div class="formkit-field relative mr-3 flex-grow">
					<input
						bind:value={newContent}
						class="formkit-input block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:border-blue-500 focus:ring-blue-500"
						placeholder="Enter a goal..."
						required
						type="text"
					/>
				</div>
				<button type="button" on:click={addGoal} class="formkit-submit">
					<span
						class="cursor-pointer rounded-lg bg-blue-700 px-5 py-3 text-center text-sm font-medium text-white hover:bg-blue-800"
					>
						Add
					</span>
				</button>
			</div>
		</div>

		<div class="relative overflow-x-auto shadow-md sm:rounded-lg">
			{#if goals.length === 0}
				<div class="flex items-center justify-center py-4">
					<Badge border>
						<LoadingAnimation />
						<span class="ml-4"> Creating subtasks... </span>
					</Badge>
				</div>
			{:else}
				<table
					id="dynamicTable"
					class="w-full text-left text-sm text-gray-500 rtl:text-right dark:text-gray-400"
				>
					<thead
						class="bg-gray-50 text-xs uppercase text-gray-700 dark:bg-gray-700 dark:text-gray-400"
					>
						<tr>
							<th scope="col" class="px-6 py-3">ID</th>
							<th scope="col" class="px-6 py-3">Content</th>
							<th scope="col" class="px-6 py-3"
								><span class="sr-only">Edit</span></th
							>
						</tr>
					</thead>
					<tbody>
						{#each goals as data, index}
							<tr>
								<td class="px-6 py-4">{index + 1}</td>
								<td class="px-6 py-4">
									{#if editIndex === index}
										<input
											type="text"
											bind:value={editContent}
											class="rounded border border-gray-300 p-2 text-xs"
										/>
									{:else}
										{data}
									{/if}
								</td>
								<td class="gap-4 px-6 py-4">
									{#if editIndex === index}
										<button
											on:click={() => saveEdit(index)}
											class="mx-2 rounded bg-gray-100 px-4 py-1 text-green-500 hover:text-green-700"
											>Save</button
										>

										<button
											on:click={cancelEdit}
											class="mx-2 rounded bg-gray-100 px-4 py-1 text-blue-500 hover:text-blue-700"
											>Cancel</button
										>
									{:else}
										<button
											on:click={() => startEdit(index)}
											class="mx-2 px-4 py-1 text-blue-500 hover:text-blue-700"
											>Edit</button
										>
										<button
											on:click={() => deleteGoal(index)}
											class="mx-2 ml-4 rounded bg-gray-100 px-4 py-1 text-red-500 hover:text-red-700"
											>Delete</button
										>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
		</div>
	</div>

	<div class="absolute bottom-2 right-7 gap-x-6">
		<button
			type="button"
			class="mr-4 px-2 text-sm/6 font-semibold text-gray-900"
			on:click={() => {
				dispatch("returnToPrev");
			}}>Cancel</button
		>
		<button
			type="button"
			class="rounded-md bg-blue-700 px-3 px-8 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
			on:click={() => save()}>Create</button
		>
	</div>
</div>
