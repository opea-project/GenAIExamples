<script>
	import TopNavigation from '$lib/components/topnavigation/Index.svelte';

	const style = {
		container: `bg-gray-100 h-screen overflow-hidden relative`,
		main: `h-screen overflow-auto pb-36 pt-4 px-2 md:pb-8 lg:px-4`,
		mainContainer: `flex flex-col h-screen  w-full `
	};

</script>

<div class={style.container}>
	<div class="flex items-start">
		<div class={style.mainContainer}>
			<TopNavigation />
			<main class={style.main}>
				<slot />
			</main>
		</div>
	</div>
</div>
