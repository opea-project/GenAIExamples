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
	import Highlight, { LineNumbers } from "svelte-highlight";
	import typescript from "svelte-highlight/languages/typescript";
	import c from "svelte-highlight/languages/c";
	import cpp from "svelte-highlight/languages/cpp";
	import csharp from "svelte-highlight/languages/csharp";
	import go from "svelte-highlight/languages/go";
	import java from "svelte-highlight/languages/java";
	import python from "svelte-highlight/languages/python";
	import javascript from "svelte-highlight/languages/javascript";
	import swift from "svelte-highlight/languages/swift";
	import ruby from "svelte-highlight/languages/ruby";
	import rust from "svelte-highlight/languages/rust";
	import php from "svelte-highlight/languages/php";
	import kotlin from "svelte-highlight/languages/kotlin";
	import objectivec from "svelte-highlight/languages/objectivec";
	import perl from "svelte-highlight/languages/perl";
	import matlab from "svelte-highlight/languages/matlab";
	import r from "svelte-highlight/languages/r";
	import lua from "svelte-highlight/languages/lua";
	import bash from "svelte-highlight/languages/bash";
	import sql from "svelte-highlight/languages/sql";
	import { marked } from "marked";
	import { afterUpdate, onMount } from "svelte";

	export let output = "";
	export let lang = "Python";
	export let isCode = false;
	export let md_output = "";
	export let segments: Segment[] = [];

	let outputEl: HTMLDivElement;
	let copyText = "copy";
	let shouldAutoscroll = true;

	type Segment = {
		id: number;
		type: "text" | "code";
		content: string;
		lang?: string;
	};

	const languagesTag = {
		Typescript: typescript,
		Python: python,
		C: c,
		Cpp: cpp,
		Csharp: csharp,
		Go: go,
		Java: java,
		Javascript: javascript,
		Swift: swift,
		Ruby: ruby,
		Rust: rust,
		Php: php,
		Kotlin: kotlin,
		Objectivec: objectivec,
		Perl: perl,
		Matlab: matlab,
		R: r,
		Lua: lua,
		Bash: bash,
		Sql: sql,
	} as const;

	type LangKey = keyof typeof languagesTag;

	const aliasMap: Record<string, LangKey> = {
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

	$: normalizedLangKey = (() => {
		const raw = (lang ?? "").toString().trim();
		if (!raw) return null;
		const lower = raw.toLowerCase();

		if (lower in aliasMap) return aliasMap[lower];

		const hit = (Object.keys(languagesTag) as LangKey[]).find(
			(k) => k.toLowerCase() === lower
		);
		return hit ?? null;
	})();

	$: fullText = buildFullText();

	function atBottom(el: HTMLElement, threshold = 8) {
		return el.scrollHeight - el.scrollTop - el.clientHeight <= threshold;
	}

	function handleScroll() {
		if (!outputEl) return;
		shouldAutoscroll = atBottom(outputEl);
	}

	function scrollToBottom() {
		if (!outputEl) return;
		requestAnimationFrame(() =>
			requestAnimationFrame(() => {
				if (outputEl.scrollHeight) {
					outputEl.scrollTop = outputEl.scrollHeight;
				}
			})
		);
	}

	onMount(() => {
		scrollToBottom();
	});

	afterUpdate(() => {
		if (shouldAutoscroll) scrollToBottom();
	});
	async function copyAllFromDiv() {
		await navigator.clipboard.writeText(outputEl.innerText);
		copyText = "copied!";
		setTimeout(() => (copyText = "copy"), 1000);
	}

	function copyToClipboard(text: string) {
		if (navigator?.clipboard?.writeText) {
			navigator.clipboard.writeText(text);
		} else {
			const textArea = document.createElement("textarea");
			textArea.value = text;
			document.body.appendChild(textArea);
			textArea.select();
			document.execCommand("copy");
			document.body.removeChild(textArea);
		}
	}

	function normalizeToKey(raw?: string | null) {
		const s = (raw ?? "").trim().toLowerCase();
		if (!s) return null;
		if (s in aliasMap) return aliasMap[s as keyof typeof aliasMap];
		const hit = (
			Object.keys(languagesTag) as (keyof typeof languagesTag)[]
		).find((k) => k.toLowerCase() === s);
		return hit ?? null;
	}

	function buildFullText(): string {
		if (segments && segments.length > 0) {
			return segments
				.map((seg) => {
					if (seg.type === "code") {
						const key = normalizeToKey(seg.lang) ?? "text";
						return ["```" + key.toLowerCase(), seg.content, "```"].join("\n");
					}
					return seg.content;
				})
				.join("\n\n");
		}

		const parts: string[] = [];
		if (isCode && output) {
			const key = (normalizedLangKey ?? "text").toLowerCase();
			parts.push(["```" + key, output, "```"].join("\n"));
		}
		if (md_output) {
			parts.push(md_output);
		}
		return parts.join("\n\n");
	}
</script>

<div class="flex w-full flex-col" data-testid="code-output">
	<div
		class="flex justify-end border-2 border-none border-b-gray-800 bg-[#1C1C1C] px-3 text-white"
	>
		<button
			class="rounded border border-none py-1 text-[0.8rem] text-[#abb2bf]"
			on:click={copyAllFromDiv}>{copyText}</button
		>
	</div>

	<div
		class="
    hiddenScroll h-[22rem] overflow-auto
    bg-[#011627] p-5 text-[13px]
    leading-5
  "
		bind:this={outputEl}
		on:scroll={handleScroll}
	>
		{#if segments && segments.length > 0}
			{#each segments as seg (seg.id)}
				{#if seg.type === "code"}
					<div class="relative border-t border-[#0c2233]">
						<Highlight
							language={languagesTag[normalizeToKey(seg.lang) ?? "Python"]}
							code={seg.content}
							let:highlighted
						>
							<LineNumbers {highlighted} wrapLines hideBorder />
						</Highlight>
					</div>
				{:else}
					<div>{@html marked(seg.content)}</div>
				{/if}
			{/each}
		{:else}
			{#if isCode && output}
				<Highlight language={python} code={output} let:highlighted>
					<LineNumbers {highlighted} wrapLines hideBorder />
				</Highlight>
			{/if}
			{#if md_output}
				<div class="bg-[#282c34] py-2 text-[#abb2bf]">
					{@html marked(md_output)}
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.hiddenScroll::-webkit-scrollbar {
		display: none;
	}
	.hiddenScroll {
		-ms-overflow-style: none; /* IE and Edge */
		scrollbar-width: none; /* Firefox */
	}
</style>
