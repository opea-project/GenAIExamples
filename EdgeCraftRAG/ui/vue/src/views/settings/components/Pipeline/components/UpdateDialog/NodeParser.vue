<template>
  <a-form
    :model="form"
    :rules="rules"
    name="nodeParser"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <a-form-item
      :label="$t('pipeline.config.nodeParserType')"
      name="parser_type"
    >
      <a-select
        showSearch
        v-model:value="form.parser_type"
        :placeholder="$t('pipeline.valid.nodeParserType')"
        @change="handleTypeChange"
      >
        <a-select-option
          v-for="item in nodeParserList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip :title="$t('pipeline.desc.nodeParserType')" />
    </a-form-item>
    <div class="option-introduction">
      <InfoCircleOutlined />
      {{ $t(optionIntroduction!) }}
    </div>
    <template v-if="!isHierarchical && !isSentencewindow && !isKbadmin">
      <a-form-item
        :label="$t('pipeline.config.chunkSize')"
        name="chunk_size"
        class="slider-wrap"
      >
        <a-slider
          v-model:value="form.chunk_size"
          :min="100"
          :max="2000"
          :marks="sliderMarks.size"
        />
        <a-form-item noStyle>
          <a-input-number
            v-model:value="form.chunk_size"
            :min="100"
            :max="2000"
            @change="handleChunkSizeChange"
          />
        </a-form-item>
        <FormTooltip :title="$t('pipeline.desc.chunkSize')" />
      </a-form-item>
      <a-form-item
        :label="$t('pipeline.config.chunkOverlap')"
        name="chunk_overlap"
        class="slider-wrap"
      >
        <a-slider
          v-model:value="form.chunk_overlap"
          :min="0"
          :max="400"
          :marks="sliderMarks.overlap"
        />
        <a-form-item noStyle>
          <a-input-number
            v-model:value="form.chunk_overlap"
            :min="0"
            :max="400"
            @change="handleChunkOverlapChange"
          />
        </a-form-item>
        <FormTooltip :title="$t('pipeline.desc.chunkOverlap')" /> </a-form-item
    ></template>
    <template v-if="isSentencewindow">
      <a-form-item
        :label="$t('pipeline.config.windowSize')"
        name="window_size"
        class="slider-wrap"
      >
        <a-slider
          v-model:value="form.window_size"
          :min="1"
          :max="10"
          :marks="sliderMarks.window"
        />
        <a-form-item noStyle>
          <a-input-number
            v-model:value="form.window_size"
            :min="1"
            :max="10"
            @change="handleWindowSizeChange"
          />
        </a-form-item>
        <FormTooltip :title="$t('pipeline.desc.windowSize')" />
      </a-form-item>
    </template>
  </a-form>
</template>

<script lang="ts" setup name="NodeParser">
import type { FormInstance } from "ant-design-vue";
import { computed, reactive, ref } from "vue";
import { NodeParser } from "../../enum.ts";
import { InfoCircleOutlined } from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";
import { useNotification } from "@/utils/common";
import { SelectValue } from "ant-design-vue/es/select/index";

const { t } = useI18n();
const { antNotification } = useNotification();
const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
  formType: {
    type: String,
    default: "create",
  },
});
interface FormType {
  parser_type: string;
  chunk_size?: number;
  chunk_overlap?: number;
  chunk_sizes?: number[];
  window_size?: number;
}

const validate = {
  chunkSize: async (_rule: any, value: number) => {
    if (!value) {
      return Promise.reject(t("pipeline.valid.chunkSizeValid1"));
    } else if (form?.chunk_overlap && value < form?.chunk_overlap) {
      return Promise.reject(t("pipeline.valid.chunkSizeValid2"));
    } else {
      return Promise.resolve();
    }
  },
  chunkOverlap: async (_rule: any, value: number) => {
    if (form?.chunk_size && value > form?.chunk_size) {
      return Promise.reject(t("pipeline.valid.chunkOverlapValid2"));
    } else {
      return Promise.resolve();
    }
  },
};

