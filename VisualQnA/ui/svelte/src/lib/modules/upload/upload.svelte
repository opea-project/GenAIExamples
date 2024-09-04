<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { Card, Button, Hr, Label, Input } from "flowbite-svelte";
	import UploadImg from "./uploadImg.svelte";
	import { Tooltip } from "flowbite-svelte";

	import { Range } from "flowbite-svelte";
	import Help from "$lib/assets/upload/help.svelte";
	import { EnvelopeSolid } from "flowbite-svelte-icons";
	let stepValue = 512;
	let UseShow = false;
</script>

<div class="flex w-full flex-col gap-3 rounded-xl bg-white p-5">
	<p>Upload Images</p>
	<UploadImg />
	<Hr classHr="my-8 w-64">or</Hr>
	<div class="mb-6">
		<Label for="input-group-1" class="block mb-2">Import from URL</Label>
		<Input id="email" type="email" placeholder="name@flowbite.com">
		  <EnvelopeSolid slot="left" class="w-5 h-5 text-gray-500 dark:text-gray-400" />
		</Input>
	  </div>
	<p>Parameters</p>
	<Range id="range-steps" min="0" max="1024" bind:value={stepValue} step="1" />
	<p>Max output tokens: {stepValue}</p>
	<div class="flex flex-row justify-between pb-4">
		<button
			class="text-#eee gap-2 bg-white  p-0 hover:bg-[white] flex flex-row items-center"
			on:click={() => {
				UseShow = !UseShow;
			}}><Help />Help Centre</button
		>
		<div class="mt-4 flex space-x-3">
			<Button color="light" class="dark:text-white">Cancel</Button>
			<Button>Done</Button>
		</div>
	</div>
</div>

{#if UseShow}
	<div class="mt-5 flex w-full flex-col gap-3 rounded-xl bg-white p-5">
		<p>Terms of use</p>
		<p>
			By using this service, users are required to agree to the following terms:
			The service is a research preview intended for non-commercial use only. It
			only provides limited safety measures and may generate offensive content.
			It must not be used for any illegal, harmful, violent, racist, or sexual
			purposes. The service may collect user dialogue data for future research.
			Please click the "Flag" button if you get any inappropriate answer! We
			will collect those to keep improving our moderator. For an optimal
			experience, please use desktop computers for this demo, as mobile devices
			may compromise its quality.
		</p>
	</div>
{/if}
