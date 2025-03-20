<template>
  <div>
    <a-collapse expandIconPosition="end" class="config-container mt-20">
      <a-collapse-panel :header="$t('setting.config')">
        <vue-json-pretty :data="jsonData" virtual v-if="jsonData" />
        <a-empty v-else />
      </a-collapse-panel>
    </a-collapse>
  </div>
</template>

<script lang="ts" setup name="xxx">
import VueJsonPretty from "vue-json-pretty";
import "vue-json-pretty/lib/styles.css";

const props = defineProps({
  jsonData: {
    type: String,
    default: "",
  },
});

const jsonData = ref(JSON.parse(props.jsonData));
</script>

<style scoped lang="less">
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
</style>
