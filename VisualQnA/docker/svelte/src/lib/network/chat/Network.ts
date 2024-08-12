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

export async function fetchTextStream(query: string, knowledge_base_id: string, isCheckedStore: boolean) {
	let payload = {};
	let url = "";

	payload = {
		messages: query,
		stream: "True",
	};
	url = `${BACKEND_BASE_URL}`;

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
