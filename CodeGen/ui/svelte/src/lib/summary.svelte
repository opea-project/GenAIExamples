<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
  import LoadingAnimation from "./assets/loadingAnimation.svelte";
  import SummaryLogo from "./assets/summaryLogo.svelte";
  import { loading } from "./shared/Store.js";

  export let chatMessage: any;
</script>

<form>
  <div
    class="text-white w-full mb-4 border border-[#0054ae] bg-gray-50 dark:bg-gray-700 dark:border-gray-600"
  >
    <div
      class="h-full flex flex-row bg-[#0054ae] items-center border-b dark:border-gray-600"
    >
      <div class="bg-[#00285a] w-4 h-8"></div>

      <button
        type="button"
        class="p-2 text-white rounded cursor-pointer dark:text-gray-400"
      >
        <SummaryLogo />
        <span class="sr-only">Timeline</span>
      </button>
      <p>Code Gen</p>
    </div>
    {#if chatMessage === "" && $loading}
      <LoadingAnimation />
    {/if}
    <textarea
      id="editor"
      rows="15"
      class="xl:h-[40rem] tracking-tighter leading-loose block w-full px-2 font-medium text-sm text-gray-600 bg-white border-0 dark:bg-gray-800 focus:ring-0 dark:text-white dark:placeholder-gray-400"
      placeholder={chatMessage === "" && $loading
        ? ""
        : "Generate the corresponding code according to the prompts."}
      required
      bind:value={chatMessage}
    />
  </div>
</form>

<style>
  .custom-textarea {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .custom-textarea::-webkit-scrollbar {
    display: none;
  }
</style>
