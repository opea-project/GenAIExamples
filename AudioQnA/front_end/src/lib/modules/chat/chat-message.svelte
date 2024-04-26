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
	import MessageTimer from "./message-timer.svelte";
	import ChatAudio from "./chat-audio.svelte";
	import MessageAvatar from "$lib/assets/icons/svelte/message-avatar.svelte";

	export let type: string;
	export let message: string;
	export let displayTimer: Boolean = true;

</script>

<div
	class="flex w-full mt-4 space-x-3 {type === 'Human' || type === 'user'
		? 'ml-auto justify-end'
		: ''}"
>
	{#if type === "Assistant" || type === "assistant" || type === "system"}
		<div class="w-[3px] items-center justify-center rounded bg-[#0597ff]">
		</div>
	{/if}
	<div class="relative group">
		<div
			class={type === "Human" || type === "user"
				? "bg-blue-600 text-white p-3 rounded-l-lg rounded-br-lg wrap-style"
				: "border-2 p-3 rounded-r-lg rounded-bl-lg wrap-style"}
		>
			{#if message.includes("blob:")}
				<ChatAudio src={message} />
			{:else}
				<p class="text-sm message max-w-md line">{message}</p>
			{/if}
		</div>
		{#if displayTimer}
			<MessageTimer />
		{/if}
	</div>
	{#if type === "Human" || type === "user"}
		<div class="w-[3px] items-center justify-center rounded bg-[#000]">
		</div>
	{/if}
</div>

<style>
	.wrap-style {
		width: 100%;
		height: auto;
		word-wrap: break-word;
		word-break: break-all;
	}

	audio::-webkit-media-controls-panel {
		background-color: rgb(37 99 235);
	}

</style>
