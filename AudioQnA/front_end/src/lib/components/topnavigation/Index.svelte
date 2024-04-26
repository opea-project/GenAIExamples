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

<script>
	import UploadVoice from "../talkbot/upload-voice.svelte";
</script>

<header
	class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-[#0054ae]"
>
	<nav
		class="w-full divide-gray-200 border-gray-200 bg-[#0054ae] px-4 py-1.5 text-gray-500 dark:text-gray-400 sm:px-4"
	>
		<div class="mx-auto flex w-full flex-wrap items-center justify-between">
			<span
				class="ml-4 self-center whitespace-nowrap py-2 text-3xl font-semibold text-white"
				>AudioQnA</span
			>
			<UploadVoice />
		</div>
	</nav>
</header>
