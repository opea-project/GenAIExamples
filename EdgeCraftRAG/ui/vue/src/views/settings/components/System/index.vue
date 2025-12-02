<template>
  <div class="system-container">
    <a-collapse v-model:activeKey="activeKey" expandIconPosition="end">
      <a-collapse-panel key="status" :header="$t('system.title')">
        <div class="chart-container">
          <SystemChart :system-data="systemData" :chart-col="chartCol" />
          <div class="info-wrap">
            <a-descriptions
              :title="$t('system.info')"
              :column="1"
              :label-style="{ color: 'var(--font-info-color)' }"
              :content-style="{
                color: 'var(--font-text-color)',
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
        </div>
      </a-collapse-panel>
    </a-collapse>
  </div>
</template>

<script lang="ts" setup name="System">
import { getSystemStatus } from "@/api/pipeline";
import { onMounted, onUnmounted, ref } from "vue";
import SystemChart from "./SystemChart.vue";
import { SystemType } from "./type";

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
  setTimeout(() => querySystemStatus(), 10);

  intervalId.value = setInterval(querySystemStatus, 60000);
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
  .chart-container {
    .flex-left;
    gap: 20px;
  }
  .info-wrap {
    border-radius: 8px;
    background-color: var(--bg-card-color);
    padding: 8px 16px 0 16px;
    width: 400px;
    :deep(.intel-descriptions) {
      .intel-descriptions-header {
        margin-bottom: 12px;
      }
      .intel-descriptions-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .intel-descriptions-item {
        padding-bottom: 8px;
        flex: 1 1 auto;
        min-width: 250px;
      }
    }
  }
}
</style>
