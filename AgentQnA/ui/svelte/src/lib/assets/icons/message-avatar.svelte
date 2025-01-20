<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import PersonOutlined from "$lib/assets/icons/portrait.svelte";
	import AssistantIcon from "$lib/assets/icons/assistant.svelte";

	export let role: string;
</script>

{#if role === "Assistant"}
	<AssistantIcon />
{:else}
	<PersonOutlined />
{/if}
