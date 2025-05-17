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
	import { Drawer, Button, CloseButton, Tabs, TabItem } from "flowbite-svelte";
	import { InfoCircleSolid } from "flowbite-svelte-icons";
	import { sineIn } from "svelte/easing";
	import UploadFile from "./upload-knowledge.svelte";
	import PasteURL from "./PasteKnowledge.svelte";
	import {
		knowledge1,
		knowledgeName,
		storageFiles,
	} from "$lib/shared/stores/common/Store";
	import { getNotificationsContext } from "svelte-notifications";
	import {
		fetchAllFile,
		fetchKnowledgeBaseId,
		fetchKnowledgeBaseIdByPaste,
	} from "$lib/network/upload/Network";
	import DocCard from "../doc_management/docCard.svelte";
	import NoFile from "$lib/assets/upload/no-file.svelte";
	import LoadingButton from "$lib/assets/upload/loading-button.svelte";

	const { addNotification } = getNotificationsContext();

	$: files = $storageFiles ? $storageFiles : [];
	let hidden6 = true;
	let uploading = false;

	let transitionParamsRight = {
		x: 320,
		duration: 200,
		easing: sineIn,
	};

	async function handleKnowledgePaste(
		e: CustomEvent<{ pasteUrlList: string[] }>
	) {
		uploading = true;
		try {
			const pasteUrlList = e.detail.pasteUrlList;
			const res = await fetchKnowledgeBaseIdByPaste(pasteUrlList);
			handleUploadResult(res, "knowledge_base");
		} catch {
			handleUploadError();
		}
	}

	async function handleKnowledgeUpload(e: CustomEvent<any>) {
		uploading = true;
		try {
			const blob = await fetch(e.detail.src).then((r) => r.blob());
			const fileName = e.detail.fileName;
			const res = await fetchKnowledgeBaseId(blob, fileName);
			handleUploadResult(res, fileName);
		} catch {
			handleUploadError();
		}
	}

	async function handleUploadResult(res: Response, fileName: string) {
		if (res.status === 200) {
			knowledge1.set({ id: "default" });
			knowledgeName.set(fileName);
			showNotification("Uploaded successfully", "success");
			// update fileStructure
			const res = await fetchAllFile();
			uploading = false;
			console.log('handleUploadResult', res);

			if (res) {
				storageFiles.set(res);
				files = $storageFiles;
			}
		} else {
			showNotification("Uploaded failed", "error");
		}
	}

	function handleUploadError() {
		showNotification("Uploaded failed", "error");
	}

	function showNotification(text: string, type: string) {
		addNotification({
			text: text,
			position: "top-left",
			type: type,
			removeAfter: 3000,
		});
	}
</script>

<div class="text-center">
	<Button
		on:click={() => (hidden6 = false)}
		class="bg-transparent focus-within:ring-gray-300 hover:bg-transparent focus:ring-0"
		data-testid="open-upload"
	>
		<svg
			aria-hidden="true"
			class="h-7 w-7 text-blue-700"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
			><path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
			/></svg
		>
	</Button>
</div>

<Drawer
	backdrop={false}
	placement="right"
	transitionType="fly"
	transitionParams={transitionParamsRight}
	bind:hidden={hidden6}
	class=" border-2 border-b-0 border-r-0 shadow"
	id="sidebar6"
>
	<div class="flex items-center">
		<h5
			id="drawer-label"
			class="mb-4 inline-flex items-center text-base font-semibold text-gray-500 dark:text-gray-400"
		>
			<InfoCircleSolid class="me-2.5 h-4 w-4" />Data Source
		</h5>
		<CloseButton
			on:click={() => (hidden6 = true)}
			class="mb-4 dark:text-white"
		/>
	</div>
	<p class="mb-6 text-sm text-gray-500 dark:text-gray-400">
		Please upload your local file or paste a remote file link, and Chat will
		respond based on the content of the uploaded file.
	</p>

	<Tabs
		style="full"
		defaultClass="flex rounded-lg divide-x rtl:divide-x-reverse divide-gray-200 shadow dark:divide-gray-700 focus:ring-0"
	>
		<TabItem class="w-full" open>
			<span slot="title">Upload File</span>
			<UploadFile on:upload={handleKnowledgeUpload} />
		</TabItem>
		<TabItem class="w-full" data-testid="exchange-paste">
			<span slot="title">Paste Link</span>
			<PasteURL on:paste={handleKnowledgePaste} />
		</TabItem>
	</Tabs>
	{#if uploading}
		<div class="flex flex-col items-center justify-center my-6">
			<LoadingButton />
		</div>
	{/if}

	{#if files.length > 0}
		<DocCard {files} />
	{:else}
		<div class="flex flex-col items-center justify-center mt-6">
			<NoFile />
			<p class=" text-sm opacity-70">No files uploaded</p>
		</div>
	{/if}
</Drawer>
