<template>
  <a-form
    :model="form"
    :rules="rules"
    name="postProcessor"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <div
      class="processor-wrap"
      v-for="(processor, index) in form.postprocessor"
      :key="index"
    >
      <a-form-item
        :label="$t('pipeline.config.postProcessorType')"
        :name="['postprocessor', index, 'processor_type']"
        :rules="rules.processor_type"
      >
        <a-select
          showSearch
          v-model:value="processor.processor_type"
          :placeholder="$t('pipeline.valid.postProcessorType')"
        >
          <a-select-option
            v-for="item in postProcessorList"
            :key="item.value"
            :value="item.value"
            :disabled="getDisable(item.value)"
            >{{ item.name }}</a-select-option
          >
        </a-select>
        <FormTooltip :title="$t('pipeline.desc.postProcessorType')" />
      </a-form-item>
      <div class="option-introduction" v-if="processor.processor_type">
        <InfoCircleOutlined />
        {{ $t(getOptionIntroduction(processor.processor_type)!) }}
      </div>
      <template v-if="processor.processor_type === 'reranker'">
        <a-form-item
          :label="$t('pipeline.config.rerank')"
          :name="['postprocessor', index, 'reranker_model', 'model_id']"
          :rules="rules.model_id"
        >
          <a-select
            showSearch
            v-model:value="processor.reranker_model.model_id"
            :placeholder="$t('pipeline.valid.rerank')"
            @dropdownVisibleChange="handleModelVisible"
            @change="(value:string) => handleModelChange(processor.reranker_model, value)"
          >
            <a-select-option
              v-for="item in modelList"
              :key="item"
              :value="item"
              >{{ item }}</a-select-option
            >
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.rerank')" />
        </a-form-item>
        <a-form-item
          :label="$t('pipeline.config.rerankDevice')"
          :name="['postprocessor', index, 'reranker_model', 'device']"
          :rules="rules.device"
        >
          <a-select
            showSearch
            v-model:value="processor.reranker_model.device"
            :placeholder="$t('pipeline.valid.rerankDevice')"
            @dropdownVisibleChange="handleDeviceVisible"
          >
            <a-select-option
              v-for="item in deviceList"
              :key="item"
              :value="item"
              >{{ item }}</a-select-option
            >
          </a-select>
          <FormTooltip
            :title="$t('pipeline.desc.rerankDevice')"
          /> </a-form-item
      ></template>
      <div class="icon-wrap">
        <a-tooltip
          placement="topRight"
          arrow-point-at-center
          :title="$t('common.add')"
          v-if="form.postprocessor?.length < 2"
        >
          <PlusCircleOutlined @click="handleAdd" />
        </a-tooltip>
        <a-tooltip
          placement="topRight"
          arrow-point-at-center
          :title="$t('common.delete')"
          v-if="form.postprocessor?.length > 1"
        >
          <MinusCircleOutlined @click="handleDelete(index)" />
        </a-tooltip>
      </div>
    </div>
  </a-form>
</template>

<script lang="ts" setup name="PostProcessor">
import { getRunDevice, getModelList } from "@/api/pipeline";
import { MinusCircleOutlined, PlusCircleOutlined } from "@ant-design/icons-vue";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { PostProcessor } from "../../enum.ts";
import { ModelType } from "../../type.ts";
import { InfoCircleOutlined } from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
});

interface ProcessorType {
  processor_type: string;
  top_n?: number;
  reranker_model: ModelType;
}
interface FormType {
  postprocessor: ProcessorType[];
}
const { postprocessor = [] } = props.formData.postprocessor || [];

const defaultConfig = [
  {
    processor_type: "reranker",
    top_n: 5,
    reranker_model: {
      model_id: "BAAI/bge-reranker-large",
      model_path: "./models/BAAI/bge-reranker-large",
      device: "AUTO",
      weight: "INT4",
    },
  },
];
const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  postprocessor: postprocessor.length ? postprocessor : defaultConfig,
});
const rules = reactive({
  processor_type: [
    {
      required: true,
      message: t("pipeline.valid.postProcessorType"),
      trigger: "change",
    },
  ],
  model_id: [
    {
      required: true,
      message: t("pipeline.valid.rerank"),
      trigger: "change",
    },
  ],
  device: [
    {
      required: true,
      message: t("pipeline.valid.rerankDevice"),

      trigger: "change",
    },
  ],
});
const postProcessorList = PostProcessor;
const modelList = ref<EmptyArrayType>([]);
const deviceList = ref<EmptyArrayType>([]);
const getDisable = (value: string) => {
  return form.postprocessor.some((item) => item.processor_type === value);
};
const getOptionIntroduction = (value: string) => {
  return postProcessorList.find((item) => item.value === value)?.describe;
};
// Handling Model Folding Events
const handleModelVisible = async (visible: boolean) => {
  if (visible) {
    try {
      const data: any = await getModelList("reranker");
      modelList.value = [].concat(data);
    } catch (err) {
      console.error(err);
    }
  }
};
//Complete model_cath
const handleModelChange = (item: EmptyObjectType, value: string) => {
  item.model_path = `./models/${value}`;
};
const handleAdd = () => {
  form.postprocessor.push({
    processor_type: "",
    reranker_model: {
      model_id: "",
      model_path: "",
      device: "",
      weight: "INT4",
    },
  });
};
const handleDelete = (index: number) => {
  form.postprocessor.splice(index, 1);
};
// Handling Device Folding Events
const handleDeviceVisible = async (visible: boolean) => {
  if (visible) {
    try {
      const data: any = await getRunDevice();
      deviceList.value = [].concat(data);
    } catch (err) {
      console.error(err);
    }
  }
};
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        resolve({
          result: true,
          data: form,
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

<style scoped lang="less">
.processor-wrap {
  padding: 16px;
  border: 1px solid var(--border-main-color);
  position: relative;
  margin-bottom: 20px;
  border-radius: 6px;
  .icon-wrap {
    position: absolute;
    top: 12px;
    right: 16px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    .anticon {
      font-size: 16px;
      &:hover {
        color: var(--color-primary);
      }
    }
  }
  .slider-wrap {
    border-bottom: none !important;
  }
}
</style>
