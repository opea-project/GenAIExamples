<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import FileIcon from "$lib/assets/DocManagement/fileIcon.svelte";
	import FolderIcon from "$lib/assets/DocManagement/folderIcon.svelte";
	import LinkfolderIcon from "$lib/assets/DocManagement/LinkfolderIcon.svelte";
	import { createEventDispatcher } from "svelte";

	import { onMount } from "svelte";
	type IData = {
		name: string;
		id: string;
		type: string;
		children: never[];
		parent: IData;
		currentIdx: number;
	};
	export let node: IData,
		collapse = false,
		onClick = "",
		parent = "";

	export let currentIdx;

	let open = collapse;

	function toggleOpen() {
		open = !open;
	}

	function handleClickOpen() {
		toggleOpen();
	}

	onMount(() => {
		if (node) {
			node.parent = parent;
		}
	});


</script>

<li class="relative ml-5">
	<div
		class="my-2 flex items-center gap-4 {node.type === 'File' ? 'ml-5' : ''}"
	>
		<!-- link -->
		{#if node.type === "Directory"}
			{#if open}
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<svg
					on:click={handleClickOpen}
					data-testid="caret-down-node"
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 cursor-pointer"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
						clip-rule="evenodd"
					/>
				</svg>
			{:else}
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<svg
					on:click={handleClickOpen}
					data-testid="caret-up-node"
					xmlns="http://www.w3.org/2000/svg"
					class="h-5 w-5 cursor-pointer"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						fill-rule="evenodd"
						d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
						clip-rule="evenodd"
					/>
				</svg>
			{/if}
			{#if node.id === "uploaded_links"}
				<LinkfolderIcon className={"w-12 h-12"} />
			{:else}
				<FolderIcon className={"w-12 h-12"} />
			{/if}
		{:else}
			<FileIcon className={"w-10 h-10"} />
		{/if}
		<!-- link -->

		<span>{node?.name}</span>
	</div>

	{#if open && node.type === "Directory"}
		<ul>
			{#each node.children as child}
				<svelte:self
					bind:node={child}
					bind:parent={node}
					{collapse}
					{onClick}
				/>
			{/each}
		</ul>
	{/if}
</li>
