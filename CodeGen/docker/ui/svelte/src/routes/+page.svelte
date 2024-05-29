<!--
  Copyright (C) 2024 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script lang="ts">
  import Header from "$lib/header.svelte";
  import InputAirPlane from "$lib/InputAirPlane.svelte";
  import Doc from "$lib/doc.svelte";
  import Summary from "$lib/summary.svelte";
  import { fetchTextStream } from "$lib/shared/Network.js";
  import { loading } from "$lib/shared/Store.js";
  import { onMount } from "svelte";
  import { scrollToBottom } from "$lib/shared/Utils.js";

  let messages = "";
  let scrollToDiv: HTMLDivElement;

  onMount(() => {
    scrollToDiv = document.querySelector("#editor")!;
    console.log("scrollToDiv", scrollToDiv);
  });

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
              log.path.endsWith("/streamed_output/-") &&
              typeof log.value === "string"
            ) {
              messages += log.value;
              scrollToBottom(scrollToDiv);
            }
          }
        });
      } else {
        loading.set(false);
        scrollToBottom(scrollToDiv);
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

  function handleSubmit() {

  }


</script>

<div class="h-full">
  <Header />
  <div class="w-[80%] mx-auto">
    <InputAirPlane on:handelSubmit={handleSubmit}/>
    <Summary chatMessage={messages} />
  </div>
  <pre><code>{@html `<span class="hljs"></span>`}</code></pre>
</div>
