import { env } from "$env/dynamic/public";
import { SSE } from "sse.js";

const PDF_BASE_URL = env.PDF_BASE_URL;


export async function fetchTextStream(
	query: string,
	knowledge_base_id: string,
	isCheckedStore: boolean
) {
	let payload = {};
	let url = "";

	payload = {
		query: query,
		knowledge_base_id: knowledge_base_id,
	};
	url = `${PDF_BASE_URL}/chat_stream`;

	return new SSE(url, {
		headers: { "Content-Type": "application/json" },
		payload: JSON.stringify(payload),
	});
}
