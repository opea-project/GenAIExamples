<template>
  <div class="kb-detail-container">
    <div class="header-wrap">
      <div class="info-wrap">
        <div class="name-wrap">{{ kbInfo.name }}</div>
        <div class="des-wrap" v-if="kbInfo.description">
          {{ kbInfo.description }}
        </div>
      </div>
      <div class="button-wrap">
        <a-button
          type="primary"
          ghost
          :icon="h(RollbackOutlined)"
          @click="handleBack"
          >{{ $t("common.back") }}</a-button
        >
      </div>
    </div>
    <component :is="currentComponent" :key="componentKey" :kb-info="kbInfo" />
  </div>
</template>

<script setup lang="ts" name="DetailComponent">
import { h, provide } from "vue";
import { RollbackOutlined } from "@ant-design/icons-vue";
import eventBus from "@/utils/mitt";
import { KnowledgeDetail, ExperienceDetail } from "./index";

const props = defineProps({
  kbInfo: {
    type: Object,
    default: () => {},
    required: true,
  },
});

provide("kbInfo", props.kbInfo);
const emit = defineEmits(["back"]);

const currentComponent = computed(() => {
  return props.kbInfo.comp_type === "experience"
    ? ExperienceDetail
    : KnowledgeDetail;
});

const componentKey = computed(() => {
  return `detail-${props.kbInfo.idx}`;
});
const handleBack = () => {
  emit("back");
  eventBus.emit("reset");
};
</script>

<style lang="less" scoped>
.kb-detail-container {
  display: block !important;
  .flex-column;
  .header-wrap {
    padding: 12px 16px;
    height: 60px;
    border-bottom: 1px solid var(--border-main-color);
    .flex-between;
    gap: 16px;
    min-width: 0;
    .info-wrap {
      flex: 1;
      .flex-column;
      gap: 4px;
      min-width: 0;
      .name-wrap {
        font-size: 16px;
        font-weight: 600;
        flex: 1;
        min-width: 0;
        line-height: 16px;
        .single-ellipsis;
      }
      .des-wrap {
        color: var(--font-info-color);
        font-size: 12px;
        .single-ellipsis;
      }
    }
    .button-wrap {
      .vertical-center;
      gap: 4px;
    }
  }
}
</style>
