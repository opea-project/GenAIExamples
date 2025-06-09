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
    <a-form-item
      :label="$t('pipeline.config.retrieverType')"
      name="retriever_type"
    >
      <a-select
        v-model:value="form.retriever_type"
        showSearch
        :placeholder="$t('pipeline.valid.retrieverType')"
      >
        <a-select-option
          v-for="item in retrieverList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip :title="$t('pipeline.desc.retrieverType')" />
    </a-form-item>
    <div class="option-introduction">
      <InfoCircleOutlined />
      {{ $t(optionIntroduction!) }}
    </div>
    <a-form-item
      :label="$t('pipeline.config.topk')"
      name="retrieve_topk"
      class="slider-wrap"
    >
      <a-slider
        v-model:value="form.retrieve_topk"
        :min="1"
        :max="200"
        :marks="sliderMarks.retrieval"
      />
      <a-form-item noStyle>
        <a-input-number
          v-model:value="form.retrieve_topk"
          :min="1"
          :max="200"
        />
      </a-form-item>
      <FormTooltip :title="$t('pipeline.desc.topk')" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Retriever">
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { Retriever } from "../../enum.ts";
import { InfoCircleOutlined } from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
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
      message: t("pipeline.valid.retrieverType"),
      trigger: "blur",
    },
  ],
  retrieve_topk: [
    {
      required: true,
      message: t("pipeline.valid.topk"),
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
    200: "200",
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
