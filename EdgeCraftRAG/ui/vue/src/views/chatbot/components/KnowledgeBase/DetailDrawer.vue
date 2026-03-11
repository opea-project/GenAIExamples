<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="$t('knowledge.detail')"
    destroyOnClose
    width="500px"
    @close="handleClose"
  >
    <!-- basic -->
    <div class="basic-wrap">
      <p class="basic-item">
        <span class="label-wrap">{{ $t("knowledge.name") }}</span>
        <span class="content-wrap">{{ formData.name }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("knowledge.class") }}</span>
        <span class="content-wrap">{{ formData.comp_subtype }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("knowledge.activated") }}</span>
        <span :class="{ 'active-state': formData.active, 'content-wrap': true }">{{
          formData.active ? $t("pipeline.activated") : $t("pipeline.inactive")
        }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("knowledge.des") }}</span>
        <span class="content-wrap">{{ formData.description || "--" }}</span>
      </p>
    </div>
    <!-- Node Parser -->
    <div class="module-wrap" v-if="!isKbadmin">
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
                formData.indexer.embedding_model?.api_base
              }}</span>
            </li>
            <li class="item-wrap">
              <span class="label-wrap">{{ $t("pipeline.config.embedding") }}</span>
              <span class="content-wrap">{{ formData.indexer.embedding_model?.model_id }}</span>
            </li>
            <li class="item-wrap" v-if="formData.indexer.inference_type === 'local'">
              <span class="label-wrap">{{ $t("pipeline.config.embeddingDevice") }}</span>
              <span class="content-wrap">{{ formData.indexer.embedding_model?.device }}</span>
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
  const nodeParserActive = ref<string>("nodeParser");
  const indexerActive = ref<string>("indexer");

  const isKbadmin = computed(() => {
    return formData.comp_subtype === "kbadmin_kb";
  });
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
