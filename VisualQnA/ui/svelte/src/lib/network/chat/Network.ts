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

const BACKEND_BASE_URL = env.BACKEND_BASE_URL;

export async function fetchTextStream(query: string, stepValueStore: number, base64ImageStore: string) {
	let payload = {};
	let url = "";
	base64ImageStore = base64ImageStore.replace(/^data:[a-zA-Z]+\/[a-zA-Z]+;base64,/, "");

	payload = {
		messages: [
			{
				role: "user",
				content: [
					{
						type: "text",
						text: query,
					},
					{
						type: "image_url",
						image_url: { url: base64ImageStore },
					},
				],
			},
		],
		max_new_tokens: stepValueStore,
		stream: true,
	};
	console.log("payload", payload);

	url = `${BACKEND_BASE_URL}`;

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
