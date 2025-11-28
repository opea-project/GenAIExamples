<template>
  <div class="illustration-wrap">
    <a-row type="flex" wrap :gutter="[20, 20]">
      <a-col :span="chartCol">
        <v-chart
          class="chart-wrap"
          :option="cpuOption"
          :theme="currentTheme"
          autoresize
        />
      </a-col>
      <a-col :span="chartCol" v-if="systemData.gpuUsage">
        <v-chart
          class="chart-wrap"
          :option="gpuOption"
          :theme="currentTheme"
          autoresize
        />
      </a-col>
      <a-col :span="chartCol">
        <v-chart
          class="chart-wrap"
          :option="diskOption"
          :theme="currentTheme"
          autoresize
        />
      </a-col>
      <a-col :span="chartCol">
        <v-chart
          class="chart-wrap"
          :option="memoryOption"
          :theme="currentTheme"
          autoresize
        />
      </a-col>
    </a-row>
  </div>
</template>

<script lang="ts" setup name="SystemChart">
import { themeAppStore } from "@/store/theme";
import { PieChart } from "echarts/charts";
import {
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { computed } from "vue";
import VChart from "vue-echarts";
import { useI18n } from "vue-i18n";
import { formatDecimals } from "@/utils/common";

const { t } = useI18n();
const themeStore = themeAppStore();

// Required components
echarts.use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
]);

const props = defineProps({
  systemData: {
    type: Object,
    required: true,
    default: () => {},
  },
  chartCol: {
    type: Number,
    default: 8,
  },
});

const currentTheme = computed(() => {
  return themeStore.theme;
});
const currentThemeBg = computed(() => {
  return themeStore.theme === "dark" ? "#2d2d2d" : "";
});
const memoryInfo = computed(() => {
  return `${formatDecimals(props.systemData.memoryUsed)}GB/${formatDecimals(
    props.systemData.memoryTotal
  )}GB`;
});

const cpuOption = computed(() => ({
  color: ["#5470c6", "#D8D8D8"],
  backgroundColor: currentThemeBg.value,
  title: {
    text: t("system.cpu"),
    left: "16",
    top: "16",
    textStyle: {
      fontSize: 14,
      fontWeight: "500",
    },
  },
  tooltip: { trigger: "item", formatter: "{b}: {c}%" },
  series: [
    {
      name: t("system.cpu"),
      type: "pie",
      radius: ["65%", "80%"],
      center: ["50%", "75%"],
      itemStyle: {
        borderRadius: 15,
      },
      label: {
        show: false,
        position: "center",
        fontSize: 12,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: "12",
          fontWeight: "bold",
        },
      },
      startAngle: 180,
      endAngle: 360,
      data: [
        {
          value: props.systemData.cpuUsage,
          name: t("system.used"),
          label: { show: true, formatter: "{b}: {d}%" },
        },
        {
          value: 100 - props.systemData.cpuUsage,
          name: t("system.notUsed"),
          label: { show: false },
        },
      ],
    },
  ],
}));
const gpuOption = computed(() => ({
  color: ["#91cc75", "#D8D8D8"],
  backgroundColor: currentThemeBg.value,
  title: {
    text: t("system.gpu"),
    left: "16",
    top: "16",
    textStyle: {
      fontSize: 14,
      fontWeight: "500",
    },
  },
  tooltip: { trigger: "item", formatter: "{b}: {c}%" },
  series: [
    {
      name: t("system.gpu"),
      type: "pie",
      radius: ["65%", "80%"],
      center: ["50%", "75%"],
      itemStyle: {
        borderRadius: 15,
      },
      label: {
        show: false,
        position: "center",
        fontSize: 12,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: "14",
          fontWeight: "bold",
        },
      },
      startAngle: 180,
      endAngle: 360,
      data: [
        {
          value: props.systemData.gpuUsage,
          name: t("system.used"),
          label: { show: true, formatter: "{b}: {d}%" },
        },
        {
          value: 100 - props.systemData.gpuUsage,
          name: t("system.notUsed"),
          label: { show: false },
        },
      ],
    },
  ],
}));
const diskOption = computed(() => ({
  color: ["#fac858", "#D8D8D8"],
  backgroundColor: currentThemeBg.value,
  title: {
    text: t("system.disk"),
    left: "16",
    top: "16",
    textStyle: {
      fontSize: 14,
      fontWeight: "500",
    },
  },
  tooltip: { trigger: "item", formatter: "{b}: {c}%" },
  series: [
    {
      name: t("system.disk"),
      type: "pie",
      radius: ["65%", "80%"],
      center: ["50%", "75%"],
      itemStyle: {
        borderRadius: 15,
      },
      label: {
        show: false,
        position: "center",
        fontSize: 12,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: "14",
          fontWeight: "bold",
        },
      },
      startAngle: 180,
      endAngle: 360,
      data: [
        {
          value: props.systemData.diskUsage,
          name: t("system.used"),
          label: { show: true, formatter: "{b}: {d}%" },
        },
        {
          value: 100 - props.systemData.diskUsage,
          name: t("system.notUsed"),
          label: { show: false },
        },
      ],
    },
  ],
}));
const memoryOption = computed(() => ({
  color: ["#66C7FD", "#D8D8D8"],
  backgroundColor: currentThemeBg.value,
  title: [
    {
      text: t("system.memory"),
      left: "16",
      top: "16",
      textStyle: {
        fontSize: 14,
        fontWeight: "500",
      },
    },
    {
      subtext: memoryInfo.value,
      left: "20",
      bottom: "10",
      textAlign: "left",
      verticalAlign: "bottom",
    },
  ],
  tooltip: { trigger: "item", formatter: "{b}: {c}%" },
  series: [
    {
      name: t("system.memory"),
      type: "pie",
      radius: ["65%", "80%"],
      center: ["50%", "75%"],
      itemStyle: {
        borderRadius: 15,
      },
      label: {
        show: false,
        position: "center",
        fontSize: 12,
      },
      emphasis: {
        label: {
          show: true,
          fontSize: "14",
          fontWeight: "bold",
        },
      },
      startAngle: 180,
      endAngle: 360,
      data: [
        {
          value: props.systemData.memoryUsage,
          name: t("system.used"),
          label: { show: true, formatter: "{b}: {d}%" },
        },
        {
          value: 100 - props.systemData.memoryUsage,
          name: t("system.notUsed"),
          label: { show: false },
        },
      ],
    },
  ],
}));
</script>

<style scoped lang="less">
.illustration-wrap {
  flex: 1;
}
.chart-wrap {
  width: 100%;
  height: 172px;
  border-radius: 8px;
  background-color: var(--bg-card-color);
  overflow: hidden;
}
</style>
