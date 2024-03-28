<script>

  import IntelLogo from "$lib/assets/header/intelLogo.svelte";

</script>
<header
  class="sticky top-0 z-40 flex-none w-full mx-auto bg-[#0054ae] border-b border-gray-200 dark:border-gray-600 dark:bg-gray-800"
>
  <nav
    class="bg-[#0054ae] dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700 divide-gray-200 dark:divide-gray-700 px-2 sm:px-4 w-full py-1.5"
  >
    <div class="mx-auto flex flex-wrap justify-between items-center w-full">
        <IntelLogo />
      <span
        class="self-center whitespace-nowrap text-2xl font-semibold text-white ml-4"
        data-svelte-h="svelte-1hbktnk">Web Search Chatbot</span
      >
    </div>
  </nav>
</header>
