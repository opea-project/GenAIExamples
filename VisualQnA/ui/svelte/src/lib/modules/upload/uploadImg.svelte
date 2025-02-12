<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { base64ImageStore } from "$lib/shared/stores/common/Store";
	import { Dropzone } from "flowbite-svelte";
	import Pica from 'pica';

	let value = [];
	export let imageUrl = "";

	$: if (imageUrl !== "") {
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
        const base64Data = reader.result;
        const fileType = file.type;

        if (!fileType.includes("png")) {
            convertImageToPNG(base64Data); // Convert if not PNG
        } else {
            base64ImageStore.set(base64Data); // Store Base64
        }

        imageUrl = URL.createObjectURL(file); // Create URL for preview
    };
    reader.readAsDataURL(file); // Read file as Data URL
};

const convertImageToPNG = async (base64Data) => {
    if (!base64Data || !base64Data.startsWith("data:image/")) {
        console.error("Invalid Base64 data");
        return;
    }

    console.log("Starting image conversion...");

    const img = new Image();
    img.src = base64Data;

    img.onload = async () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        let width = img.width;
        let height = img.height;

        // Set resize factor to 1 (no scaling) to keep the original size
        const scaleFactor = 0.1; // Resize factor (keep original size)
        width = Math.floor(width * scaleFactor);
        height = Math.floor(height * scaleFactor);

        canvas.width = width;
        canvas.height = height;

        ctx.drawImage(img, 0, 0, width, height); // Draw the original image (no resizing)

        const outputCanvas = document.createElement("canvas");
        outputCanvas.width = width;
        outputCanvas.height = height;

        const pica = new Pica();

        try {
            // Resize and compress the image using Pica
            await pica.resize(canvas, outputCanvas);

            // Convert canvas to PNG format with data URL
            const pngDataUrl = outputCanvas.toDataURL("image/png", 0.8); // Adjust quality (0.9 is high, between 0-1)

            // Store the Base64 PNG image
            base64ImageStore.set(pngDataUrl);
        } catch (err) {
            console.error("Error during image processing:", err);
        }
    };

    img.onerror = (err) => {
        console.error("Error loading image:", err);
    };
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
