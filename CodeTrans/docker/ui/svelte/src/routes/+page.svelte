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
  import Highlight, { LineNumbers } from "svelte-highlight";
  import typescript from "svelte-highlight/languages/typescript";
  import c from "svelte-highlight/languages/c";
  import cpp from "svelte-highlight/languages/cpp";
  import csharp from "svelte-highlight/languages/csharp";
  import go from "svelte-highlight/languages/go";
  import java from "svelte-highlight/languages/java";
  import python from "svelte-highlight/languages/python";
  import javascript from "svelte-highlight/languages/javascript";
  import swift from "svelte-highlight/languages/swift";
  import ruby from "svelte-highlight/languages/ruby";
  import rust from "svelte-highlight/languages/rust";
  import php from "svelte-highlight/languages/php";
  import kotlin from "svelte-highlight/languages/kotlin";
  import objectivec from "svelte-highlight/languages/objectivec";
  import perl from "svelte-highlight/languages/perl";
  import matlab from "svelte-highlight/languages/matlab";
  import r from "svelte-highlight/languages/r";
  import lua from "svelte-highlight/languages/lua";
  import bash from "svelte-highlight/languages/bash";
  import sql from "svelte-highlight/languages/sql";

  import atomOneDark from "svelte-highlight/styles/atom-one-dark";
  import Header from "$lib/header.svelte";
  import { fetchTextStream } from "$lib/shared/Network.js";
  import type { Language } from "./types.js";
  import { languagesList } from "$lib/shared/constant.js";
  import LoadingAnimation from "$lib/assets/loadingAnimation.svelte";
  import TranslateIcon from "$lib/assets/translateIcon.svelte";

  const languagesTag = {
    Typescript: typescript,
    Python: python,
    C: c,
    Cpp: cpp,
    Csharp: csharp,
    Go: go,
    Java: java,
    Javascript: javascript,
    Swift: swift,
    Ruby: ruby,
    Rust: rust,
    Php: php,
    Kotlin: kotlin,
    Objectivec: objectivec,
    Perl: perl,
    Matlab: matlab,
    R: r,
    Lua: lua,
    Bash: bash,
    Sql: sql,
  } as { [key: string]: any };

  let copyText = "copy";
  // Set default language
  let langFrom: string = "Python";
  let langTo: string = "Go";
  let languages: Language[] = languagesList;
  // Initialize disabled state of input
  let inputDisabled: boolean = false;
  // Initialize input and output
  let input: string = "";
  let output: string = "";
  let timer: number;
  let loading = false;
  let deleteFlag: boolean = false;
  let inputClick: boolean = true;

  function handelCopy() {
    navigator.clipboard.writeText(output);
    copyText = "copied!";
    setTimeout(() => {
      copyText = "copy";
    }, 1000);
  }

  function handelInputClick() {
    inputClick = !inputClick;
  }

  const handelTranslate = async () => {
    loading = true;
    output = "";
    inputClick = false;
    const eventSource = await fetchTextStream(input, langFrom, langTo);

    eventSource.addEventListener("message", (e: any) => {
      let Msg = e.data;
      console.log('Msg', Msg);

      if (Msg.startsWith("b")) {
        const trimmedData = Msg.slice(2, -1);
        if (trimmedData.includes("'''")) {
          deleteFlag = true;
        } else if (deleteFlag && trimmedData.includes("\\n")) {
          deleteFlag = false;
        } else if (trimmedData !== "</s>" && !deleteFlag) {
          output += trimmedData.replace(/\\n/g, "\n");
        }
      } else if (Msg === "[DONE]") {
        deleteFlag = false;
        loading = false;
      }
    });
    eventSource.stream();
  };

  $: if ((input || langFrom || langTo) && input !== "") {
    clearTimeout(timer);
    timer = setTimeout(handelTranslate, 1000);
  } else {
    handelTranslate;
  }
</script>

<svelte:head>
  {@html atomOneDark}
</svelte:head>

<div>
  <Header />
  <div class="mt-4 flex flex-col items-center">
    <div class="w-[70%] rounded shadow-2xl p-8">
      <div class="flex flex-row gap-4 mx-4 pb-4 border-b-2">
        <TranslateIcon />
        Select Language
      </div>
      <div class="flex items-center">
        <select
          class="p-4 m-2 w-full border-none"
          name="lang-from"
          id="lang-from"
          bind:value={langFrom}
        >
          {#each languages as language}
            <option value={language.name}>{language.name}</option>
          {/each}
        </select>

        <select
          class="p-4 m-2 w-full border-none"
          name="lang-to"
          id="lang-to"
          bind:value={langTo}
        >
          {#each languages as language}
            <option value={language.name}>{language.name}</option>
          {/each}
        </select>
      </div>
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <div class="grid grid-cols-2 gap-4">
        {#if inputClick}
          <textarea
            class="grow bg-[#011627] text-white"
            disabled={inputDisabled}
            name="input"
            id="translateinput"
            rows="25"
            placeholder="Input"
            bind:value={input}
            data-testid="code-input"
          />
        {:else}
          <div
            class="bg-[#011627] rounded overflow-auto code-format-style"
            on:click={() => {
              handelInputClick();
            }}
          >
            <Highlight
              language={languagesTag[langFrom]}
              code={input}
              let:highlighted
            >
              <LineNumbers {highlighted} wrapLines hideBorder />
            </Highlight>
          </div>
        {/if}

        <div
          class="h-[40rem] bg-[#011627] rounded overflow-auto code-format-style divide-y hiddenScroll"
          data-testid="code-output"
        >
          {#if output !== ""}
            <div class="bg-[#282c34] p-2 px-6 text-white flex justify-end border-2 border-none border-b-gray-800">
              <button
                class="border px-3 py-1 rounded border-none"
                on:click={() => {
                  handelCopy();
                }}>{copyText}</button
              >
            </div>
            <Highlight
              language={languagesTag[langTo]}
              code={output}
              let:highlighted
            >
              <LineNumbers {highlighted} wrapLines hideBorder />
            </Highlight>
          {/if}
        </div>
      </div>
    </div>
    {#if loading}
      <LoadingAnimation />
    {/if}
  </div>
</div>

<style>
  textarea,
  .code-format-style {
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
    border: solid #91c6ff 4px;
  }

  .hiddenScroll::-webkit-scrollbar {
    display: none;
  }

  .hiddenScroll {
    -ms-overflow-style: none; /* IE and Edge */
    scrollbar-width: none; /* Firefox */
  }
</style>
