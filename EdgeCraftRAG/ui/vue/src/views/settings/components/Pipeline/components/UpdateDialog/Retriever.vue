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
    <div class="column-wrap">
      <a-form-item :label="$t('pipeline.config.retrieverType')" name="retriever_type"
        ><div class="flex-left">
          <a-select
            showSearch
            v-model:value="form.retriever_type"
            :placeholder="$t('pipeline.valid.retrieverType')"
          >
            <a-select-option v-for="item in retrieverList" :key="item.value" :value="item.value">{{
              item.name
            }}</a-select-option>
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.retrieverType')" />
        </div>
        <div class="option-introduction">
          <InfoCircleOutlined />
          {{ $t(optionIntroduction!) }}
        </div>
      </a-form-item>
    </div>

    <a-form-item :label="$t('pipeline.config.topk')" name="retrieve_topk" class="slider-wrap">
      <a-slider
        v-model:value="form.retrieve_topk"
        :min="1"
        :max="500"
        :marks="sliderMarks.retrieval"
      />
      <a-form-item noStyle>
        <a-input-number
          v-model:value="form.retrieve_topk"
          :min="1"
          :max="500"
          @change="handleTopkChange"
        />
      </a-form-item>
      <FormTooltip :title="$t('pipeline.desc.topk')" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Retriever">
  import { useNotification } from "@/utils/common";
import { InfoCircleOutlined } from "@ant-design/icons-vue";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import { Retriever } from "../../enum.ts";

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
    retriever_type: string;
    retrieve_topk: number;
  }

  const { retriever_type = "vectorsimilarity", retrieve_topk = 30 } =
    props.formData?.retriever || {};
  const { indexer_type = "" } = props.formData?.indexer || {};

  const formRef = ref<FormInstance>();
  const form = reactive<FormType>({
    retriever_type,
    retrieve_topk,
  });
  const rules: FormRules = reactive({
    retriever_type: [
      {
        required: true,
        message: t("pipeline.valid.retrieverType"),
        trigger: "change",
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
  const isKbadmin = computed(() => {
    return form.retriever_type === "kbadmin_retriever";
  });
  const retrieverList = Retriever;
  const optionIntroduction = computed(() => {
    const { retriever_type } = form;

    return Retriever.find(item => item.value === retriever_type)?.describe;
  });
  const sliderMarks = reactive<EmptyObjectType>({
    retrieval: {
      1: "1",
      500: "500",
    },
  });
  const handleTopkChange = () => {
    formRef.value?.validateFields(["retrieve_topk"]);
  };
  // Validate the form, throw results form
  const handleValidate = (): Promise<object> => {
    return new Promise(resolve => {
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
