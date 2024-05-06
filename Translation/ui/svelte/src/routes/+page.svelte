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
  import Header from "$lib/header.svelte";
  import { fetchLanguageResponse } from "$lib/shared/Network.js";
  import type { Language } from "./types.js";
  import { languagesList } from "$lib/shared/constant.js";
  import LoadingAnimation from "$lib/assets/loadingAnimation.svelte";

  // Set default language
  let langFrom: string = "en";
  let langTo: string = "zh";
  let languages: Language[] = languagesList;
  // Initialize disabled state of input
  let inputDisabled: boolean = false;
  // Initialize input and output
  let input: string = "";
  let output: string = "";
  let loading = false;

  async function handelTranslate() {
    loading = true;
    const res = await fetchLanguageResponse(input, langFrom, langTo);
    if (res) {
      output = res.target_language;
      loading = false;
    }
  }

  let timer;

  $: if ((input || langFrom || langTo) && input !== "") {
    if (langFrom === langTo) {
      output = input;
    } else {
      clearTimeout(timer);
      timer = setTimeout(handelTranslate, 1000);
    }
  }
</script>

<div>
  <Header />
  <div class="mt-10 flex flex-col items-center">
    <div class="w-[70%]">
      <div class="flex items-center mx-2">
        <select
          class="p-4 m-2 shadow-md rounded w-full border-[#0000001f] hover:border-[#0054ae]"
          name="lang-from"
          id="lang-from"
          bind:value={langFrom}
        >
          {#each languages as language}
            <option value={language.shortcode}
              >{#if language.flagUnicode}{language.flagUnicode} |
              {/if}{language.name}</option
            >
          {/each}
        </select>

        <select
          class="p-4 m-2 shadow-md rounded w-full border-[#0000001f] hover:border-[#0054ae]"
          name="lang-to"
          id="lang-to"
          bind:value={langTo}
        >
          {#each languages as language}
            <option value={language.shortcode}
              >{#if language.flagUnicode}{language.flagUnicode} |
              {/if}{language.name}</option
            >
          {/each}
        </select>
      </div>
      <div class="translate-textareas">
        <textarea
          class="grow"
          disabled={inputDisabled}
          name="input"
          id="translateinput"
          rows="25"
          placeholder="Input"
          bind:value={input}
        />
        <textarea
          readonly
          name="output"
          class="bg-[#f5f5f5] grow disabled"
          id="translateoutput"
          rows="25"
          placeholder="Translation"
          bind:value={output}
        />
      </div>
    </div>
    {#if loading}
      <LoadingAnimation />
    {/if}
  </div>
</div>

<style>
  .translate-textareas {
    padding: 8px;
    display: flex;
    flex-direction: row;
    align-items: center;
    width: 100%;
  }

  textarea {
    resize: none;
    margin: 8px;
    padding: 8px;

    font-size: 16px;

    border-radius: 12px;
    border: solid rgba(128, 0, 128, 0) 4px;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.19);

    transition: 0.1s linear;
  }

  #translateinput:hover {
    border: solid #0054ae 4px;
  }
</style>
