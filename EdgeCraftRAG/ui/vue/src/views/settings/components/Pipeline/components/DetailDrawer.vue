<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="$t('pipeline.detail')"
    destroyOnClose
    width="500px"
    @close="handleClose"
  >
    <!-- basic -->
    <div class="basic-wrap">
      <p class="basic-item">
        <span class="label-wrap">{{ $t("pipeline.name") }}</span>
        <span class="content-wrap">{{ formData.name }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("pipeline.status") }}</span>
        <span :class="{ 'active-state': formData.active, 'content-wrap': true }">{{
          formData.active ? $t("pipeline.activated") : $t("pipeline.inactive")
        }}</span>
      </p>
    </div>
    <!-- Retriever -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="retrieverActive" expandIconPosition="end">
        <a-collapse-panel key="retriever" :header="$t('pipeline.config.retriever')">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.retrieverType") }}</span>
              <span class="content-wrap">{{ formData.retriever.retriever_type }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.topk") }}</span>
              <span class="content-wrap">{{ formData.retriever.retrieve_topk }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- PostProcessor -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="postProcessorActive" expandIconPosition="end">
        <a-collapse-panel key="postProcessor" :header="$t('pipeline.config.postProcessor')">
          <ul
            v-for="(item, index) in formData.postprocessor"
            key="index"
            :class="['form-wrap', index ? 'bt-border' : '']"
          >
            <li class="item-wrap">
              <span class="label-wrap"> {{ $t("pipeline.config.postProcessorType") }}</span>
              <span class="content-wrap">{{ item.processor_type }}</span>
            </li>
            <template v-if="item.processor_type === 'reranker'">
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.topn") }}</span>
                <span class="content-wrap">{{ item.top_n }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.rerank") }}</span>
                <span class="content-wrap">{{ item.reranker_model.model_id }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.rerankDevice") }}</span>
                <span class="content-wrap">{{ item.reranker_model.device }}</span>
              </li></template
            >
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Generator -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="generatorActive" expandIconPosition="end">
        <a-collapse-panel key="generator" :header="$t('pipeline.config.generator')">
          <ul
            v-for="(item, index) in formData.generator"
            key="index"
            :class="['form-wrap', index ? 'bt-border' : '']"
          >
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.generatorType") }}</span>
              <span class="content-wrap">
                {{ item.generator_type }}
              </span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.llm") }}</span>
              <span class="content-wrap">{{ item.inference_type }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.language") }}</span>
              <span class="content-wrap">{{ item.model.model_id }}</span>
            </li>
            <template v-if="item.inference_type === 'local'">
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.llmDevice") }}</span>
                <span class="content-wrap">{{ item.model.device }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.weights") }}</span>
                <span class="content-wrap">{{ item.model.weight }}</span>
              </li></template
            >
            <li class="item-wrap" v-else>
              <span class="label-wrap">{{ $t("pipeline.config.vllm_url") }}</span>
              <span class="content-wrap">{{ item.vllm_endpoint }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </a-drawer>
</template>
<script lang="ts" setup name="DetailDrawer">
  import { reactive, ref } from "vue";

  const props = defineProps({
    drawerData: {
      type: Object,
      required: true,
      default: () => {},
    },
  });
  const emit = defineEmits(["close"]);
  const formData = reactive<EmptyObjectType>(props.drawerData);
  const drawerVisible = ref<boolean>(true);
  const retrieverActive = ref<string>("retriever");
  const postProcessorActive = ref<string>("postProcessor");
  const generatorActive = ref<string>("generator");
  const handleClose = () => {
    emit("close");
  };
</script>
<style scoped lang="less">
  .basic-wrap {
    .basic-item {
      display: flex;
      gap: 12px;
      margin: 0;
      line-height: 24px;
      .content-wrap {
        color: var(--font-main-color);
        font-weight: 600;
      }
      .active-state {
        color: var(--color-success);
      }
    }
  }
  .module-wrap {
    margin-top: 20px;
    .intel-collapse {
      border-color: var(--border-main-color);
      :deep(.intel-collapse-header) {
        padding: 8px 16px;
      }
      :deep(.intel-collapse-header-text) {
        .fs-14;
        font-weight: 600;
        color: var(--font-main-color);
      }

      :deep(.intel-collapse-item) {
        border-bottom: 1px solid var(--border-main-color);
      }

      :deep(.intel-collapse-content) {
        border-top: 1px solid var(--border-main-color);
        .intel-collapse-content-box {
          padding: 10px 16px;
        }
      }
    }
    .form-wrap {
      padding: 0;
      margin: 0;
      .item-wrap {
        list-style: none;
        display: flex;
        gap: 12px;
        line-height: 1.2;
        padding: 6px 0;
        display: flex;
        color: var(--font-text-color);
        word-wrap: break-word;
        .content-wrap {
          color: var(--font-main-color);
          font-weight: 500;
          display: inline-flex;
          align-items: baseline;
          justify-content: end;
          flex: 1;
          word-break: break-word;
          overflow-wrap: break-word;
        }
      }
      &.bt-border {
        border-top: 1px dashed var(--border-main-color);
      }
    }
  }
  .label-wrap {
    position: relative;
    &::after {
      content: ":";
      .ml-2;
    }
  }
</style>
