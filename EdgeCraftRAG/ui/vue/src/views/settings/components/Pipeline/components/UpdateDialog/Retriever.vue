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
      <a-form-item
        :label="$t('pipeline.config.retrieverType')"
        name="retriever_type"
        ><div class="flex-left">
          <a-select
            showSearch
            v-model:value="form.retriever_type"
            :placeholder="$t('pipeline.valid.retrieverType')"
            @change="handleTypeChange"
          >
            <a-select-option
              v-for="item in retrieverList"
              :key="item.value"
              :value="item.value"
              >{{ item.name }}</a-select-option
            >
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.retrieverType')" />
        </div>
        <div class="option-introduction">
          <InfoCircleOutlined />
          {{ $t(optionIntroduction!) }}
        </div>
      </a-form-item>
    </div>

    <a-form-item
      :label="$t('pipeline.config.topk')"
      name="retrieve_topk"
      class="slider-wrap"
    >
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
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { Retriever } from "../../enum.ts";
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
  retriever_type: string;
  retrieve_topk: number;
}

const { retriever_type = "vectorsimilarity", retrieve_topk = 30 } =
  props.formData?.retriever || {};
const { indexer_type = "" } = props.formData?.indexer || {};

const validateIndeserType = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("pipeline.valid.retrieverType"));
  }
  if (indexer_type === "kbadmin_indexer" && value !== "kbadmin_retriever") {
    return Promise.reject(t("pipeline.valid.retrieverTypeFormat"));
  }
  return Promise.resolve();
};

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  retriever_type,
  retrieve_topk,
});
const rules: FormRules = reactive({
  retriever_type: [
    {
      required: true,
      validator: validateIndeserType,
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

const isCreate = computed(() => {
  return props.formType === "create";
});
const isKbadmin = computed(() => {
  return form.retriever_type === "kbadmin_retriever";
});
const retrieverList = computed(() => {
  if (isCreate.value) {
    return Retriever;
  }
  return isKbadmin.value
    ? Retriever.filter((item) => item.value === "kbadmin_retriever")
    : Retriever.filter((item) => item.value !== "kbadmin_retriever");
});
const optionIntroduction = computed(() => {
  const { retriever_type } = form;

  return Retriever.find((item) => item.value === retriever_type)?.describe;
});
const sliderMarks = reactive<EmptyObjectType>({
  retrieval: {
    1: "1",
    500: "500",
  },
});
const handleTypeChange = (value: SelectValue) => {
  if (value === "kbadmin_retriever")
    antNotification(
      "warning",
      t("common.prompt"),
      t("pipeline.valid.retrieverTypeTip")
    );
};
const handleTopkChange = () => {
  formRef.value?.validateFields(["retrieve_topk"]);
};
const generateFormData = () => {
  const baseData = { retriever: form };
  const { indexer } = props.formData;

  if (isKbadmin.value && indexer_type !== "kbadmin_indexer") {
    antNotification(
      "warning",
      t("common.prompt"),
      t("pipeline.valid.retrieverTypeTip")
    );
    return {
      ...baseData,
      node_parser: { parser_type: "kbadmin_parser" },
      indexer: {
        ...indexer,
        indexer_type: "kbadmin_indexer",
        embedding_url: "",
        vector_url: "",
      },
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
        let dest = null;
        if (indexer_type !== "kbadmin_indexer" && isKbadmin.value) {
          antNotification(
            "warning",
            t("common.prompt"),
            t("pipeline.valid.retrieverValid")
          );
          dest = 3;
        }
        resolve({
          result: true,
          data: generateFormData(),
          dest,
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
