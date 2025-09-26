<template>
  <div v-if="props.visible" class="loading-container">
    <div class="loading-wrap">
      <a-spin :size="size" />
      <p
        class="loading-title"
        :style="{ fontSize: size === 'default' ? '14px' : '18px' }"
      >
        {{ title ? title : t("common.loading") }}...
      </p>
      <p class="loading-text" v-if="showDes">
        {{ describe ? describe : t("common.waitTip") }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts" name="TunerLoading">
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
    default: false,
  },
  size: {
    type: String,
    default: "large",
  },
  title: {
    type: String,
    default: "",
  },
  describe: {
    type: String,
    default: "",
  },
  showDes: {
    type: Boolean,
    default: true,
  },
});
</script>

<style lang="less" scoped>
.loading-container {
  width: 100%;
  height: 100%;
  flex: 1;
  .vertical-center;
  .loading-wrap {
    text-align: center;
    padding: 24px;
    .loading-title {
      font-size: 18px;
      line-height: 28px;
      font-weight: 600;
      color: var(--font-main-color);
      margin: 8px auto;
    }
    .loading-text {
      line-height: 20px;
      color: var(--font-text-color);
    }
  }
}
</style>
