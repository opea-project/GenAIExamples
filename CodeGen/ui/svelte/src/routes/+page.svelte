<!--
  Copyright (c) 2024 Intel Corporation

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

<script lang="ts">
	export let data;
	import { fetchTextStream } from "$lib/network/chat/Network";
	import LoadingAnimation from "$lib/shared/components/loading/Loading.svelte";
	import "driver.js/dist/driver.css";
	import "$lib/assets/layout/css/driver.css";
	import PaperAirplane from "$lib/assets/chat/svelte/PaperAirplane.svelte";
	import Output from "$lib/modules/chat/Output.svelte";

	let query: string = "";
	let loading: boolean = false;
	let inFence = false;
	let tickRun = 0;
	let skipLangLine = false;
	let langBuf = "";
	let currentLang = "";

	type Segment = {
		id: number;
		type: "text" | "code";
		content: string;
		lang?: string;
	};
	let segments: Segment[] = [];
	let _sid = 0;

	const languageAliases: Record<string, string> = {
		javascript: "Javascript",
		js: "Javascript",
		jsx: "Javascript",
		typescript: "Typescript",
		ts: "Typescript",
		tsx: "Typescript",

		python: "Python",
		py: "Python",

		c: "C",
		"c++": "Cpp",
		cpp: "Cpp",
		cxx: "Cpp",
		csharp: "Csharp",
		"c#": "Csharp",

		go: "Go",
		golang: "Go",
		java: "Java",
		swift: "Swift",
		ruby: "Ruby",
		rust: "Rust",
		php: "Php",
		kotlin: "Kotlin",
		objectivec: "Objectivec",
		objc: "Objectivec",
		"objective-c": "Objectivec",
		perl: "Perl",
		matlab: "Matlab",
		r: "R",
		lua: "Lua",

		bash: "Bash",
		sh: "Bash",
		shell: "Bash",
		zsh: "Bash",

		sql: "Sql",
	};

	function canonicalLang(raw?: string | null): string | null {
		const s = (raw ?? "").toString().trim();
		if (!s) return null;
		const lower = s.toLowerCase();
		return languageAliases[lower] ?? s;
	}

	function appendText(s: string) {
		if (!s) return;
		const last = segments[segments.length - 1];
		if (!last || last.type !== "text") {
		segments = [...segments, { id: ++_sid, type: "text", content: "" }];
		}
		segments[segments.length - 1].content += s;
	}

	function appendCode(s: string) {
		if (!s) return;
		const last = segments[segments.length - 1];
		if (!last || last.type !== "code") {
		segments = [
			...segments,
			{
			id: ++_sid,
			type: "code",
			content: "",
			lang: currentLang || "python",
			},
		];
		}
		segments[segments.length - 1].content += s;
	}

	function settleTicks() {
		if (tickRun === 0) return;

		if (tickRun >= 3) {
		const toggles = Math.floor(tickRun / 3);
		for (let i = 0; i < toggles; i++) {
			inFence = !inFence;
			if (inFence) {
			skipLangLine = true;
			langBuf = "";
			currentLang = "";
			} else {
			skipLangLine = false;
			}
		}
		const leftovers = tickRun % 3;
		if (leftovers) (inFence ? appendCode : appendText)("`".repeat(leftovers));
		} else {
		(inFence ? appendCode : appendText)("`".repeat(tickRun));
		}
		tickRun = 0;
	}

	function consumeChunk(s: string) {
		for (let i = 0; i < s.length; i++) {
		const ch = s[i];

		if (ch === "`") {
			tickRun++;
			continue;
		}

		settleTicks();

		if (skipLangLine) {
			if (ch === "\n") {
			skipLangLine = false;
			const canon = canonicalLang(langBuf);
			currentLang = canon ?? (langBuf.trim() || "python");
			langBuf = "";
			} else {
			langBuf += ch;
			}
			continue;
		}

		if (inFence) appendCode(ch);
		else appendText(ch);
		}
	}

	const callTextStream = async (query: string) => {
		loading = true;

		segments = [];
		_sid = 0;
		inFence = false;
		tickRun = 0;
		skipLangLine = false;
		langBuf = "";
		currentLang = "";

		const eventSource = await fetchTextStream(query);

		eventSource.addEventListener("message", (e: any) => {
		const raw = String(e.data);
		const payloads = raw
			.split(/\r?\n/)
			.map((l) => l.replace(/^data:\s*/, "").trim())
			.filter((l) => l.length > 0);

		for (const part of payloads) {
			if (part === "[DONE]") {
			settleTicks();
			loading = false;
			return;
			}
			try {
			const json = JSON.parse(part);
			const msg =
				json.choices?.[0]?.delta?.content ?? json.choices?.[0]?.text ?? "";
			if (!msg || msg === "</s>") continue;
			consumeChunk(msg);
			} catch (err) {
			console.error("JSON chunk parse error:", err, part);
			}
		}
		});

		eventSource.addEventListener("error", () => {
			loading = false;
		});

		eventSource.stream();
	};

	const handleTextSubmit = async () => {
		if (!query) return;
		await callTextStream(query);
	};
</script>

<div class="flex grow flex-col text-white">
	<div class="relative h-full items-center gap-5 bg-fixed sm:flex">
		<div
		class="relative mx-auto flex h-full w-full flex-col items-center sm:mt-0 sm:w-[70%]"
		>
		<div
			class="fixed relative flex w-full flex-col items-center justify-between bg-white p-2 pb-0"
		>
			<div class="relative my-4 flex w-full flex-row justify-center">
			<div class="relative w-full focus:border-none">
					<input
					class="block w-full break-words border-0 border-b-2 border-gray-300 px-1 py-4 pl-4 pr-20 text-xs
					text-gray-900 focus:border-gray-300 focus:ring-0 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500 dark:focus:ring-blue-500"
					type="text"
					data-testid="code-input"
					placeholder="Enter prompt here"
					disabled={loading}
					maxlength="1200"
					bind:value={query}
					on:keydown={(event) => {
						if (event.key === "Enter" && !event.shiftKey && query) {
						event.preventDefault();
						handleTextSubmit();
						}
					}}
					/>
					<button
					on:click={() => {
						if (query) {
						handleTextSubmit();
						}
					}}
					type="submit"
					id="send"
					class="absolute bottom-2.5 end-2.5 px-4 py-2 text-sm font-medium text-white dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
					><PaperAirplane /></button>
				</div>
				</div>
			</div>
			<div class="mb-4 flex h-full w-full flex-col items-center">
				{#if segments.length}
				<div class="w-full items-center gap-4">
					<Output {segments} />
				</div>
				{/if}
				{#if loading}
					<LoadingAnimation />
				{/if}
			</div>
		</div>
	</div>
</div>
