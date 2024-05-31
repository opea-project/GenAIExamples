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
      <p>Summary</p>
    </div>
    {#if chatMessage === "" && $loading}
      <LoadingAnimation />
    {/if}
    <textarea
      id="editor"
      data-testid="display-answer"
      rows="15"
      class="xl:h-[50rem] tracking-tighter leading-loose block w-full px-2 font-medium text-sm text-gray-600 bg-white border-0 dark:bg-gray-800 focus:ring-0 dark:text-white dark:placeholder-gray-400"
      placeholder={chatMessage === "" && $loading
        ? ""
        : "Upload or paste content on the left."}
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
