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
	import MessageAvatar from "$lib/modules/chat/MessageAvatar.svelte";
	import type { Message } from "$lib/shared/constant/Interface";
	import MessageTimer from "./MessageTimer.svelte";
	import { createEventDispatcher } from "svelte";

	let dispatch = createEventDispatcher();

	export let msg: Message;
	export let time: string = "";
</script>

<div
	class={msg.role === 0
		? "flex w-full gap-3"
		: "flex w-full items-center gap-3"}
	data-testid={msg.role === 0
		? "display-answer"
		: "display-question"}
>
	<div
		class={msg.role === 0
			? "flex aspect-square w-[3px]  items-center justify-center rounded bg-[#0597ff] max-sm:hidden"
			: "flex aspect-square h-10 w-[3px] items-center justify-center rounded bg-[#000] max-sm:hidden"}
	>
		<MessageAvatar role={msg.role} />
	</div>
	<div class="group relative items-center">
		<div>
			<p
				class=" max-w-[60vw] items-center whitespace-pre-line break-keep text-[0.8rem] leading-5 sm:max-w-[60rem]"
			>
				{@html msg.content}
			</p>
		</div>
	</div>
</div>
{#if time}
	<div>
		<MessageTimer
			{time}
			on:handleTop={() => {
				dispatch("scrollTop");
			}}
		/>
	</div>
{/if}

<style>
	.wrap-style {
		word-wrap: break-word;
		word-break: break-all;
	}
</style>
