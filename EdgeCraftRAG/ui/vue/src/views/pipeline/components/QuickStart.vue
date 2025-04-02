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
      <div class="guide-title">Quick Start</div>
      <div class="steps-wrap">
        <a-steps
          :current="0"
          :items="steps"
          labelPlacement="vertical"
        ></a-steps>
      </div>
      <div class="card-wrap">
        <div class="item-wrap">
          <div class="left-wrap">1</div>
          <div class="right-wrap">
            <div class="title">Create Pipeline</div>
            <div class="des">
              Build your RAG pipeline with customized settings to maximize the
              potential of AI information processing capability.
            </div>
            <a-button
              class="special-button-primary"
              :icon="h(PlusOutlined)"
              @click="handleCreate"
              >Go Create</a-button
            >
          </div>
        </div>
        <div class="item-wrap">
          <div class="left-wrap">2</div>
          <div class="right-wrap">
            <div class="title">Use the Chatbot</div>
            <div class="des">
              Start engaging with the intelligent chatbot, which supports file
              uploads and information retrieval to assist you in completing
              tasks more efficiently.
            </div>
          </div>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup name="EditDialog">
import { userAppStore } from "@/store/user";
import { PlusOutlined } from "@ant-design/icons-vue";
import { computed, h } from "vue";

const userGuideStore = userAppStore();

const emit = defineEmits(["create"]);
const modelVisible = computed(() => {
  return !userGuideStore.userGuide;
});

const steps = ref<EmptyArrayType>([
  {
    title: "Step 1",
  },
  {
    title: "Step 2",
  },
]);
const handleCreate = () => {
  userGuideStore.setUserGuideState(true);
  emit("create");
};
const handleClose = () => {
  userGuideStore.setUserGuideState(true);
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
  .steps-wrap {
    width: 600px;
    margin: 0 auto;
    :deep(.intel-steps) {
      padding-top: 30px;
      .intel-steps-item-title {
        position: absolute;
        top: -35px;
        left: 35px;
        font-weight: 500;
      }
      .intel-steps-item-active {
        .intel-steps-item-title {
          color: var(--color-primary);
        }
      }
      .intel-steps-item-tail::after {
        height: 3px;
        background-color: var(--color-primary);
      }
    }
  }
  .card-wrap {
    display: flex;
    gap: 32px;
    margin-top: 24px;
    .item-wrap {
      flex: 1;
      padding: 20px;
      border-radius: 6px;
      height: 200px;
      box-shadow: var(--bg-gradient-shadow);
      display: flex;
      gap: 12px;
      .left-wrap {
        width: 30px;
        color: var(--border-main-color);
        font-size: 42px;
        line-height: 42px;
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
