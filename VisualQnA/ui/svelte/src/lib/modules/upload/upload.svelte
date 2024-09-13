<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { Hr, Label, Input } from "flowbite-svelte";
	import UploadImg from "./uploadImg.svelte";

	import { Range } from "flowbite-svelte";
	import { FilePasteSolid } from "flowbite-svelte-icons";
	import { stepValueStore } from "$lib/shared/stores/common/Store";
	let stepValue = 512;
    let imageUrl = '';

	$: stepValueStore.set(stepValue);
</script>

<div class="flex w-full flex-col gap-3 rounded-xl bg-white p-5">
	<p>Upload Images</p>
	<UploadImg imageUrl={imageUrl}/>
	<Hr classHr="my-8 w-64">or</Hr>
	<div class="mb-6">
		<Label for="input-group-1" class="block mb-2">Import from URL</Label>
		<Input type="text" placeholder=""  bind:value={imageUrl}>
		  <FilePasteSolid slot="left" class="w-5 h-5 text-gray-500 dark:text-gray-400" />
		</Input>
	  </div>
	<p>Parameters</p>
	<Range id="range-steps" min="0" max="1024" bind:value={stepValue} step="1" />
	<p>Max output tokens: {stepValue}</p>
</div>