const {
  parser_type = "simple",
  chunk_size = 250,
  chunk_overlap = 48,
  chunk_sizes = [2048, 512, 128],
  window_size = 3,
} = props.formData?.node_parser || {};

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  parser_type,
  chunk_size,
  chunk_overlap,
  chunk_sizes,
  window_size,
});
const rules: FormRules = reactive({
  parser_type: [
    {
      required: true,
      message: t("pipeline.valid.retrieverType"),
      trigger: "blur",
    },
  ],
  chunk_size: [
    {
      required: true,
      validator: validate.chunkSize,
      trigger: ["change", "blur"],
    },
  ],
  chunk_overlap: [
    {
      required: true,
      validator: validate.chunkOverlap,
      trigger: ["change", "blur"],
    },
  ],
  window_size: [
    {
      required: true,
      message: t("pipeline.valid.windowSize"),
      trigger: ["change", "blur"],
    },
  ],
});

const isCreate = computed(() => {
  return props.formType === "create";
});
const isHierarchical = computed(() => {
  return form.parser_type === "hierarchical";
});
const isKbadmin = computed(() => {
  return form.parser_type === "kbadmin_parser";
});
const isSentencewindow = computed(() => {
  return form.parser_type === "sentencewindow";
});
const nodeParserList = computed(() => {
  if (isCreate.value) {
    return NodeParser;
  }
  return isKbadmin.value
    ? NodeParser.filter((item) => item.value === "kbadmin_parser")
    : NodeParser.filter((item) => item.value !== "kbadmin_parser");
});
const optionIntroduction = computed(() => {
  const { parser_type } = form;

  return NodeParser.find((item) => item.value === parser_type)?.describe;
});
const sliderMarks = reactive<EmptyObjectType>({
  size: {
    100: "100",
    2000: "2000",
  },
  overlap: {
    0: "0",
    400: "400",
  },
  window: {
    1: "1",
    10: "10",
  },
});

const handleTypeChange = (value: SelectValue) => {
  if (value === "kbadmin_parser")
    antNotification(
      "warning",
      t("common.prompt"),
      t("pipeline.valid.nodeParserTypeTip")
    );
};
const handleChunkSizeChange = () => {
  formRef.value?.validateFields(["chunk_size"]);
};
const handleChunkOverlapChange = () => {
  formRef.value?.validateFields(["chunk_overlap"]);
};
const handleWindowSizeChange = () => {
  formRef.value?.validateFields(["window_size"]);
};
// Format parameter
const formatFormParam = () => {
  const { parser_type, chunk_size, chunk_overlap, chunk_sizes, window_size } =
    form;

  const chunkSizes = isHierarchical.value ? chunk_sizes : undefined;
  const windowSize = isSentencewindow.value ? window_size : undefined;

  const chunkSize =
    !isHierarchical.value && !isSentencewindow.value && !isKbadmin.value
      ? chunk_size
      : undefined;

  const chunkOverlap = isHierarchical.value
    ? 20
    : isKbadmin.value
    ? undefined
    : !isSentencewindow.value
    ? chunk_overlap
    : undefined;

  return {
    parser_type,
    chunk_sizes: chunkSizes,
    window_size: windowSize,
    chunk_size: chunkSize,
    chunk_overlap: chunkOverlap,
  };
};
const generateFormData = () => {
  const baseData = { node_parser: formatFormParam() };
  const { indexer, retriever } = props.formData;

  if (isKbadmin.value) {
    return {
      ...baseData,
      indexer: { ...indexer, indexer_type: "kbadmin_indexer" },
      retriever: { ...retriever, retriever_type: "kbadmin_retriever" },
    };
  }

  return baseData;
};
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        resolve({
          result: true,
          data: generateFormData(),
        });
      })
      .catch(() => {
        resolve({ result: false });
      });
  });
};
defineExpose({
  validate: handleValidate,
});
</script>

<style scoped lang="less"></style>
