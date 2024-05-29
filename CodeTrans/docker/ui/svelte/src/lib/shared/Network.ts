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
import { env } from "$env/dynamic/public";
import { SSE } from "sse.js";

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

export async function fetchLanguageResponse(input: string, transform: string, transTo: string) {
  const url = `${BASIC_URL}/v1/translation`;
  const transData = {
    language_from: transform,
    language_to: transTo,
    source_language: input,
  };

  const init: RequestInit = {
    method: "POST",
    body: JSON.stringify(transData),
  };

  return fetchPostRes(url, init);
}

export async function fetchTextStream(query: string, langFrom, langTo) {
  const payload = {
    language_from: langFrom,
    language_to: langTo,
    source_code: query,
  };

  let url = `${BASIC_URL}/v1/code_translation_stream`;

  return new SSE(url, {
    headers: { "Content-Type": "application/json" },
    payload: JSON.stringify(payload),
  });
}
