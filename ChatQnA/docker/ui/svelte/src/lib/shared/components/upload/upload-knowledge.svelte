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
	import { Fileupload, Label } from "flowbite-svelte";
	import { createEventDispatcher } from "svelte";

	const dispatch = createEventDispatcher();
	let value;
	let fileName = "未选择文件";

	function handleInput(event: Event) {
		const file = (event.target as HTMLInputElement).files![0];

		if (!file) return;

		const reader = new FileReader();
		reader.onloadend = () => {
			if (!reader.result) return;
			const src = reader.result.toString();
			dispatch("upload", { src: src, fileName: file.name });
		};
		reader.readAsDataURL(file);
	}

	const handleFileChange = (event) => {
		const fileInput = event.target;
		if (fileInput.files.length > 0) {
			fileName = fileInput.files[0].name;
		} else {
			fileName = "未选择文件";
		}
	};
</script>

<div>
	<Label class="mb-2 space-y-2">
		<div class="file-upload border-gray-300 h-full">
			<label
				for="file-upload"
				class="file-upload-label bg-gray-50 p-2.5 text-gray-900"
				data-testid="file-upload"
			>
				选择文件
			</label>
			<input
				id="file-upload"
				type="file"
				class="hidden-input"
				on:change={handleInput}
				data-testid="file-upload"
			/>
			<span class="file-upload-name pl-4">
				{fileName}
			</span>
		</div>

	</Label>
</div>

<style>
	.file-upload {
		border: 1px solid #d1d5db;
		padding: 5% 0;
		border-radius: 10px;
	}

	.file-upload-label {
		background: #1f2937;
		color: #fafafa;
		border-radius: 10px 0 0 10px;
		padding: 5% 9%;
	}
	.hidden-input {
		display: none;
	}
</style>
