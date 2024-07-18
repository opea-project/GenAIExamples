<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script>
	import FolderIcon from "$lib/assets/DocManagement/folderIcon.svelte";
	import LinkfolderIcon from "$lib/assets/DocManagement/LinkfolderIcon.svelte";
	import { Modal } from "flowbite-svelte";
	import SvelteTree from "$lib/shared/components/doc_management/treeView/svelte-tree.svelte";
	import FileIcon from "$lib/assets/DocManagement/fileIcon.svelte";
	import { createEventDispatcher } from "svelte";

	let dispatch = createEventDispatcher();
	let showDirectory = false;
	let chooseDir = undefined;
	let currentIdx = 0;

	export let files = [];

	console.log("files", files);

	function handleDirClick(file, index) {
		chooseDir = file;
		showDirectory = true;
		currentIdx = index;
		console.log("chooseDir", chooseDir);
	}


</script>

<Modal
	bind:open={showDirectory}
	size="xs"
	autoclose={true}
	class="z-50 w-full"
	outsideclose
>
	<hr class="my-8 h-px border-0 bg-gray-200 dark:bg-gray-700" />
	<SvelteTree data={chooseDir.children} {currentIdx} />

</Modal>

<div class="grid grid-cols-2 gap-5 max-h-[35rem]  overflow-auto">
	{#each files as file, index}
		<div
			class="group relative flex w-full flex-col items-center justify-center p-2 px-12 text-center hover:bg-[#d9eeff] focus:bg-[#d9eeff]"
		>
			{#if file.type === "File"}
				<div class="flex-shrink-0">
					<FileIcon />
				</div>
				<p class="w-[6rem] truncate">
					{file.name}
				</p>
			{:else if file.type === "Directory" && file.id === "uploaded_links"}
				<button
					class="flex flex-col items-center"
					on:click={() => handleDirClick(file, index)}
				>
					<div class="flex-shrink-0">
						<LinkfolderIcon />
					</div>
					<p class="truncate">
						{file.name}
					</p>
				</button>
			{:else}
				<button
					class="flex flex-col items-center"
					on:click={() => handleDirClick(file, index)}
				>
					<div class="flex-shrink-0">
						<FolderIcon />
					</div>
					<p class="truncate">
						{file.name}
					</p>
				</button>
			{/if}
		</div>
	{/each}
</div>
