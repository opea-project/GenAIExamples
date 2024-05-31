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
	export let data;
	import { fetchTextStream } from "$lib/network/chat/Network";
	import LoadingAnimation from "$lib/shared/components/loading/Loading.svelte";
	import "driver.js/dist/driver.css";
	import "$lib/assets/layout/css/driver.css";
	import PaperAirplane from "$lib/assets/chat/svelte/PaperAirplane.svelte";
	import Output from "$lib/modules/chat/Output.svelte";

	let code_output: string = "";
	let query: string = "";
	let loading: boolean = false;
	let deleteFlag: boolean = false;

	const callTextStream = async (query: string) => {
		loading = true;
		code_output = "";
		const eventSource = await fetchTextStream(query);

		eventSource.addEventListener("message", (e: any) => {
			let Msg = e.data;
			console.log("Msg", Msg);

			if (Msg.startsWith("b")) {
				const trimmedData = Msg.slice(2, -1);
				if (trimmedData.includes("'''")) {
					deleteFlag = true;
				} else if (deleteFlag && trimmedData.includes("\\n")) {
					deleteFlag = false;
				} else if (trimmedData !== "</s>" && !deleteFlag) {
					code_output += trimmedData.replace(/\\n/g, "\n");
				}
			} else if (Msg === "[DONE]") {
				deleteFlag = false;
				loading = false;
				query = '';
			}
		});
		eventSource.stream();
	};

	const handleTextSubmit = async () => {
		await callTextStream(query);
	};
</script>

<div class="flex grow flex-col text-white">
	<div class="relative h-full items-center gap-5 bg-fixed sm:flex">
		<div
			class="relative mx-auto flex h-full w-full flex-col items-center sm:mt-0 sm:w-[70%]"
		>
			<div
				class="fixed relative flex w-full flex-col items-center justify-between bg-white p-2 pb-0"
			>
				<div class="relative my-4 flex w-full flex-row justify-center">
					<div class="relative w-full focus:border-none">
						<input
							class="block w-full break-words border-0 border-b-2 border-gray-300 px-1 py-4 pl-4 pr-20 text-xs
					text-gray-900 focus:border-gray-300 focus:ring-0 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500"
							type="text"
							data-testid="code-input"
							placeholder="Enter prompt here"
							disabled={loading}
							maxlength="1200"
							bind:value={query}
							on:keydown={(event) => {
								if (event.key === "Enter" && !event.shiftKey && query) {
									event.preventDefault();
									handleTextSubmit();
								}
							}}
						/>
						<button
							on:click={() => {
								if (query) {
									handleTextSubmit();
								}
							}}
							type="submit"
							id="send"
							class="absolute bottom-2.5 end-2.5 px-4 py-2 text-sm font-medium text-white dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
							><PaperAirplane /></button
						>
					</div>
				</div>
			</div>
			<div class="mb-4 flex h-full w-full flex-col items-center">
				{#if code_output !== ""}
					<div class="w-full items-center gap-4">
						<Output label="Generated results" output={code_output} />
					</div>
				{/if}
				{#if loading}
					<LoadingAnimation />
				{/if}
			</div>
		</div>
	</div>
</div>
