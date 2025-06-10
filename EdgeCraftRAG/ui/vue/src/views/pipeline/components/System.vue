<template>
  <div class="system-container">
    <a-collapse v-model:activeKey="activeKey" expandIconPosition="end">
      <a-collapse-panel key="status" :header="$t('system.title')">
        <SystemChart :system-data="systemData" :chart-col="chartCol" />
        <div class="info-wrap">
          <a-descriptions
            :title="$t('system.info')"
            :column="1"
            :label-style="{ color: 'var(--font-text-color)' }"
            :content-style="{
              color: 'var(--font-main-color)',
              justifyContent: 'end',
            }"
          >
            <a-descriptions-item :label="$t('system.kernel')">{{
              systemData.kernel
            }}</a-descriptions-item>
            <a-descriptions-item :label="$t('system.processor')">{{
              systemData.processor
            }}</a-descriptions-item>
            <a-descriptions-item :label="$t('system.os')">{{
              systemData.os
            }}</a-descriptions-item>
            <a-descriptions-item :label="$t('system.time')">{{
              systemData.currentTime
            }}</a-descriptions-item>
          </a-descriptions>
        </div>
      </a-collapse-panel>
    </a-collapse>
  </div>
</template>

<script lang="ts" setup name="System">
import { getSystemStatus } from "@/api/pipeline";
import { onMounted, onUnmounted, ref } from "vue";
import { SystemChart } from "./index";
import { SystemType } from "../type";

const activeKey = ref<string>("status");
const intervalId = ref<any>(null);
let systemData = reactive<SystemType>({
  cpuUsage: 0,
  gpuUsage: 0,
  diskUsage: 0,
  memoryUsage: 0,
  memoryUsed: "",
  memoryTotal: "",
  kernel: "",
  processor: "",
  os: "",
  currentTime: "",
});

const chartCol = computed(() => {
  return systemData.gpuUsage ? 6 : 8;
});
const querySystemStatus = async () => {
  const data = await getSystemStatus();
  Object.assign(systemData, data);
};

onMounted(() => {
  querySystemStatus();
  intervalId.value = setInterval(querySystemStatus, 50000);
});
onUnmounted(() => {
  clearInterval(intervalId.value);
});
</script>

<style scoped lang="less">
.system-container {
  .title {
    .fs-16;
    font-weight: 600;
    color: var(--font-main-color);
  }

  .intel-collapse {
    background-color: var(--bg-content-color);
    border-color: transparent;
    border: 1px solid transparent;

    :deep(.intel-collapse-header-text) {
      .title;
    }

    :deep(.intel-collapse-item) {
      border-bottom: transparent;
    }

    :deep(.intel-collapse-content) {
      border-top: transparent;

      .intel-collapse-content-box {
        padding-top: 0;
      }
    }
  }
  .info-wrap {
    border-radius: 8px;
    background-color: var(--bg-card-color);
    padding: 16px 16px 0 16px;
    margin-top: 20px;
    width: 500px;
    :deep(.intel-descriptions) {
      .intel-descriptions-header {
        margin-bottom: 12px;
      }
      .intel-descriptions-item {
        padding-bottom: 8px;
      }
    }
  }
}
</style>
