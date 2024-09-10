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
