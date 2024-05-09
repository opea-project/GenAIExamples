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
	import uploadFile from "$lib/assets/icons/svg/upload.svg";
	import {
		fetchAudioEmbedding,
		fetchAudioText,
	} from "$lib/modules/chat/network";
	import { getNotificationsContext } from "svelte-notifications";
	import { uploadName } from "./store";
	import LoadingButtonSpinnerIcon from "$lib/assets/icons/svelte/loading-button-spinner-icon.svelte";

	const { addNotification } = getNotificationsContext();
	let loading = false;

	async function handleInput(event: Event) {
		loading = true;
		const file = (event.target as HTMLInputElement).files![0];
		if (!file) return;

		const res = await fetchAudioText(file);
		if (res) {
			// upload
			const uploadRes = await fetchAudioEmbedding(file, res.asr_result);
			if (uploadRes.message === "Success") {
				uploadName.set(file.name);
				loading = false;
				addNotification({
					text: "Uploaded successfully",
					position: "bottom-center",
					type: "success",
					removeAfter: 3000,
				});
			}
		}
	}
</script>

<label for="audio">
	<div class="h-15 w-15 flex cursor-pointer flex-col justify-center rounded-md mr-10">
		{#if loading}
			<LoadingButtonSpinnerIcon />
			<p>uploading</p>
		{:else}
			<img class="swap-on h-8" src={uploadFile} alt="" />
			<p>{$uploadName}</p>
		{/if}
	</div>
</label>

<input
	id="audio"
	type="file"
	required
	on:change={handleInput}
	accept="audio/*"
/>

<style lang="postcss">
	input[type="file"] {
		display: none;
	}
</style>
