<template>
  <a-layout class="layout-container">
    <a-layout-header class="layout-header">
      <Header />
    </a-layout-header>
    <a-layout-content :class="{ 'layout-main': true, 'full-screen': isFull }">
      <router-view class="layout-view" />
    </a-layout-content>
  </a-layout>
</template>
<script lang="ts" setup name="Main">
import { watch, onMounted } from "vue";
import Header from "./Header.vue";
const route = useRoute();
const isFull = ref<boolean>(false);

const handleRouteChange = () => {
  const { name } = route;
  if (name === "Chatbot") isFull.value = true;
  else isFull.value = false;
};

watch(
  () => route.path,
  () => {
    handleRouteChange();
  }
);

onMounted(() => {
  handleRouteChange();
});
</script>
<style lang="less">
.full-screen {
  padding: 0 !important;
  overflow: hidden !important;
  .layout-view {
    width: 100% !important;
    min-width: 960px !important;
    max-width: none !important;
  }
}
</style>
