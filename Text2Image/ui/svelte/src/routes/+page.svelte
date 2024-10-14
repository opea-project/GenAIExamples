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
	import "driver.js/dist/driver.css";
	import "$lib/assets/layout/css/driver.css";
	import { imgList } from "$lib/shared/stores/common/Store";
	import Header from "$lib/shared/components/header/header.svelte";
	import LoadingAnimation from "$lib/shared/components/loading/Loading.svelte";
	import GenerateImg from "$lib/modules/imageList/GenerateImg.svelte";
	import { fetchImgList } from "$lib/network/Network";

	let query: string = "";
	let loading: boolean = false;
	let notNumber: boolean = false;
	let inputHint: boolean = false;
	let imgNum = 1;
	let numButtons = [1, 2, 4];
	let selectedButton = 1;
	let genImgNum: number;

	const selectButton = (button: number) => {
		selectedButton = button;
		imgNum = selectedButton;
		notNumber = false; // Reset notNumber when selecting a button
	};

	const selectInput = () => {
		selectedButton = 0;
		notNumber = false;
		verifyNum();
	};

	const updateInputHint = () => {
		if (query) {
			inputHint = false;
		}
	};

	const verifyNum = () => {
		if (/^\d+$/.test(genImgNum) && genImgNum > 0) {
			imgNum = genImgNum;
			notNumber = false;
		} else {
			notNumber = true;
		}
	};

	const generateImages = async () => {
		if (!query) {
			inputHint = true;
			return;
		};
		loading = true;
		imgList.set([]);

		await fetchImgList(query, imgNum).then((res) => {
			imgList.set(res.images)
			console.log('imgList', $imgList);

			loading = false;
		});
	};

	$: genImgNum && verifyNum();
	$: query && updateInputHint();
</script>

<div class="h-full w-full bg-gray-200">
	<Header />
	<div class="mx-auto mt-[2%] h-[85%] w-[90%] rounded-3xl bg-white p-8">
		<p class="text-3xl">AI Image Generator</p>
		<div class="relative my-6 w-full">
			<span class="absolute p-2 text-xs text-gray-500">Description prompt</span>
			<input
				class="block w-full rounded-xl border-gray-300 px-2 py-10 text-gray-900"
				type="text"
				data-testid="img-input"
				placeholder="What do you want to see?"
				disabled={loading}
				maxlength="1200"
				bind:value={query}
			/>
			{#if inputHint}
				<p class="absolute -bottom-[1rem] mt-2 text-xs text-red-600">
					Please input the details you want to describe!
				</p>
			{/if}
		</div>
		<div class="relative flex flex-row items-center justify-end gap-3">
			<span class="text-[0.8rem] text-gray-700">Number of images:</span>
			{#each numButtons as button}
				<button
					class="rounded-xl border px-6 py-1
					{selectedButton === button
						? 'border-2 border-[#1c64f2] outline-[#1c64f2] ring-2'
						: 'border-gray-600'}"
					on:click={() => selectButton(button)}
				>
					{button}
				</button>
			{/each}

			<input
				type="text"
				class="
				{selectedButton === 0
					? 'border-2 border-[#1c64f2] outline-[#1c64f2] ring-2'
					: 'border-gray-800'}
				focus:ring-none h-[2.1rem] w-[3.6rem] rounded-xl pl-2 text-center focus:outline-none"
				placeholder="?"
				on:focus={selectInput}
				bind:value={genImgNum}
			/>
			{#if notNumber}
				<p
					class="absolute -bottom-[1rem] right-[10rem] mt-2 text-xs text-red-600"
				>
					Enter a number greater than 0!
				</p>
			{/if}
			<button
				on:click={generateImages}
				type="submit"
				data-testid="img-gen"
				class="ml-12 bg-blue-600 px-8 py-3 text-base font-medium text-white hover:bg-blue-700 focus:ring-blue-800"
			>
				Generate ({imgNum})
			</button>
		</div>
		{#if loading}
			<LoadingAnimation />
		{:else if $imgList.length !== 0}
			<GenerateImg />
		{/if}
	</div>
</div>

<style>
	.row::-webkit-scrollbar {
		display: none;
	}

	.row {
		scrollbar-width: none;
		-ms-overflow-style: none;
	}
</style>
