<template>
  <div class="main-container">
    <a-layout>
      <a-layout-sider :width="80">
        <div class="sider-container">
          <div class="header-menu">
            <div
              v-for="menu in componentList"
              :key="menu.path"
              @click="handleMenuChange(menu.path)"
              :class="[
                'menu-wrap',
                currentMenu === menu.path ? 'menu-active' : '',
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
              :title="$t('system.title')"
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
          </div>
        </div>
      </a-layout-sider>
      <a-layout-content class="body-container">
        <div class="content-container">
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>
    <!-- QuickStart -->
    <QuickStart @create="handleCreate" />
  </div>
</template>

<script lang="ts" setup name="Chatbot">
import router from "@/router";
import { onMounted, reactive } from "vue";
import { QuickStart, SystemChart } from "../pipeline/components/index";
import { getSystemStatus } from "@/api/pipeline";

const route = useRoute();

const currentMenu = ref<string>(route.fullPath);
let systemData = reactive<EmptyObjectType>({});
const componentList = ref<EmptyArrayType>([
  {
    label: "chat.title",
    path: "/chatbot",
    icon: "icon-chat",
  },
  {
    label: "knowledge.title",
    path: "/chatbot?type=kb",
    icon: "icon-knowledge",
  },
  {
    label: "chat.setting",
    path: "/pipeline",
    icon: "icon-setting",
  },
]);

const handleMenuChange = (path: string) => {
  currentMenu.value = path;
  router.push(path);
};
//create
const handleCreate = () => {
  router.push({ name: "Pipeline" });
};
const querySystemStatus = async () => {
  const data = await getSystemStatus();
  Object.assign(systemData, data);
};
watch(
  () => route.fullPath,
  (value) => {
    currentMenu.value = value;
  }
);
onMounted(() => {
  querySystemStatus();
});
</script>

<style scoped lang="less">
.main-container {
  position: relative;
  height: 100%;
  background: var(--bg-blue-color);
  overflow: hidden;
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
    overflow: hidden;
    display: flex;
    min-width: 0;
    .content-container {
      overflow-y: auto;
      flex: 1;
      background-color: var(--bg-main-color);
      border-radius: 12px;
      width: 100%;
      min-width: 960px;
      height: 100%;
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
