<template>
  <a-layout-header class="chatbot-header">
    <div class="header-wrap">
      <div class="left-wrap">
        <img :height="36" :src="headerLog" />
        <div class="header-title">
          Intelligent AI assistant, quickly answer your questions
        </div>
      </div>
      <div class="right-wrap">
        <a-popover
          trigger="click"
          title="System status"
          placement="bottomRight"
        >
          <span @click="querySystemStatus" class="button-wrap">
            <SvgIcon
              name="icon-notice-board"
              :style="{ color: 'var(--color-primary)' }"
            />
            System status
          </span>
          <template #content>
            <div class="chart-box">
              <SystemChart :system-data="systemData" :chart-col="12" />
            </div>
          </template>
        </a-popover>
        <a-divider type="vertical" />
        <span @click="handleConfig" class="button-wrap">
          <SvgIcon
            name="icon-setting"
            :size="17"
            :style="{ color: 'var(--color-primary)' }"
          />
          Configure
        </span>
      </div>
    </div>
  </a-layout-header>
</template>

<script lang="ts" setup name="Chatbot">
import headerLog from "@/assets/svgs/header-log.svg";
import SvgIcon from "@/components/SvgIcon.vue";
import { SystemChart } from "@/views/pipeline/components";
import { getSystemStatus } from "@/api/pipeline";

const emit = defineEmits(["config"]);

let systemData = reactive<EmptyObjectType>({});

const querySystemStatus = async () => {
  const data = await getSystemStatus();
  Object.assign(systemData, data);
};
const handleConfig = () => {
  emit("config");
};
onMounted(() => {
  querySystemStatus();
});
</script>

<style scoped lang="less">
.chatbot-header {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 20;
  background-color: var(--bg-content-color);
  box-shadow: 0px 1px 2px 0px var(--bg-box-shadow);
  width: 100%;
}
.header-wrap {
  max-width: 1440px;
  min-width: 960px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  .left-wrap {
    display: flex;
    align-items: center;
    .header-title {
      margin-left: 24px;
      color: var(--font-text-color);
      font-size: 16px;
    }
  }

  .right-wrap {
    display: flex;
    justify-items: flex-end;
    align-items: center;
    gap: 8px;
    .button-wrap {
      display: flex;
      align-items: center;
      gap: 4px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      &:hover {
        color: var(--color-primary);
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
