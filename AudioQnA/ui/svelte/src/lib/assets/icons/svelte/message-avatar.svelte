<script lang="ts">
	import PersonOutlined from "$lib/assets/icons/svelte/portrait.svelte";
	import AssistantIcon from "$lib/assets/icons/svelte/assistant.svelte";
	export let role: string;

</script>

{#if role === "Human"}
	<PersonOutlined />
{:else}
	<AssistantIcon />
{/if}
