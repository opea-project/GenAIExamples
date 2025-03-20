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
    <a-form-item label="Node Parser Type" name="parser_type">
      <a-select
        v-model:value="form.parser_type"
        showSearch
        placeholder="please select Node Parser Type"
      >
        <a-select-option
          v-for="item in nodeParserList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip title="Node parsing type when you use RAG" />
    </a-form-item>
    <div class="option-introduction">
      <InfoCircleOutlined />
      {{ optionIntroduction }}
    </div>
    <template v-if="!isHierarchical && !isSentencewindow">
      <a-form-item label="Chunk Size" name="chunk_size" class="slider-wrap">
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
          />
        </a-form-item>
        <FormTooltip title="Size of each chunk for processing" />
      </a-form-item>
      <a-form-item
        label="Chunk Overlap"
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
          />
        </a-form-item>
        <FormTooltip title="Overlap size between chunks" /> </a-form-item
    ></template>
    <template v-if="isSentencewindow">
      <a-form-item label="Window Size" name="window_size" class="slider-wrap">
        <a-slider
          v-model:value="form.window_size"
          :min="1"
          :max="10"
          :marks="sliderMarks.size"
        />
        <a-form-item noStyle>
          <a-input-number v-model:value="form.window_size" :min="1" :max="10" />
        </a-form-item>
        <FormTooltip
          title="The number of sentences on each side of a sentence to capture"
        />
      </a-form-item>
    </template>
  </a-form>
</template>

<script lang="ts" setup name="NodeParser">
import type { FormInstance } from "ant-design-vue";
import { computed, reactive, ref } from "vue";
import { NodeParser } from "../../enum.ts";
import { InfoCircleOutlined } from "@ant-design/icons-vue";

const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
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
      return Promise.reject("Please select Chunk Size");
    } else if (form?.chunk_overlap && value < form?.chunk_overlap) {
      return Promise.reject(
        "The value of Chunk Size cannot be less than Chunk Overlap"
      );
    } else {
      return Promise.resolve();
    }
  },
  chunkOverlap: async (_rule: any, value: number) => {
    if (!value) {
      return Promise.reject("Please select Chunk Overlap");
    } else if (form?.chunk_size && value > form?.chunk_size) {
      return Promise.reject(
        "The value of Chunk Overlap cannot be greater than Chunk Size"
      );
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
const rules = reactive({
  parser_type: [
    {
      required: true,
      message: "please select Node Parser Type",
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
      message: "Please select Chunk Window Size",
      trigger: ["change", "blur"],
    },
  ],
});

const nodeParserList = NodeParser;
const isHierarchical = computed(() => {
  return form.parser_type === "hierarchical";
});
const isSentencewindow = computed(() => {
  return form.parser_type === "sentencewindow";
});
const optionIntroduction = computed(() => {
  const { parser_type } = form;

  return nodeParserList.find((item) => item.value === parser_type)?.describe;
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
});
// Format parameter
const formatFormParam = () => {
  const { parser_type, chunk_size, chunk_overlap, chunk_sizes, window_size } =
    form;

  return {
    parser_type,
    chunk_sizes: isHierarchical.value ? chunk_sizes : undefined,
    window_size: isSentencewindow.value ? window_size : undefined,
    chunk_size:
      !isHierarchical.value && !isSentencewindow.value ? chunk_size : undefined,
    chunk_overlap:
      !isHierarchical.value && !isSentencewindow.value
        ? chunk_overlap
        : undefined,
  };
};
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        resolve({
          result: true,
          data: { node_parser: formatFormParam() },
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
