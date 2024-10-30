<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import FolderIcon from "$lib/assets/DocManagement/folderIcon.svelte";
	import LinkfolderIcon from "$lib/assets/DocManagement/LinkfolderIcon.svelte";
	import { Button, Modal } from "flowbite-svelte";
	import SvelteTree from "$lib/shared/components/doc_management/treeView/svelte-tree.svelte";
	import FileIcon from "$lib/assets/DocManagement/fileIcon.svelte";
	import { createEventDispatcher } from "svelte";
	import DeleteIcon from "$lib/assets/upload/deleteIcon.svelte";
	import { deleteFiles } from "$lib/network/upload/Network";
	import { storageFiles } from "$lib/shared/stores/common/Store";
	import { getNotificationsContext } from "svelte-notifications";

	const { addNotification } = getNotificationsContext();

	let dispatch = createEventDispatcher();
	let showDirectory = false;
	let chooseDir = undefined;
	let currentIdx = 0;
	let deleteModal = false;
	/**
	 * @type {any}
	 */
	let currentFile;
	/**
	 * @type {number}
	 */
	let currentFileIdx;


	export let files = [];

	console.log("files", files);

	function handleDirClick(file, index) {
		chooseDir = file;
		showDirectory = true;
		currentIdx = index;
		console.log("chooseDir", chooseDir);
	}

	async function deleteCurrentFolder() {

		const res = await deleteFiles(currentFile);
		// succeed
		if (res.status) {
			$storageFiles = $storageFiles.filter((_, index) => index !== currentFileIdx);
			files = $storageFiles;
			showNotification("Deleted successfully", "success");

		} else {
			showNotification("Deletion failed", "success");

		}
	}

	function showNotification(text: string, type: string) {
		addNotification({
			text: text,
			position: "top-left",
			type: type,
			removeAfter: 3000,
		});
	}

	function deleteFileIdx(file, index) {
		currentFile = file;
		currentFileIdx = index;
		deleteModal = true;

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

<Modal bind:open={deleteModal} size="xs" autoclose>
	<div class="text-center">
		<h3 class="mb-5 text-lg font-normal text-gray-500">Confirm file deletion?</h3>
		<Button
			color="red"
			class="mr-2"
			on:click={() => { deleteCurrentFolder() }}>Yes, I'm sure</Button
		>
		<Button color="alternative"
			on:click={() => { deleteModal = false; }}
		>No, cancel</Button>
	</div>
</Modal>

<div class="grid max-h-[35rem] grid-cols-2 gap-5 overflow-auto mt-6">
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

			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<div
				class="absolute right-0 top-0 hidden group-hover:block"
				on:click={() => { deleteFileIdx(file.id, index)  }}
			>
				<DeleteIcon />
			</div>
		</div>
	{/each}
</div>
