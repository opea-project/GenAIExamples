<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
  import PaperAirplane from "$lib/assets/PaperAirplane.svelte";
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  let query: string = "";
  let loading: boolean = false;
</script>

<div
  class="fixed relative flex w-full flex-col items-center justify-between  p-2"
>
  <div class="relative my-4 flex w-full flex-row justify-center">
    <div class="focus:border-none relative w-full">
      <input
        class="text-md block w-full border-0 border-b-2 border-gray-300  px-1 py-4
						text-white placeholder-white focus:border-gray-300 focus:ring-0"
        type="text"
        placeholder="Enter prompt here"
        disabled={loading}
        maxlength="1200"
        bind:value={query}
        on:keydown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && query) {
            event.preventDefault();
            dispatch("handelSubmit", { query, loading});
          }
        }}
      />
      <button
        on:click={() => {
          if (query) {
            dispatch("handelSubmit", { query, loading});
          }
        }}
        type="submit"
        class="absolute bottom-2.5 end-2.5 px-4 py-2 text-sm font-medium text-white dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
        ><PaperAirplane /></button
      >
    </div>
  </div>
</div>
