<template>
  <a-config-provider
    :locale="getGlobalI18n"
    :theme="currentTheme"
    prefixCls="intel"
    autoInsertSpaceInButton
  >
    <router-view />
  </a-config-provider>
</template>
<script setup lang="ts">
import { themeAppStore } from "@/store/theme";
import { antTheme } from "@/utils/antTheme";
import { computed } from "vue";
import { useI18n } from "vue-i18n";

const themeStore = themeAppStore();

const currentTheme = computed(() => {
  return antTheme[themeStore.theme as keyof typeof antTheme];
});

const { messages, locale } = useI18n();
const getGlobalI18n = computed(() => {
  return messages.value[locale.value];
});
</script>
<style scoped lang="less"></style>
