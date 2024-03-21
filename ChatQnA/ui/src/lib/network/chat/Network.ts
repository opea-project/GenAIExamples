import { env } from "$env/dynamic/public";
import { SSE } from "sse.js";

const DOC_BASE_URL = env.DOC_BASE_URL;


export async function fetchTextStream(
	query: string,
	knowledge_base_id: string,
) {
	let payload = {};
	let url = "";

	payload = {
		query: query,
		knowledge_base_id: knowledge_base_id,
	};
	url = `${DOC_BASE_URL}/chat_stream`;

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
