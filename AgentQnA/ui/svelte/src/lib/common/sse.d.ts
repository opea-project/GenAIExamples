// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

declare module "sse.js" {
	export type SSEOptions = EventSourceInit & {
		headers?: Record<string, string>;
		payload?: string;
		method?: string;
	};

	export class SSE extends EventSource {
		constructor(url: string | URL, sseOptions?: SSEOptions);
		stream(): void;
	}
}
