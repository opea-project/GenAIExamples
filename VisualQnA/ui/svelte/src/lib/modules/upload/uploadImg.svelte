<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { base64ImageStore } from "$lib/shared/stores/common/Store";
	import { Dropzone } from "flowbite-svelte";

	let value = [];
	export let imageUrl = "";

	$: if (imageUrl) {
		uploadImage();
	}

	const uploadImage = async () => {
		try {
			if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
				base64ImageStore.set(imageUrl);
				console.log("Image URL Stored:", imageUrl);
				return;
			}
		} catch (error) {
			console.error("Error converting image to Base64:", error);
		}
	};

	const dropHandle = (event) => {
		event.preventDefault();
		if (event.dataTransfer.items) {
			[...event.dataTransfer.items].forEach((item) => {
				if (item.kind === "file") {
					const file = item.getAsFile();
					if (file) {
						value = [file.name]; // Allow only one file selection
						readFileAsBase64(file); // Convert to Base64
					}
				}
			});
		} else {
			[...event.dataTransfer.files].forEach((file) => {
				value = [file.name]; // Allow only one file selection
				readFileAsBase64(file); // Convert to Base64
			});
		}
	};

	const handleChange = (event) => {
		const files = event.target.files;
		if (files.length > 0) {
			value = [files[0].name]; // Allow only one file selection
			readFileAsBase64(files[0]); // Convert to Base64
		}
	};

	const readFileAsBase64 = (file) => {
		const reader = new FileReader();
		reader.onload = () => {
			const base64Data = reader.result; // Get Base64 data
			base64ImageStore.set(base64Data); // Store the Base64 string in the store
			imageUrl = URL.createObjectURL(file); // Keep the object URL for preview
		};
		reader.readAsDataURL(file); // Read the file as a Data URL
	};

	const showFiles = (files) => {
		if (files.length === 1) return files[0];
		let concat = files.join(", ");
		if (concat.length > 40) concat = concat.slice(0, 40) + "...";
		return concat;
	};
</script>

<Dropzone
	id="dropzone"
	on:drop={dropHandle}
	on:dragover={(event) => {
		event.preventDefault();
	}}
	on:change={handleChange}
>
	{#if value.length === 0 && !imageUrl}
		<svg
			aria-hidden="true"
			class="mx-auto mb-3 h-10 w-10 text-gray-400"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
			/>
		</svg>
		<p class="mb-2 text-center text-sm text-gray-500 dark:text-gray-400">
			<span class="font-semibold">Click to upload</span> or drag and drop
		</p>
		<p class="text-center text-xs text-gray-500 dark:text-gray-400">
			SVG, PNG, JPG
		</p>
	{:else if imageUrl}
		<img src={imageUrl} alt="Uploaded Image" class="m-2 mx-auto block" />
	{/if}
</Dropzone>
