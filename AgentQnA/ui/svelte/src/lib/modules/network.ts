// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { env } from "$env/dynamic/public";
import { SSE } from "sse.js";

const AGENT_URL = env.AGENT_URL;

export async function fetchAgentExecute(query: string) {
	let payload = {};
	let url = "";

	payload = {
		messages: query,
		stream: true,
	};

	url = AGENT_URL;

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
