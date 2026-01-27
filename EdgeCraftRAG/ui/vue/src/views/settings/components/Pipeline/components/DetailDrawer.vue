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
    <!-- Node Parser -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="nodeParserActive" expandIconPosition="end">
        <a-collapse-panel key="nodeParser" :header="$t('pipeline.config.nodeParser')">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.nodeParser") }}</span>
              <span class="content-wrap">{{ formData.node_parser.parser_type }}</span>
            </li>
            <template v-if="!isHierarchical && !isSentencewindow">
              <li class="item-wrap">
                <span class="label-wrap"> {{ $t("pipeline.config.chunkSize") }}</span>
                <span class="content-wrap">{{ formData.node_parser.chunk_size }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.chunkOverlap") }}</span>
                <span class="content-wrap">{{ formData.node_parser.chunk_overlap }}</span>
              </li></template
            >
            <template v-if="isSentencewindow">
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.windowSize") }}</span>
                <span class="content-wrap">{{ formData.node_parser.window_size }}</span>
              </li></template
            >
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
    <!-- Indexer -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="indexerActive" expandIconPosition="end">
        <a-collapse-panel key="indexer" :header="$t('pipeline.config.indexer')">
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.indexerType") }}</span>
              <span class="content-wrap">{{ formData.indexer.indexer_type }}</span>
            </li>
            <li class="item-wrap" v-if="formData.indexer.indexer_type !== 'kbadmin_indexer'">
              <span class="label-wrap">{{ $t("pipeline.config.llm") }}</span>
              <span class="content-wrap">{{ formData.indexer.inference_type }}</span>
            </li>
            <li
              class="item-wrap"
              v-if="
                formData.indexer.indexer_type === 'kbadmin_indexer' ||
                formData.indexer.inference_type === 'vllm'
              "
            >
              <span class="label-wrap">{{ $t("pipeline.config.embeddingUrl") }}</span>
              <span
                class="content-wrap"
                v-if="formData.indexer.indexer_type === 'kbadmin_indexer'"
                >{{ formData.indexer?.embedding_url }}</span
              >
              <span class="content-wrap" v-if="formData.indexer.inference_type === 'vllm'">{{
                formData.indexer.embedding_model.api_base
              }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.embedding") }}</span>
              <span class="content-wrap">{{ formData.indexer.embedding_model.model_id }}</span>
            </li>
            <li class="item-wrap" v-if="formData.indexer.inference_type === 'local'">
              <span class="label-wrap">{{ $t("pipeline.config.embeddingDevice") }}</span>
              <span class="content-wrap">{{ formData.indexer.embedding_model.device }}</span>
            </li>
            <li
              class="item-wrap"
              v-if="['kbadmin_indexer', 'milvus_vector'].includes(formData.indexer.indexer_type)"
            >
              <span class="label-wrap">{{ $t("pipeline.config.vector_url") }}</span>
              <span class="content-wrap">{{ formData.indexer?.vector_url }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
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
              <span class="label-wrap">
                {{ $t("pipeline.config.postProcessorType") }}
                <template v-if="formData.postprocessor?.length > 1">
                  {{ index + 1 }}
                </template></span
              >
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
          <ul class="form-wrap">
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.generatorType") }}</span>
              <span class="content-wrap">
                {{ formData.generator.generator_type }}
              </span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.llm") }}</span>
              <span class="content-wrap">{{ formData.generator.inference_type }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.language") }}</span>
              <span class="content-wrap">{{ formData.generator.model.model_id }}</span>
            </li>
            <template v-if="formData.generator.inference_type === 'local'">
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.llmDevice") }}</span>
                <span class="content-wrap">{{ formData.generator.model.device }}</span>
              </li>
              <li class="item-wrap">
                <span class="label-wrap">{{ $t("pipeline.config.weights") }}</span>
                <span class="content-wrap">{{ formData.generator.model.weight }}</span>
              </li></template
            >
            <li class="item-wrap" v-else>
              <span class="label-wrap">{{ $t("pipeline.config.vllm_url") }}</span>
              <span class="content-wrap">{{ formData.generator.vllm_endpoint }}</span>
            </li>
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
    return (
      formData.node_parser.parser_type === "hierarchical" ||
      formData.node_parser.parser_type === "kbadmin_parser"
    );
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
