<template>
  <div class="chat-container">
    <a-layout class="content-container">
      <a-layout-sider :width="currentMenu === 'knowledge' ? 240 : 0">
        <KnowledgeBase
          @view="handleViewKBDetial"
          v-if="currentMenu === 'knowledge'"
        />
      </a-layout-sider>
      <a-layout-content>
        <keep-alive>
          <component
            :is="currentComponent"
            class="body-wrap"
            :kb-name="kbName"
            @back="handleBack"
          />
        </keep-alive>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script lang="ts" setup name="Chatbot">
import { onMounted, computed } from "vue";
import { Chatbot, KnowledgeDetial, KnowledgeBase } from "./components";

const route = useRoute();

const currentMenu = ref<string>("chat");
const currentPage = ref<string>("chat");
const kbName = ref<string>("");

const componentList = ref<EmptyArrayType>([
  {
    label: "chat.title",
    id: "chat",
    icon: "icon-chat",
    component: markRaw(Chatbot),
  },
  {
    label: "knowledge.title",
    id: "knowledge",
    icon: "icon-knowledge",
    component: markRaw(KnowledgeDetial),
  },
]);

const currentComponent = computed(() => {
  return componentList.value.find((item) => item.id === currentPage.value)
    ?.component;
});

const handleViewKBDetial = (name: string) => {
  kbName.value = name;
  if (kbName.value) currentPage.value = "knowledge";
  else currentPage.value = "chat";
};
const handleBack = () => {
  currentPage.value = "chat";
};
watch(
  () => route,
  (route) => {
    if (route.query?.type === "kb") {
      currentMenu.value = "knowledge";
    } else {
      currentMenu.value = "chat";
      currentPage.value = "chat";
    }
  },
  { immediate: true, deep: true }
);
onMounted(() => {});
</script>

<style scoped lang="less">
.chat-container {
  position: relative;
  height: 100%;
  min-width: 0;
  min-height: 0;
  .intel-layout.intel-layout-has-sider {
    height: 100%;
    background-color: transparent;
    .intel-layout-content {
      overflow: auto;
    }
    .intel-layout-sider {
      background-color: transparent;
    }
  }
}
</style>
