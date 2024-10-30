<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import AssistantIcon from "$lib/assets/chat/svelte/Assistant.svelte";
	import PersonOutlined from "$lib/assets/chat/svelte/PersonOutlined.svelte";
	import { MessageRole } from "$lib/shared/constant/Interface";
	export let role: MessageRole;


</script>

{#if role === MessageRole.User}
	<PersonOutlined />
{:else}
	<AssistantIcon />
{/if}
