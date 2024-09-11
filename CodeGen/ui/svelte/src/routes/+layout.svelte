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
	import "tailwindcss/tailwind.css";
	import "../app.postcss";
	import Notifications from "svelte-notifications";
	import Header from "$lib/modules/frame/header.svelte";
  import atomOneDark from "svelte-highlight/styles/atom-one-dark";
</script>

<svelte:head>
	{@html atomOneDark}
</svelte:head>

<Notifications>
		<Header />
		<slot />
</Notifications>
