<script>
	import "tailwindcss/tailwind.css";
	import Layout from "$lib/components/layout.svelte";
	import Notifications from "svelte-notifications";
</script>

<Notifications>
	<Layout>
		<slot />
	</Layout>
</Notifications>
