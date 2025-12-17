<template>
  <div class="chat-container">
    <a-layout class="content-container">
      <a-layout-sider :width="expandMenu ? 260 : 60" class="sider-wrap">
        <div
          :class="{ 'fold-but': true, 'fold-up': !expandMenu }"
          @click="expandMenu = !expandMenu"
        >
          <DoubleLeftOutlined v-if="expandMenu" class="fold-icon" />
          <DoubleRightOutlined v-else />
        </div>
        <KnowledgeBase
          v-if="currentMenu == 'knowledge'"
          @view="handleViewKBDetail"
          :is-collapsed="!expandMenu"
        />
        <ChatHistory v-else :is-collapsed="!expandMenu" />
      </a-layout-sider>
      <a-layout-content>
        <keep-alive>
          <component
            :is="currentComponent"
            class="body-wrap"
            :kb-info="kbInfo"
            @back="handleBack"
          />
        </keep-alive>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script lang="ts" setup name="Chatbot">
  import { DoubleLeftOutlined, DoubleRightOutlined } from "@ant-design/icons-vue";
  import { computed } from "vue";
  import { Chatbot, ChatHistory, DetailComponent, KnowledgeBase } from "./components";

  const route = useRoute();

  const currentMenu = ref<string>("chat");
  const currentPage = ref<string>("chat");
  const expandMenu = ref<boolean>(true);
  let kbInfo = reactive<EmptyObjectType>({});

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
      component: markRaw(DetailComponent),
    },
  ]);

  const currentComponent = computed(() => {
    return componentList.value.find(item => item.id === currentPage.value)?.component;
  });

  const handleViewKBDetail = (row: EmptyObjectType) => {
    Object.assign(kbInfo, row);

    if (kbInfo.name) currentPage.value = "knowledge";
    else currentPage.value = "chat";
  };
  const handleBack = () => {
    currentPage.value = "chat";
  };

  watch(
    () => route,
    route => {
      if (route.query?.type === "kb") {
        currentMenu.value = "knowledge";
      } else {
        currentMenu.value = "chat";
        currentPage.value = "chat";
      }
    },
    { immediate: true, deep: true }
  );
  watch(
    () => currentMenu.value,
    value => {
      if (value) expandMenu.value = true;
    }
  );
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
  .sider-wrap {
    position: relative;
    &:hover {
      .fold-icon {
        display: block;
      }
    }
    .fold-but {
      position: absolute;
      top: 50%;
      right: -30px;
      cursor: pointer;
      z-index: 99;
      font-size: 20px;
      width: 40px;
      height: 50px;
      padding: 12px 0;
      text-align: end;
      color: var(--font-tip-color);
      &.fold-up {
        right: -20px;
      }
    }
    .fold-icon {
      display: none;
      font-weight: 600;
    }
  }
</style>
