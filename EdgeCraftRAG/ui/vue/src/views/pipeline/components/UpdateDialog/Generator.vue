<template>
  <a-form
    :model="form"
    :rules="rules"
    name="generator"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <a-form-item
      :label="$t('pipeline.config.generatorType')"
      name="generator_type"
    >
      <a-select
        showSearch
        v-model:value="form.generator_type"
        :placeholder="$t('pipeline.valid.generatorType')"
      >
        <a-select-option
          v-for="item in generatorList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip :title="$t('pipeline.desc.generatorType')" />
    </a-form-item>
    <a-form-item :label="$t('pipeline.config.llm')" name="inference_type">
      <a-radio-group v-model:value="form.inference_type">
        <a-radio value="local">{{ $t("pipeline.config.local") }}</a-radio>
        <a-radio value="vllm">{{ $t("pipeline.config.vllm") }}</a-radio>
      </a-radio-group>
    </a-form-item>
    <template v-if="form.inference_type === 'local'">
      <a-form-item
        :label="$t('pipeline.config.language')"
        :name="['model', 'model_id']"
        :rules="rules.model_id"
      >
        <a-select
          showSearch
          v-model:value="form.model.model_id"
          :placeholder="$t('pipeline.valid.language')"
          @change="handleModelChange"
          @dropdownVisibleChange="handleModelVisible"
        >
          <a-select-option
            v-for="item in modelList"
            :key="item"
            :value="item"
            >{{ item }}</a-select-option
          >
        </a-select>
        <FormTooltip :title="$t('pipeline.desc.language')" />
      </a-form-item>
      <a-form-item
        :label="$t('pipeline.config.llmDevice')"
        :name="['model', 'device']"
        :rules="rules.device"
      >
        <a-select
          showSearch
          v-model:value="form.model.device"
          :placeholder="$t('pipeline.valid.llmDevice')"
          @dropdownVisibleChange="handleDeviceVisible"
        >
          <a-select-option
            v-for="item in deviceList"
            :key="item"
            :value="item"
            >{{ item }}</a-select-option
          >
        </a-select>
        <FormTooltip :title="$t('pipeline.desc.llmDevice')" />
      </a-form-item>
      <a-form-item
        :label="$t('pipeline.config.weights')"
        :name="['model', 'weight']"
        :rules="rules.weight"
      >
        <a-select
          showSearch
          v-model:value="form.model.weight"
          :placeholder="$t('pipeline.valid.weights')"
          @dropdownVisibleChange="handleWeightVisible"
        >
          <a-select-option
            v-for="item in generatorWeightList"
            :key="item"
            :value="item"
            >{{ item }}</a-select-option
          >
        </a-select>
        <FormTooltip :title="t('pipeline.desc.weights')" />
      </a-form-item>
    </template>
  </a-form>
</template>

<script lang="ts" setup name="Generator">
import { getModelWeight, getRunDevice, getModelList } from "@/api/pipeline";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { Generator } from "../../enum.ts";
import { ModelType } from "../../type.ts";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
});
interface FormType {
  generator_type: string;
  inference_type: string;
  model: ModelType;
}
const {
  generator_type = "chatqna",
  inference_type = "local",
  model = {
    model_id: "Qwen/Qwen2-7B-Instruct",
    model_path: "",
    device: "AUTO",
    weight: "INT4",
  },
} = props.formData?.generator || {};

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  generator_type,
  inference_type,
  model,
});
const rules = reactive({
  generator_type: [
    {
      required: true,
      message: t("pipeline.valid.generatorType"),
      trigger: "change",
    },
  ],
  inference_type: [
    {
      required: true,
      message: t("pipeline.valid.generatorType"),
      trigger: "change",
    },
  ],
  model_id: [
    {
      required: true,
      message: t("pipeline.valid.language"),
      trigger: "change",
    },
  ],
  device: [
    {
      required: true,
      message: t("pipeline.valid.llmDevice"),
      trigger: "change",
    },
  ],
  weight: [
    {
      required: true,
      message: t("pipeline.valid.weights"),
      trigger: "change",
    },
  ],
});
const generatorList = Generator;
const generatorWeightList = ref<EmptyArrayType>([]);
const modelList = ref<EmptyArrayType>([]);
const deviceList = ref<EmptyArrayType>([]);

// Complete model_cath
const handleModelChange = () => {
  form.model.weight = "";
};
// Handling Model Folding Events
const handleModelVisible = async (visible: boolean) => {
  if (visible) {
    try {
      const data: any = await getModelList("LLM");
      modelList.value = [].concat(data);
    } catch (err) {
      console.error(err);
    }
  }
};
const handleModelPath = (
  modelId: string,
  weights?: string,
  prefix: string = "./models/"
) => {
  const modelDirs = {
    fp16_model: prefix + modelId + "/FP16/",
    int8_model: prefix + modelId + "/INT8_compressed_weights/",
    int4_model: prefix + modelId + "/INT4_compressed_weights/",
  };
  let modelPath: string = "";
  switch (weights) {
    case "INT4":
      modelPath = modelDirs["int4_model"];
      break;
    case "INT8":
      modelPath = modelDirs["int8_model"];
      break;
    default:
      modelPath = modelDirs["fp16_model"];
  }
  return modelPath;
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
// Handling Weight Folding Events
const handleWeightVisible = async (visible: boolean) => {
  if (visible) {
    try {
      const { model_id } = form.model;
      const data: any = await getModelWeight(model_id);
      generatorWeightList.value = [].concat(data);
    } catch (err) {
      console.error(err);
    }
  }
};

// Format parameter
const formatFormParam = () => {
  const { inference_type, model } = form;
  const { model_id, weight } = model;
  model.model_path = handleModelPath(model_id, weight);

  return {
    inference_type,
    prompt_path: "./default_prompt.txt",
    model,
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
          data: { generator: formatFormParam() },
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
