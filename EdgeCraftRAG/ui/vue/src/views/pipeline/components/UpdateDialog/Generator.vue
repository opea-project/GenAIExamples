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
        <a-radio value="vllm">{{ $t("pipeline.config.vllm") }}</a-radio>
        <a-radio value="local">{{ $t("pipeline.config.local") }}</a-radio>
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
    <template v-else>
      <a-form-item
        :label="$t('pipeline.config.language')"
        name="modelName"
        :rules="rules.modelName"
      >
        <a-input
          v-model:value.trim="form.modelName"
          :placeholder="$t('pipeline.valid.modelName')"
        >
        </a-input>
        <FormTooltip :title="$t('pipeline.desc.language')" />
      </a-form-item>
      <a-form-item
        :label="$t('pipeline.config.vllm_url')"
        name="vllm_endpoint"
        :rules="rules.vllm_endpoint"
      >
        <a-input
          v-model:value="form.vllm_endpoint"
          :addon-before="protocol"
          :placeholder="$t('pipeline.valid.vllm_url')"
          @change="handleUrlChange"
        >
          <template #addonAfter>
            <a-button
              type="primary"
              class="text-btn"
              :disabled="!isPass"
              @click="handleTestUrl"
            >
              <CheckCircleFilled
                v-if="validatePass"
                :style="{ color: 'var(--color-success)', fontSize: '18px' }"
              />
              <span v-else> {{ $t("pipeline.desc.test") }}</span>
            </a-button>
          </template>
        </a-input>
        <FormTooltip :title="$t('pipeline.desc.vllm_url')" />
      </a-form-item>
    </template>
  </a-form>
</template>

<script lang="ts" setup name="Generator">
import {
  getModelWeight,
  getRunDevice,
  getModelList,
  requestUrlVllm,
} from "@/api/pipeline";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref, onMounted } from "vue";
import { Generator } from "../../enum.ts";
import { ModelType } from "../../type.ts";
import { useI18n } from "vue-i18n";
import { CheckCircleFilled } from "@ant-design/icons-vue";
import { validateIpPort } from "@/utils/validate.ts";
import { useNotification } from "@/utils/common";

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
  generator_type: string;
  inference_type: string;
  model: ModelType;
  vllm_endpoint?: string;
  modelName?: string;
}
const validateUnique = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("pipeline.valid.vllmUrlValid1"));
  }
  if (!validateIpPort(value)) {
    return Promise.reject(t("pipeline.valid.vllmUrlValid2"));
  }

  isPass.value = true;
  return Promise.resolve();
};
const handleUrlFormat = (url: string) => {
  if (!url) return "";
  return url.replace(/http:\/\//g, "");
};
const {
  generator_type = "chatqna",
  inference_type = "vllm",
  vllm_endpoint = "",
  model = {
    model_id: undefined,
    model_path: "",
    device: "AUTO",
    weight: undefined,
  },
} = props.formData?.generator || {};

const isPass = ref<boolean>(false);
const validatePass = ref<boolean>(false);
const protocol = ref<string>("http://");
const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  generator_type,
  inference_type,
  vllm_endpoint: handleUrlFormat(vllm_endpoint),
  modelName: inference_type === "vllm" ? model.model_id : "",
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
  vllm_endpoint: [
    {
      required: true,
      validator: validateUnique,
      trigger: "blur",
    },
  ],
  modelName: [
    {
      required: true,
      message: t("pipeline.valid.modelName"),
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
const handleUrlChange = () => {
  isPass.value = false;
  validatePass.value = false;
};
// Format parameter
const formatFormParam = () => {
  const { inference_type, model, modelName, vllm_endpoint } = form;
  const { model_id, weight } = model;
  model.model_path = handleModelPath(model_id, weight);
  model.model_id = inference_type === "vllm" ? modelName : model_id;
  return {
    inference_type,
    prompt_path: "./default_prompt.txt",
    model,
    vllm_endpoint:
      inference_type === "vllm" ? protocol.value + vllm_endpoint : undefined,
  };
};

const handleTestUrl = async () => {
  formRef.value?.validateFields(["modelName"]);
  const { modelName } = form;
  if (!modelName) return;
  const server_address = protocol.value + form.vllm_endpoint;

  const { status = "" } = await requestUrlVllm({
    server_address,
    model_name: modelName,
  });
  if (status !== "200") {
    antNotification(
      "error",
      t("common.error"),
      t("pipeline.valid.vllmUrlValid3")
    );
    return;
  }
  validatePass.value = true;
  antNotification(
    "success",
    t("common.success"),
    t("pipeline.valid.vllmUrlValid4")
  );
};
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        if (form.inference_type === "vllm" && !validatePass.value) {
          antNotification(
            "warning",
            t("common.prompt"),
            t("pipeline.valid.vllmUrlValid5")
          );
          return;
        }
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
onMounted(() => {
  if (props.formType === "update") {
    isPass.value = true;
    validatePass.value = true;
  }
});
</script>

<style scoped lang="less">
:deep(.intel-input-group) {
  .intel-input-group-addon {
    overflow: hidden;
  }
}
.text-btn {
  width: 72px;
  height: 30px;
  margin: 0 -11px;
  border-radius: 0 6px 6px 0;
}
</style>
