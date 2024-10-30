<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { Button, Helper, Input, Label, Modal } from "flowbite-svelte";
	import { createEventDispatcher } from "svelte";

	const dispatch = createEventDispatcher();
	let formModal = false;
	let urlValue = "";

	function handelPasteURL() {
		const pasteUrlList = urlValue.split(";").map((url) => url.trim());
		dispatch("paste", { pasteUrlList });
		formModal = false;
	}
</script>

<Label class="space-y-1">
	<div class="grid grid-cols-3">
		<Input
			class="col-span-2 rounded-none rounded-l-lg focus:border-blue-700 focus:ring-blue-700"
			type="text"
			name="text"
			placeholder="URL"
			bind:value={urlValue}
			data-testid="paste-link"
		/>
		<Button
			type="submit"
			class="w-full rounded-none rounded-r-lg bg-blue-700"
			data-testid="paste-click"

			on:click={() => handelPasteURL()}>Confirm</Button
		>
	</div>

	<Helper>Use semicolons (;) to separate multiple URLs.</Helper>
</Label>
