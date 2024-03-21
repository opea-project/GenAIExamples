<script lang="ts">
	export let time: string;
	import { createEventDispatcher } from "svelte";

	let dispatch = createEventDispatcher();
</script>

<div class="ml-2 flex flex-col">
	<div class="my-4 flex items-center justify-end gap-2 space-x-2">
		<div class="ml-2 w-min cursor-pointer" data-state="closed">
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<svg
				xmlns="http://www.w3.org/2000/svg"
				xml:space="preserve"
				viewBox="0 0 21.6 21.6"
				width="24"
				height="24"
				class="w-5 fill-[#0597ff] hover:fill-[#0597ff]"
				on:click={() => {
					dispatch("handleTop");
				}}
				><path
					d="M2.2 3.6V.8h17.2v2.8zm7.2 17.2V10.4L5.8 14l-1.9-1.9 6.9-6.9 6.9 6.9-1.9 1.9-3.6-3.6v10.4z"
				/></svg
			>
		</div>
		<div
			class="inline-block w-0.5 self-stretch bg-gray-300 opacity-100 dark:opacity-50"
		/>
		<div class="w-min cursor-pointer" data-state="closed">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				xml:space="preserve"
				viewBox="0 0 21.6 21.6"
				width="24"
				height="24"
				class="w-5 fill-[#0597ff] hover:fill-[#0597ff]"
				><path d="M12.3 17.1V7.6H7.6v2.8h1.9v6.7H6.4v2.7h8.8v-2.7z" /><circle
					cx="10.8"
					cy="3.6"
					r="1.9"
				/></svg
			>
		</div>
		<div class="flex items-center space-x-1 text-base text-gray-800">
			<strong>End to End Time: </strong>
			<p>{time}s</p>
		</div>
	</div>
	<div class="ml-2 flex flex-col" />
</div>
