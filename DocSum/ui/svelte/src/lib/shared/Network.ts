// Copyright (c) 2024 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { SSE } from "sse.js";
import { env } from "$env/dynamic/public";

const BASIC_URL = env.BASIC_URL;

async function fetchPostRes(url, init) {
  try {
    const response = await fetch(url, init);
    if (!response.ok) throw response.status;
    return await response.json();
  } catch (error) {
    console.error("network error: ", error);
    return undefined;
  }
}

export async function fetchKnowledgeBaseId(file: Blob, fileName: string) {
  const url = `${BASIC_URL}/doc_upload`;
  const formData = new FormData();
  formData.append("file", file, fileName);

  const init: RequestInit = {
    method: "POST",
    body: formData,
  };

  return fetchPostRes(url, init);
}

export async function fetchTextStream(query: string, urlSuffix: string, params: string) {
  let payload = {};
  if (params === "doc_id") {
    payload = { doc_id: query };
  } else if (params === "text") {
    payload = { text: query };
  }

  let url = `${BASIC_URL}${urlSuffix}`;
  console.log("url", url);

  return new SSE(url, {
    headers: { "Content-Type": "application/json" },
    payload: JSON.stringify(payload),
  });
}
