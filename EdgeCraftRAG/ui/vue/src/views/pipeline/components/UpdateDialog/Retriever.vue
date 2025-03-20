<template>
  <a-form
    :model="form"
    :rules="rules"
    name="retriever"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <a-form-item label="Retriever Type" name="retriever_type">
      <a-select
        v-model:value="form.retriever_type"
        showSearch
        placeholder="please select Retriever Type"
      >
        <a-select-option
          v-for="item in retrieverList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip
        title="The retrieval type used when retrieving relevant nodes from the index according to the user's query"
      />
    </a-form-item>
    <div class="option-introduction">
      <InfoCircleOutlined />
      {{ optionIntroduction }}
    </div>
    <a-form-item label="Search top k" name="retrieve_topk" class="slider-wrap">
      <a-slider
        v-model:value="form.retrieve_topk"
        :min="1"
        :max="50"
        :marks="sliderMarks.retrieval"
      />
      <a-form-item noStyle>
        <a-input-number v-model:value="form.retrieve_topk" :min="1" :max="50" />
      </a-form-item>
      <FormTooltip title="The number of top k results to return" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Retriever">
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { Retriever } from "../../enum.ts";
import { InfoCircleOutlined } from "@ant-design/icons-vue";

const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
});
interface FormType {
  retriever_type: string;
  retrieve_topk: number;
}
const { retriever_type = "vectorsimilarity", retrieve_topk = 30 } =
  props.formData?.retriever || {};

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  retriever_type,
  retrieve_topk,
});
const rules = reactive({
  retriever_type: [
    {
      required: true,
      message: "please select Retriever Type",
      trigger: "blur",
    },
  ],
  retrieve_topk: [
    {
      required: true,
      message: "Please select Search top k",
      trigger: ["change", "blur"],
    },
  ],
});
const retrieverList = Retriever;
const optionIntroduction = computed(() => {
  const { retriever_type } = form;

  return retrieverList.find((item) => item.value === retriever_type)?.describe;
});
const sliderMarks = reactive<EmptyObjectType>({
  retrieval: {
    1: "1",
    50: "50",
  },
});
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        resolve({
          result: true,
          data: { retriever: form },
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
