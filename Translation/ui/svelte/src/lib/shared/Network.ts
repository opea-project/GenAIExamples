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

const BASE_URL = env.BASE_URL;

export async function fetchLanguageResponse(input: string, transform: string, transTo: string) {
  let payload = {};
  let url = "";

  payload = {
    language_from: transform,
    language_to: transTo,
    source_data: input,
    translate_type: "text",
  };
  url = `${BASE_URL}`;

  return new SSE(url, {
    headers: { "Content-Type": "application/json" },
    payload: JSON.stringify(payload),
  });
}
