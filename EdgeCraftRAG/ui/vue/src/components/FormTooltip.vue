<template>
  <a-tooltip placement="topRight" arrow-point-at-center>
    <template #title>
      {{ title }}
    </template>
    <InfoCircleOutlined
      :style="{ fontSize: size, color: 'var(--font-text-color)' }"
    />
  </a-tooltip>
</template>

<script setup lang="ts" name="FormTooltip">
import { InfoCircleOutlined } from "@ant-design/icons-vue";

const props = defineProps({
  title: {
    type: String,
  },
  size: {
    type: String,
    default: () => "16px",
  },
});
</script>

<style lang="less" scoped></style>
