<template>
  <div class="chat-container">
    <a-layout>
      <a-layout-sider :width="80">
        <div class="sider-container">
          <div class="header-menu">
            <div class="log-wrap">
              <SvgIcon name="icon-chatbot1" :size="32" inherit />
              <div>{{ $t("chat.rag") }}</div>
            </div>
            <div
              v-for="menu in componentList"
              :key="menu.id"
              @click="handleMenuChange(menu.id)"
              :class="[
                'menu-wrap',
                currentMenu === menu.id ? 'menu-active' : '',
              ]"
            >
              <span class="active-icon">
                <SvgIcon :name="menu.icon" :size="22" inherit
              /></span>

              {{ $t(menu.label) }}
            </div>
          </div>
          <div class="footer-menu">
            <a-popover
              trigger="click"
              title="System status"
              placement="rightBottom"
            >
              <div
                class="menu-wrap menu-active menu-hover"
                @click="querySystemStatus"
              >
                <span class="active-icon">
                  <SvgIcon name="icon-system" :size="22" inherit
                /></span>
                {{ $t("system.title") }}
              </div>
              <template #content>
                <div class="chart-box">
                  <SystemChart :system-data="systemData" :chart-col="12" />
                </div>
              </template>
            </a-popover>

            <div class="menu-wrap menu-active menu-hover" @click="jumpPipeline">
              <span class="active-icon">
                <SvgIcon name="icon-setting" :size="22" inherit
              /></span>

              {{ $t("chat.setting") }}
            </div>
          </div>
        </div>
      </a-layout-sider>
      <a-layout-content>
        <div class="body-container">
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
                  :kb-id="selectedKB"
                  @back="handleBack"
                />
              </keep-alive>
            </a-layout-content>
          </a-layout>
        </div>
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script lang="ts" setup name="Chatbot">
import router from "@/router";
import { onMounted, reactive, computed } from "vue";
import { getSystemStatus } from "@/api/pipeline";
import {
  Chatbot,
  KnowledgeDetial,
  SystemChart,
  KnowledgeBase,
} from "./components";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const currentMenu = ref<string>("chat");
const currentPage = ref<string>("chat");
const selectedKB = ref<string>("");
let systemData = reactive<EmptyObjectType>({});

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
const handleMenuChange = (id: string) => {
  currentMenu.value = id;
  if (id === "chat") {
    currentPage.value = "chat";
  }
};
const querySystemStatus = async () => {
  const data = await getSystemStatus();
  Object.assign(systemData, data);
};
//Jump Pipeline
const jumpPipeline = () => {
  router.push("/pipeline");
};
const handleViewKBDetial = (idx: string) => {
  selectedKB.value = idx;
  if (selectedKB.value) currentPage.value = "knowledge";
  else currentPage.value = "chat";
};
const handleBack = () => {
  currentPage.value = "chat";
};
onMounted(() => {
  querySystemStatus();
});
</script>

<style scoped lang="less">
.chat-container {
  position: relative;
  height: 100%;
  background: linear-gradient(to right, #00377c, #1e5ca6, #4d84c8, #a3c3f2);

  .intel-layout.intel-layout-has-sider {
    height: 100%;
    background-color: transparent;
    .intel-layout-content {
      overflow: auto;
      // min-width: 900px;
    }
    .intel-layout-sider {
      background-color: transparent;
    }
  }
  .sider-container {
    width: 100%;
    height: 100%;

    .vertical-between;
    .log-wrap {
      padding: 12px 0;
      .flex-column;
      align-items: center;
      color: var(--color-white);
      gap: 4px;
      border-bottom: 1px solid var(--border-fuzzy-color);
    }
    .menu-wrap {
      color: var(--color-fuzzy-white);
      cursor: pointer;
      word-break: break-word;
      .flex-column;
      align-items: center;
      text-align: center;
      gap: 4px;
      margin-top: 20px;
      &:hover {
        color: var(--color-white);
      }
      .active-icon {
        border-radius: 50%;
        width: 36px;
        height: 36px;
        .vertical-center;
      }
      &.menu-active {
        color: var(--color-white);
        .active-icon {
          background-color: var(--border-fuzzy-color);
        }
      }
      &.menu-hover {
        .active-icon {
          background-color: transparent;
        }

        &:hover {
          .active-icon {
            transform: scale(1.2);
          }
        }
      }
    }
    .footer-menu {
      border-top: 1px solid var(--border-fuzzy-color);
      padding-bottom: 20px;
    }
  }

  .body-container {
    height: 100%;
    padding: 8px 8px 8px 0;
    // overflow-x: auto;
    overflow: hidden;
    display: flex;
    min-width: 0;
    .content-container {
      flex: 1;
      background-color: var(--bg-main-color);
      border-radius: 12px;
      width: 100%;
      height: 100%;
      min-width: 0;
      display: flex;
      .body-wrap {
        width: 100%;
        height: 100%;
        .vertical-center;
      }
    }
  }
}
.chart-box {
  width: 440px;
  padding: 10px;
  :deep(.chart-wrap) {
    width: 200px !important;
    height: 140px !important;
  }
}
</style>
