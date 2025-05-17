<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { storageFiles } from "$lib/shared/stores/common/Store";
	import TreeNode from "./tree-node.svelte";
	import { createEventDispatcher } from "svelte";

	let dispatch = createEventDispatcher();
	type IData = {
		name: string;
		id: string;
		type: string;
		children: never[];
	};
	export let data: IData[] = [],
		collapse = false,
		onClick = "";

	export let currentIdx;

	function changeData() {
		console.log('change', $storageFiles);

		data = $storageFiles[currentIdx].children;
	}

	$: $storageFiles ? changeData() : console.log('No change', $storageFiles);

	console.log(data);
</script>

{#if data && data.length > 0}
	{#each data as item}
		<TreeNode
			bind:node={item}
			{collapse}
			{onClick}
			{currentIdx}
		/>
	{/each}
{:else}
	<p>Folder is empty. Please upload a file.</p>
{/if}
