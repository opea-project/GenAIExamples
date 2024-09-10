// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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
