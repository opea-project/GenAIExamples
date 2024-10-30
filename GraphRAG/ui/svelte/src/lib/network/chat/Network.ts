//  Copyright (C) 2024 Intel Corporation
//  SPDX-License-Identifier: Apache-2.0

import { env } from "$env/dynamic/public";
import { SSE } from "sse.js";

const CHAT_BASE_URL = env.CHAT_BASE_URL;

export async function fetchTextStream(query: string) {
	let payload = {};
	let url = "";

	payload = {
		model: "Intel/neural-chat-7b-v3-3",
		messages: query,
	};
	url = `${CHAT_BASE_URL}`;
	console.log("fetchTextStream", url);

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
