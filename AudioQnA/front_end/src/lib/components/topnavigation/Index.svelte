<script>
	import UploadVoice from "../talkbot/upload-voice.svelte";
</script>

<header
	class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-[#0054ae]"
>
	<nav
		class="w-full divide-gray-200 border-gray-200 bg-[#0054ae] px-4 py-1.5 text-gray-500 dark:text-gray-400 sm:px-4"
	>
		<div class="mx-auto flex w-full flex-wrap items-center justify-between">
			<span
				class="ml-4 self-center whitespace-nowrap py-2 text-3xl font-semibold text-white"
				>AudioQnA</span
			>
			<UploadVoice />
		</div>
	</nav>
</header>
