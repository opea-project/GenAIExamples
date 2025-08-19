<template>
  <i :class="['icon-intel', 'iconfont', getIconName]" :style="iconStyle" />
</template>

<script setup lang="ts" name="svgIcon">
import { computed } from "vue";

const props = defineProps({
  name: {
    type: String,
  },
  size: {
    type: Number,
    default: () => 20,
  },
  color: {
    type: String,
    default: () => "#808080",
  },
  inherit: {
    type: Boolean,
    default: () => false,
  },
});

const getIconName = computed(() => {
  return props.inherit ? ` inherit-style ${props?.name}` : ` ${props?.name}`;
});

const iconStyle = computed(() => {
  return {
    width: `${props.size}px`,
    height: `${props.size}px`,
    display: "inline-block",
    fontSize: `${props.size}px`,
    overflow: "hidden",
    color: props.inherit ? "inherit" : props.color,
  };
});
</script>

<style lang="less" scoped>
.icon-intel {
  display: inline-flex !important;
  align-items: center;
  &:hover {
    color: var(--color-primary) !important;
  }

  &.inherit-style {
    &:hover {
      color: inherit !important;
    }
  }
}
</style>
