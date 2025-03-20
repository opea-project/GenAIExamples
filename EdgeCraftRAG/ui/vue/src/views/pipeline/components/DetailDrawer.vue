<template>
  <a-drawer
    v-model:open="drawerVisible"
    title="Pipeline Details"
    destroyOnClose
    width="500px"
    @close="handleClose"
  >
    <!-- basic -->
    <div class="basic-wrap">
      <p class="basic-item">
        <span class="label-wrap">Name</span>
        <span class="content-wrap">{{ formData.name }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">Status</span>
        <span
          :class="{ 'active-state': formData.active, 'content-wrap': true }"
          >{{ formData.active ? "Activated" : "Inactive" }}</span
        >
      </p>
    </div>
    <!-- Node Parser -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="nodeParserActive" expandIconPosition="end">
        <a-collapse-panel key="nodeParser" header="Node Parser">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">Node parser type</span>
              <span class="content-wrap">{{
                formData.node_parser.parser_type
              }}</span>
            </li>
            <template v-if="!isHierarchical && !isSentencewindow">
              <li class="item-wrap">
                <span class="label-wrap">Chunk size</span>
                <span class="content-wrap">{{
                  formData.node_parser.chunk_size
                }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">Chunk overlap</span>
                <span class="content-wrap">{{
                  formData.node_parser.chunk_overlap
                }}</span>
              </li></template
            >
            <template v-if="isSentencewindow">
              <li class="item-wrap">
                <span class="label-wrap">Window Size</span>
                <span class="content-wrap">{{
                  formData.node_parser.window_size
                }}</span>
              </li></template
            >
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Indexer -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="indexerActive" expandIconPosition="end">
        <a-collapse-panel key="indexer" header="Indexer">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">Indexer Type</span>
              <span class="content-wrap">{{
                formData.indexer.indexer_type
              }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">Embedding Model</span>
              <span class="content-wrap">{{
                formData.indexer.embedding_model.model_id
              }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">Embedding run device</span>
              <span class="content-wrap">{{
                formData.indexer.embedding_model.device
              }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Retriever -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="retrieverActive" expandIconPosition="end">
        <a-collapse-panel key="retriever" header="Retriever">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">Retriever Type</span>
              <span class="content-wrap">{{
                formData.retriever.retriever_type
              }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">Search top k</span>
              <span class="content-wrap">{{
                formData.retriever.retrieve_topk
              }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- PostProcessor -->
    <div class="module-wrap">
      <a-collapse
        v-model:activeKey="postProcessorActive"
        expandIconPosition="end"
      >
        <a-collapse-panel key="postProcessor" header="PostProcessor">
          <ul
            v-for="(item, index) in formData.postprocessor"
            key="index"
            :class="['form-wrap', index ? 'bt-border' : '']"
          >
            <li class="item-wrap">
              {{ `PostProcessor Type${index + 1}:` }}
              <span class="content-wrap">{{ item.processor_type }}</span>
            </li>
            <li class="item-wrap" v-if="item.reranker_model?.model_id">
              <span class="label-wrap">Rerank Model</span>
              <span class="content-wrap">{{
                item.reranker_model.model_id
              }}</span>
            </li>
            <li class="item-wrap" v-if="item.reranker_model?.device">
              <span class="label-wrap">Rerank run device</span>
              <span class="content-wrap">{{ item.reranker_model.device }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Generator -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="generatorActive" expandIconPosition="end">
        <a-collapse-panel key="generator" header="Generator">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">Generator Type</span>
              <span class="content-wrap"> chatqna </span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">LLM Inference Type</span>
              <span class="content-wrap">{{
                formData.generator.inference_type
              }}</span>
            </li>
            <template v-if="formData.generator.inference_type === 'local'">
              <li class="item-wrap">
                <span class="label-wrap">Large Language Model</span>
                <span class="content-wrap">{{
                  formData.generator.model.model_id
                }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">LLM run device</span>
                <span class="content-wrap">{{
                  formData.generator.model.device
                }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">Weights</span>
                <span class="content-wrap">{{
                  formData.generator.model.weight
                }}</span>
              </li></template
            >
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </a-drawer>
</template>
<script lang="ts" setup name="DetailDrawer">
import { computed, reactive, ref } from "vue";

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
const nodeParserActive = ref<string>("nodeParser");
const indexerActive = ref<string>("indexer");
const retrieverActive = ref<string>("retriever");
const postProcessorActive = ref<string>("postProcessor");
const generatorActive = ref<string>("generator");

const isHierarchical = computed(() => {
  return formData.node_parser.parser_type === "hierarchical";
});
const isSentencewindow = computed(() => {
  return formData.node_parser.parser_type === "sentencewindow";
});
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
