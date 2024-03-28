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
  import { Dropzone } from "flowbite-svelte";
  import ImgLogo from "./assets/imgLogo.svelte";
  import { kb_id } from "./shared/Store.js";
  import { fetchKnowledgeBaseId } from "./shared/Network.js";

  let uploadInput: HTMLInputElement;
  let uploadFileName = '';


  function handleInput(event: Event) {
    const file = (event.target as HTMLInputElement).files![0];

    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = async () => {
      if (!reader.result) return;
      const src = reader.result.toString();
      const blob = await fetch(src).then((r) => r.blob());
      const fileName = file.name;
      uploadFileName = fileName;
      const res = await fetchKnowledgeBaseId(blob, fileName);
      kb_id.set(res.document_id);
      console.log("upload File", $kb_id);
    };
    reader.readAsDataURL(file);
  }
</script>

<div class="flex items-center justify-center w-full xl:my-12">
  <label
    for="dropzone-file"
    class="xl:h-[30rem] flex flex-col items-center justify-center w-full sm:h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600"
  >
    <div class="flex flex-col items-center justify-center pt-5 pb-6">
      <svg
        class="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400"
        aria-hidden="true"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 20 16"
      >
        <path
          stroke="currentColor"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
        />
      </svg>
      {#if uploadFileName === ''}
        <p class="mb-2 text-sm text-gray-500 dark:text-gray-400">
          <span class="font-semibold">Click to upload</span> or drag and drop
        </p>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          PDF, TXT, .Doc and so on
        </p>
      {:else}
        <p>{uploadFileName}</p>
      {/if}
    </div>
    <input
      id="dropzone-file"
      bind:this={uploadInput}
      type="file"
      class="hidden"
      accept=".doc, .docx, .pdf, .xls, .xlsx, .txt, .json, application/pdf, application/msword, application/vnd.ms-excel, text/plain, application/json"
      required
      on:change={handleInput}
    />
  </label>
</div>
