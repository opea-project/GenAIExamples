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
	export let label = "";
	export let output = "";
	export let languages = "Python";
	export let isCode = false;

	let copyText = "copy";

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
	} as { [key: string]: any };

	function copyToClipboard(text) {
		const textArea = document.createElement("textarea");
		textArea.value = text;
		document.body.appendChild(textArea);
		textArea.select();
		document.execCommand("copy");
		document.body.removeChild(textArea);
	}

	function handelCopy() {
		copyToClipboard(output);
		copyText = "copied!";
		setTimeout(() => {
			copyText = "copy";
		}, 1000);
	}
</script>

<div class="flex w-full flex-col" data-testid="code-output">
	<span
		class=" mb-2 flex h-[3rem] w-full items-center justify-center bg-[#5856D6] px-8 py-2 text-center text-[0.89rem] uppercase leading-tight opacity-80"
		>{label}</span
	>

	<div
		class="flex justify-end border-2 border-none border-b-gray-800 bg-[#1C1C1C] px-3 text-white"
	>
		<button
			class="rounded border border-none py-1 text-[0.8rem] text-[#abb2bf]"
			on:click={() => {
				handelCopy();
			}}>{copyText}</button
		>
	</div>
	<div
		class="code-format-style hiddenScroll h-[22rem] divide-y overflow-auto bg-[#011627]"
	>
		{#if isCode}
			<Highlight language={python} code={output} let:highlighted>
				<LineNumbers {highlighted} wrapLines hideBorder />
			</Highlight>
		{:else}
			<div class="bg-[#282c34] text-[#abb2bf]">
				{@html marked(output)}
			</div>
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

	.code-format-style {
		resize: none;
		font-size: 16px;
		border: solid rgba(128, 0, 128, 0) 4px;
		box-shadow: 0 0 8px rgba(0, 0, 0, 0.19);
		transition: 0.1s linear;
	}
</style>
