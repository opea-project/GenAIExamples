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
  import Doc from "$lib/doc.svelte";
  import Summary from "$lib/summary.svelte";
  import { fetchTextStream } from "$lib/shared/Network.js";
  import { loading } from "$lib/shared/Store.js";
  import { onMount } from "svelte";
  import { scrollToBottom } from "$lib/shared/Utils.js";

  let messages = '';
  let scrollToDiv: HTMLDivElement;

  onMount(() => {
    scrollToDiv = document
		.querySelector("#editor")!
    console.log('scrollToDiv', scrollToDiv);

  })

  const callTextStream = async (
    query: string,
    urlSuffix: string,
    params: string
  ) => {
    messages = "";
    const eventSource = await fetchTextStream(query, urlSuffix, params);

    eventSource.addEventListener("message", (e: any) => {
      let Msg = e.data;
      if (Msg !== "[DONE]") {
        let res = JSON.parse(Msg);
        let logs = res.ops;

        logs.forEach((log: { op: string; path: string; value: any }) => {
          if (log.op === "add") {
            if (
              log.value !== "</s>" && log.path.endsWith("/streamed_output/-") && log.path.length > "/streamed_output/-".length
            ) {
              messages += log.value;
              scrollToBottom(scrollToDiv)
            }
          }
        });
      } else {
        loading.set(false);
        scrollToBottom(scrollToDiv)
      }
    });
    eventSource.stream();
  };

  async function handleGenerateSummary(e) {
    if (e.detail.mode === "file") {
      await callTextStream(e.detail.value, "/file_summarize", "doc_id");
    } else if (e.detail.mode === "text") {
      await callTextStream(e.detail.value, "/text_summarize", "text");
    }
  }

  function handleClearMsg(e) {
    if (e.detail.status) {
      messages = "";
    }
  }
</script>

<div class="h-full">
  <Header />
  <p class="m-7 sm:mb-0 text-gray-500 font-semibold xl:m-8">Please upload file or paste content for summarization.</p>
  <div class="mt-2 m-6 grid grid-cols-3 gap-8 h-full">
    <div class="col-span-2 h-full">
      <Doc on:generateSummary={handleGenerateSummary} on:clearMsg={handleClearMsg}/>
    </div>
    <div class="col-span-1">
      <Summary chatMessage={messages} />
    </div>
  </div>
</div>
