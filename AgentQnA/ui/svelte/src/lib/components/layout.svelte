<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { open } from '$lib/components/shared/store';
	import Overlay from '$lib/components/shared/overlay.svelte';
	import Notifications from "svelte-notifications";

	const style = {
		container: `bg-gray-100 h-screen overflow-hidden relative`,
		main: `h-screen overflow-auto p-4 md:pb-8 lg:px-4`,
		mainContainer: `flex flex-col h-screen pl-0 w-full bg-[#25252D]`
	};

	onMount(() => {
		document.getElementsByTagName('body').item(0).removeAttribute('tabindex');
	});

	if (browser) {
		page.subscribe(() => {
			// close side navigation when route changes
			$open = false;
		});
	}
</script>


<Notifications>
<div class={style.container}>
	<div class="flex items-start">
		<Overlay />
		<div class={style.mainContainer}>
			<main class={style.main}>
				<slot />
			</main>
		</div>
	</div>
</div>

</Notifications>
