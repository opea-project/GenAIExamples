<template>
  <a-modal
    v-model:open="modelVisible"
    width="800px"
    centered
    destroyOnClose
    :keyboard="false"
    :maskClosable="false"
    :footer="null"
    :aria-hidden="false"
    @cancel="handleClose"
    class="import-dialog"
  >
    <div class="guide-wrap">
      <div class="guide-title">{{ $t("knowledge.selectTitle") }}</div>
      <div class="guide-text">{{ $t("knowledge.selectDes") }}</div>
      <div class="card-wrap">
        <div class="item-wrap">
          <div class="left-wrap">
            <SvgIcon name="icon-knowledge" inherit :size="32" />
          </div>
          <div class="right-wrap">
            <div class="title">{{ $t("knowledge.title") }}</div>
            <div class="des">
              {{ $t("knowledge.kbDes") }}
            </div>
            <a-button
              class="special-button-primary"
              :icon="h(PlusOutlined)"
              @click="handleCreate"
              >{{ $t("quickStart.create") }}</a-button
            >
          </div>
        </div>
        <div class="item-wrap">
          <div class="left-wrap">
            <SvgIcon name="icon-experience" inherit :size="32" />
          </div>
          <div class="right-wrap">
            <div class="title">{{ $t("knowledge.experience") }}</div>
            <div class="des">
              {{ $t("knowledge.experienceDes") }}
            </div>
            <a-button
              :class="{
                'special-button-primary': true,
                'is-disabled': created,
              }"
              :icon="h(PlusOutlined)"
              :disabled="created"
              @click="handleCreateExperience"
              >{{ $t("quickStart.create") }}</a-button
            >
          </div>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup name="SelectTypeDialog">
import { PlusOutlined } from "@ant-design/icons-vue";
import { h } from "vue";

const props = defineProps({
  created: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["createKB", "close"]);
const modelVisible = ref<boolean>(true);
const handleCreate = () => {
  emit("createKB", "knowledge");
  handleClose();
};
const handleCreateExperience = async () => {
  emit("createKB", "experience");
  handleClose();
};
const handleClose = () => {
  emit("close");
};
</script>

<style scoped lang="less">
.guide-wrap {
  padding: 24px 0;
  .guide-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--font-main-color);
    text-align: center;
  }
  .guide-text {
    text-align: center;
    color: var(--font-tip-color);
  }
  .card-wrap {
    display: flex;
    gap: 32px;
    margin-top: 24px;
    .item-wrap {
      flex: 1;
      padding: 20px;
      border-radius: 6px;
      box-shadow: var(--bg-gradient-shadow);
      display: flex;
      gap: 12px;
      .left-wrap {
        .pt-6;
        color: var(--color-second-primaryBg);
      }
      .right-wrap {
        flex: 1;
        .title {
          font-size: 18px;
          font-weight: 500;
          line-height: 28px;
          color: var(--font-main-color);
          white-space: pre-wrap;
        }
        .des {
          margin-top: 12px;
          margin-bottom: 20px;
          line-height: 20px;
          color: var(--font-text-color);
        }
      }
    }
  }
}
</style>
