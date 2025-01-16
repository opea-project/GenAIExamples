<!--
  Copyright (C) 2025 Intel Corporation
  SPDX-License-Identifier: Apache-2.0
-->

<script>
	import { open } from './store';
</script>

<!-- The overlay will only be visible on small screens to emphasize the focus on the side navigation when it is open.-->
<div
	class={$open
		? 'bg-[#161730] fixed h-screen left-0 opacity-40 top-0 w-screen z-30 lg:bg-transparent'
		: ''}
/>
