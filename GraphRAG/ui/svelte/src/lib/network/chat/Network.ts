//  Copyright (C) 2024 Intel Corporation
//  SPDX-License-Identifier: Apache-2.0

import { env } from "$env/dynamic/public";
import { SSE } from "sse.js";

const CHAT_BASE_URL = env.CHAT_BASE_URL;
if (!env.LLM_MODEL_ID) {
	throw new Error("LLM_MODEL_ID environment variable must be set");
}
const LLM_MODEL_ID = env.LLM_MODEL_ID;

export async function fetchTextStream(query: string) {
	let payload = {};
	let url = "";

	payload = {
		model: LLM_MODEL_ID,
		messages: query,
	};
	url = `${CHAT_BASE_URL}`;
	console.log("fetchTextStream", url);

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
