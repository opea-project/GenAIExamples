<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import TreeBranch from "./tree-branch.svelte";
	import { createEventDispatcher } from "svelte";

	let dispatch = createEventDispatcher();
	type IData = {
		name: string;
		id: string;
		type: string;
		children: never[];
	};

	export let currentIdx;

	export let collapse = false,
		data: IData[] = [],
		onClick = "";

	console.log("data", data);
</script>

<div>
	{#if data && data.length > 0}
		<ul>
			<TreeBranch {data} {collapse} {onClick} {currentIdx} />
		</ul>
	{:else}
		<p>Folder is empty. Please upload a file.</p>
	{/if}
</div>
