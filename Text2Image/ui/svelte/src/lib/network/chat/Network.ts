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

const BACKEND_BASE_URL = env.BACKEND_BASE_URL;
const guardrail_BASE_URL = env.GUARDRAIL_BASE_URL;


async function fetchFunc(url, init) {
	try {
		const response = await fetch(url, init);
		if (!response.ok) throw response.status;

		return await response.json();
	} catch (error) {
		console.error("network error: ", error);

		return undefined;
	}
}


export async function fetchGuardRail(query: string, stepValueStore: number, base64ImageStore: string) {	
	let payload = {};
	let url = "";

	payload = {
		prompt: query,
	};

	url = `${guardrail_BASE_URL}`;

	const init: RequestInit = {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	};

	return fetchFunc(url, init);
}

export async function fetchTextStream(query: string, stepValueStore: number, base64ImageStore: string) {
	let payload = {};
	let url = "";
	base64ImageStore = base64ImageStore.replace(/^data:[a-zA-Z]+\/[a-zA-Z]+;base64,/, "");

	payload = {
		image: base64ImageStore,
		prompt: query,
		max_new_tokens: stepValueStore,

	};

	url = `${BACKEND_BASE_URL}`;

	const init: RequestInit = {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	};

	return fetchFunc(url, init);
}
