<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
	import { imgList } from "$lib/shared/stores/common/Store";
</script>

<p class="my-2 text-2xl" data-testid="display-img">Result</p>

<div
	class="3xl:grid-cols-7 3xl:h-[45rem] mt-4 grid h-[26rem] grid-cols-5 gap-12 overflow-auto"
>
	{#each $imgList as img}
		<div class="h-[15rem]">
			<img
				src={"data:image/png;base64," + img}
				class="h-full max-h-[16rem] w-full rounded-3xl bg-gray-600"
				alt=""
			/>
		</div>
	{/each}
</div>
