<template>
  <a-form
    ref="formRef"
    :model="form"
    :rules="rules"
    name="generator"
    layout="vertical"
    autocomplete="off"
    class="form-wrap"
  >
    <div
      class="generator-wrap"
      v-for="(item, index) in form.generator"
      :key="`generator-${index}`"
    >
      <div class="column-wrap">
        <a-form-item
          :label="$t('pipeline.config.generatorType')"
          :name="['generator', index, 'generator_type']"
          :rules="rules.generator_type"
        >
          <div class="flex-left">
            <a-select
              showSearch
              v-model:value="item.generator_type"
              :placeholder="$t('pipeline.valid.generatorType')"
            >
              <a-select-option
                v-for="item in generatorList"
                :key="item.value"
                :value="item.value"
                :disabled="isGeneratorTypeDisabled(item.value, index)"
              >
                {{ item.name }}
              </a-select-option>
            </a-select>
            <FormTooltip :title="$t('pipeline.desc.generatorType')" />
          </div>
          <div v-if="item.generator_type" class="option-introduction">
            <InfoCircleOutlined />
            {{ $t(getOptionIntroduction(item.generator_type)!) }}
          </div>
        </a-form-item>
      </div>
      <a-form-item
        :label="$t('pipeline.config.llm')"
        :name="['generator', index, 'inference_type']"
        :rules="rules.inference_type"
      >
        <a-radio-group
          v-model:value="item.inference_type"
          @change="() => handleInferenceTypeChange(index)"
        >
          <a-radio value="vllm">{{ $t("pipeline.config.vllm") }}</a-radio>
          <a-radio value="ovms">{{ $t("pipeline.config.ovms") }}</a-radio>
          <a-radio value="local">{{ $t("pipeline.config.local") }}</a-radio>
        </a-radio-group>
      </a-form-item>
      <!-- Remote -->
      <template v-if="isRemoteInference(item.inference_type)">
        <a-form-item
          :name="[
            'generator',
            index,
            getRemoteEndpointField(item.inference_type),
          ]"
          :rules="getRemoteEndpointRules(index, item.inference_type)"
        >
          <template #label>
            {{ $t(getRemoteEndpointConfigKey(item.inference_type)) }}
            <span class="eg-wrap">{{
              $t(getRemoteEndpointValidKey(item.inference_type))
            }}</span>
          </template>

          <a-input
            :value="getRemoteEndpointValue(item, item.inference_type)"
            :placeholder="$t(getRemoteEndpointValidKey(item.inference_type))"
            @update:value="
              (value) =>
                setRemoteEndpointValue(item, item.inference_type, value)
            "
            @change="() => handleRemoteEndpointChange(index)"
          >
            <template #addonBefore>
              <a-select v-model:value="generatorStates[index].protocol">
                <a-select-option value="http://">Http://</a-select-option>
                <a-select-option value="https://">Https://</a-select-option>
              </a-select>
            </template>

            <template #addonAfter>
              <a-button
                type="primary"
                class="text-btn"
                :disabled="!generatorStates[index].isEndpointValid"
                @click="handleQueryRemoteModels(index, item.inference_type)"
              >
                <CheckCircleFilled
                  v-if="generatorStates[index].isConnected"
                  style="color: var(--color-success); font-size: 18px"
                />
                <span v-else>{{ $t("common.connect") }}</span>
              </a-button>
            </template>
          </a-input>

          <FormTooltip :title="$t('pipeline.desc.vllm_url')" />
        </a-form-item>
        <a-form-item
          :label="$t('pipeline.config.language')"
          :name="['generator', index, 'model', 'model_id']"
          :rules="rules.model_id"
        >
          <div class="model-wrap">
            <a-select
              v-model:value="item.model.model_id"
              showSearch
              :placeholder="$t('pipeline.valid.language')"
              @change="() => handleRemoteModelChange(index)"
              @dropdownVisibleChange="
                (v) => handleRemoteModelVisible(v, index, item.inference_type)
              "
            >
              <a-select-option
                v-for="item in getRemoteModelList(index, item.inference_type)"
                :key="item"
                :value="item"
              >
                {{ item }}
              </a-select-option>
            </a-select>

            <a-button
              type="primary"
              class="text-btn"
              :disabled="!item.model.model_id"
              @click="handleTestRemoteEndpoint(index, item.inference_type)"
            >
              <CheckCircleFilled
                v-if="generatorStates[index].isEndpointTested"
                style="color: var(--color-success); font-size: 18px"
              />
              <span v-else>{{ $t("pipeline.desc.test") }}</span>
            </a-button>
          </div>
          <FormTooltip :title="$t('pipeline.desc.language')" />
        </a-form-item>
      </template>
      <!-- Local -->
      <template v-else>
        <a-form-item
          :label="$t('pipeline.config.language')"
          :name="['generator', index, 'model', 'model_id']"
          :rules="rules.model_id"
        >
          <a-select
            v-model:value="item.model.model_id"
            showSearch
            :placeholder="$t('pipeline.valid.language')"
            @change="() => handleLocalModelChange(index)"
            @dropdownVisibleChange="
              (value) => handleLocalModelVisible(value, index)
            "
          >
            <a-select-option
              v-for="item in generatorStates[index].localModelList"
              :key="item"
              :value="item"
            >
              {{ item }}
            </a-select-option>
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.language')" />
        </a-form-item>

        <a-form-item
          :label="$t('pipeline.config.llmDevice')"
          :name="['generator', index, 'model', 'device']"
          :rules="rules.device"
        >
          <a-select
            v-model:value="item.model.device"
            showSearch
            :placeholder="$t('pipeline.valid.llmDevice')"
            @dropdownVisibleChange="
              (value) => handleDeviceVisible(value, index)
            "
          >
            <a-select-option
              v-for="item in generatorStates[index].deviceList"
              :key="item"
              :value="item"
            >
              {{ item }}
            </a-select-option>
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.llmDevice')" />
        </a-form-item>
      </template>
      <div class="icon-wrap">
        <a-tooltip
          placement="topRight"
          arrow-point-at-center
          :title="$t('common.add')"
          v-if="showAddIcon()"
        >
          <PlusCircleOutlined @click="handleAdd"
        /></a-tooltip>
        <a-tooltip
          placement="topRight"
          arrow-point-at-center
          :title="$t('common.delete')"
          v-if="form.generator.length > 1"
        >
          <MinusCircleOutlined @click="() => handleDelete(index)"
        /></a-tooltip>
      </div>
    </div>
  </a-form>
</template>
<script lang="ts" setup>
import {
  getModelList,
  getRunDevice,
  requestUrlOvms,
  requestUrlVllm,
} from "@/api/pipeline";
import { useNotification } from "@/utils/common";
import { validateServiceAddress } from "@/utils/validate";
import {
  CheckCircleFilled,
  InfoCircleOutlined,
  MinusCircleOutlined,
  PlusCircleOutlined,
} from "@ant-design/icons-vue";
import type { FormInstance } from "ant-design-vue";
import { onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import { Generator } from "../../enum";
import type { ModelType } from "../../type";

const { t } = useI18n();
const { antNotification } = useNotification();

const props = defineProps({
  formData: {
    type: Object,
    default: () => ({}),
  },
  formType: {
    type: String,
    default: "create",
  },
});

const DEFAULT_PROTOCOL = "http://";
const host = window.location.hostname;

const formatUrl = (url?: string) => url?.replace(/^https?:\/\//, "") || "";

interface FormType {
  generator: GeneratorConfig[];
}

interface GeneratorConfig {
  generator_type: string;
  inference_type: string;
  vllm_endpoint?: string;
  ovms_endpoint?: string;
  prompt_path?: string;
  model: ModelType;
}

interface GeneratorState {
  protocol: string;
  isEndpointValid: boolean;
  isConnected: boolean;
  isEndpointTested: boolean;
  vllmModelList: string[];
  ovmsModelList: string[];
  localModelList: string[];
  deviceList: string[];
}

const formRef = ref<FormInstance>();
const generatorList = Generator;

const createDefaultGenerator = (data: any = {}): GeneratorConfig => {
  const {
    generator_type = "chatqna",
    inference_type = "vllm",
    vllm_endpoint = `${host}:8086`,
    ovms_endpoint = `${host}:8000`,
    model = {
      model_id: undefined,
      model_path: "",
      device: "AUTO",
    },
    prompt_path = "./default_prompt.txt",
  } = data;

  return {
    generator_type,
    inference_type,
    vllm_endpoint: formatUrl(vllm_endpoint || `${host}:8086`),
    ovms_endpoint: formatUrl(ovms_endpoint || `${host}:8000`),
    prompt_path,
    model,
  };
};

const initGenerators = (): GeneratorConfig[] => {
  const list = Array.isArray(props.formData?.generator)
    ? props.formData.generator
    : [];
  return list.length
    ? list.map((index) => createDefaultGenerator(index))
    : [createDefaultGenerator()];
};

const form = reactive<FormType>({
  generator: initGenerators(),
});

const getOptionIntroduction = (value: string) =>
  generatorList.find((item) => item.value === value)?.describe;

const createDefaultState = (
  endpoint?: string,
  connected = false,
): GeneratorState => ({
  protocol: DEFAULT_PROTOCOL,
  isEndpointValid: !!endpoint,
  isConnected: connected,
  isEndpointTested: false,
  vllmModelList: [],
  ovmsModelList: [],
  localModelList: [],
  deviceList: [],
});

const generatorStates = reactive<GeneratorState[]>([]);

const initStatesByForm = () => {
  generatorStates.splice(0);
  form.generator.forEach((item) => {
    const endpoint =
      item.inference_type === "ovms"
        ? item.ovms_endpoint
        : item.inference_type === "vllm"
          ? item.vllm_endpoint
          : undefined;
    generatorStates.push(createDefaultState(endpoint));
  });
};

initStatesByForm();

const rules: FormRules = reactive({
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
});

const resetGenerator = (index: number, resetEndpoint = false) => {
  Object.assign(form.generator[index].model, { model_id: undefined });
  const inferenceType = form.generator[index].inference_type;
  const endpoint =
    inferenceType === "ovms"
      ? form.generator[index].ovms_endpoint
      : inferenceType === "vllm"
        ? form.generator[index].vllm_endpoint
        : undefined;
  generatorStates[index] = createDefaultState(
    resetEndpoint ? undefined : endpoint,
  );
};

const handleInferenceTypeChange = (index: number) => resetGenerator(index);
const handleRemoteEndpointChange = (index: number) =>
  resetGenerator(index, true);

const isRemoteInference = (inferenceType: string) =>
  inferenceType === "vllm" || inferenceType === "ovms";

const getRemoteModelType = (inferenceType: string) =>
  inferenceType === "ovms" ? "OVMS" : "vLLM";

const getRemoteEndpointField = (inferenceType: string) =>
  inferenceType === "ovms" ? "ovms_endpoint" : "vllm_endpoint";

const getRemoteEndpointConfigKey = (inferenceType: string) =>
  inferenceType === "ovms"
    ? "pipeline.config.ovms_url"
    : "pipeline.config.vllm_url";

const getRemoteEndpointValidKey = (inferenceType: string) =>
  inferenceType === "ovms"
    ? "pipeline.valid.ovms_url"
    : "pipeline.valid.vllm_url";

const getRemoteModelTipKey = (inferenceType: string) =>
  inferenceType === "ovms"
    ? "pipeline.valid.ovmsModelTip"
    : "pipeline.valid.modelTip";

const getRemoteEndpointValue = (
  item: GeneratorConfig,
  inferenceType: string,
) => (inferenceType === "ovms" ? item.ovms_endpoint : item.vllm_endpoint);

const setRemoteEndpointValue = (
  item: GeneratorConfig,
  inferenceType: string,
  value: string,
) => {
  if (inferenceType === "ovms") {
    item.ovms_endpoint = value;
  } else {
    item.vllm_endpoint = value;
  }
};

const handleLocalModelChange = (index: number) => {
  // no-op: weight selection removed for local LLM
};

const handleLocalModelVisible = async (visible: boolean, index: number) => {
  if (visible) {
    try {
      const data: any = await getModelList("LLM");
      generatorStates[index].localModelList = data;
    } catch (err) {
      console.error(err);
    }
  }
};

const handleDeviceVisible = async (visible: boolean, index: number) => {
  if (visible) {
    try {
      const data: any = await getRunDevice();
      generatorStates[index].deviceList = data;
    } catch (err) {
      console.error(err);
    }
  }
};

const getRemoteEndpointRules = (
  index: number,
  inferenceType: string,
): FormRules => [
  {
    validator: (_: any, value: string) => {
      if (!value)
        return Promise.reject(
          t(
            inferenceType === "ovms"
              ? "pipeline.valid.ovmsUrlValid1"
              : "pipeline.valid.vllmUrlValid1",
          ),
        );
      if (!validateServiceAddress(generatorStates[index].protocol + value))
        return Promise.reject(
          t(
            inferenceType === "ovms"
              ? "pipeline.valid.ovmsUrlValid2"
              : "pipeline.valid.vllmUrlValid2",
          ),
        );
      generatorStates[index].isEndpointValid = true;
      return Promise.resolve();
    },
    trigger: ["change", "blur"],
    required: true,
  },
];

const handleQueryRemoteModels = async (
  index: number,
  inferenceType: string,
) => {
  const data: any = await getModelList(getRemoteModelType(inferenceType), {
    server_address:
      generatorStates[index].protocol +
      (inferenceType === "ovms"
        ? form.generator[index].ovms_endpoint
        : form.generator[index].vllm_endpoint),
  });
  if (inferenceType === "ovms") {
    generatorStates[index].ovmsModelList = data || [];
  } else {
    generatorStates[index].vllmModelList = data || [];
  }
  generatorStates[index].isConnected = !!data?.length;
};

const handleTestRemoteEndpoint = async (
  index: number,
  inferenceType: string,
) => {
  const requestUrl = inferenceType === "ovms" ? requestUrlOvms : requestUrlVllm;
  const endpoint =
    inferenceType === "ovms"
      ? form.generator[index].ovms_endpoint
      : form.generator[index].vllm_endpoint;
  try {
    const res: any = await requestUrl({
      server_address: generatorStates[index].protocol + endpoint,
      model_name: form.generator[index].model.model_id,
    });

    const statusValue = res?.status ?? res?.code ?? res?.data?.status;
    const isSuccess =
      statusValue === 200 ||
      statusValue === "200" ||
      statusValue === true ||
      statusValue === "ok" ||
      statusValue === "OK";

    generatorStates[index].isEndpointTested = isSuccess;

    if (isSuccess) {
      generatorStates[index].isConnected = true;
    } else {
      antNotification(
        "warning",
        t("common.prompt"),
        res?.message || t("pipeline.valid.remoteUrlValid5"),
      );
    }
  } catch (err) {
    generatorStates[index].isEndpointTested = false;
    throw err;
  }
};

const handleRemoteModelChange = (index: number) => {
  generatorStates[index].isEndpointTested = false;
};

const getRemoteModelList = (index: number, inferenceType: string) =>
  inferenceType === "ovms"
    ? generatorStates[index].ovmsModelList
    : generatorStates[index].vllmModelList;

const handleRemoteModelVisible = (
  visible: boolean,
  index: number,
  inferenceType: string,
) => {
  if (visible) {
    try {
      if (!generatorStates[index].isConnected) {
        antNotification(
          "warning",
          t("common.prompt"),
          t(getRemoteModelTipKey(inferenceType)),
        );
        return;
      }
      handleQueryRemoteModels(index, inferenceType);
    } catch (err) {
      console.error(err);
    }
  }
};

const getSelectedTypes = () =>
  form.generator.map((item) => item.generator_type);

const isGeneratorTypeDisabled = (value: string, index: number) =>
  getSelectedTypes().includes(value) &&
  form.generator[index].generator_type !== value;

const showAddIcon = () =>
  generatorList.some((item) => !getSelectedTypes().includes(item.value));

const handleAdd = () => {
  const type = generatorList.find(
    (item) => !getSelectedTypes().includes(item.value),
  );
  if (!type) return;
  const item = createDefaultGenerator({ generator_type: type.value });
  form.generator.push(item);
  generatorStates.push(createDefaultState(item.vllm_endpoint));
};

const handleDelete = (index: number) => {
  form.generator.splice(index, 1);
  generatorStates.splice(index, 1);
};

const hasUntestedVllmEndpoint = computed(() => {
  return form.generator.some((gen, index) => {
    const state = generatorStates[index];
    return isRemoteInference(gen.inference_type) && !state.isEndpointTested;
  });
});

const isProceed = computed(() => !hasUntestedVllmEndpoint.value);
// Format parameter
const formatFormParam = () => {
  const { generator } = form;
  return generator.map((item, index) => {
    const { inference_type, vllm_endpoint, ovms_endpoint, model, ...params } =
      item;
    const { model_id } = model;
    const localModel = {
      model_id,
      model_path: model_id || "",
      device: model.device,
    };
    return {
      ...params,
      inference_type,
      model: isRemoteInference(inference_type) ? { model_id } : localModel,
      vllm_endpoint:
        inference_type === "vllm"
          ? generatorStates[index].protocol + vllm_endpoint
          : undefined,
      ovms_endpoint:
        inference_type === "ovms"
          ? generatorStates[index].protocol + ovms_endpoint
          : undefined,
    };
  });
};

// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        if (hasUntestedVllmEndpoint.value) {
          antNotification(
            "warning",
            t("common.prompt"),
            t("pipeline.valid.remoteUrlValid5"),
          );
          resolve({ result: false });
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
  isProceed,
});

onMounted(async () => {
  for (let index = 0; index < form.generator.length; index++) {
    const item = form.generator[index];
    if (isRemoteInference(item.inference_type)) {
      formRef.value?.validateFields([
        ["generator", index, getRemoteEndpointField(item.inference_type)],
      ]);
      if (props.formType !== "update") return;
      if (item.model?.model_id) {
        generatorStates[index] = {
          ...generatorStates[index],
          isEndpointValid: true,
          isConnected: true,
          isEndpointTested: true,
        };
      }
    }
  }
});
</script>

<style scoped lang="less">
.form-wrap {
  max-height: 500px;
  overflow-y: auto;
}
.generator-wrap {
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
:deep(.intel-input-group) {
  .intel-input-group-addon {
    overflow: hidden;
    .intel-select-selector {
      border: 1px solid transparent !important;
    }
  }
}
.model-wrap {
  flex: 1;
  .flex-left;
  :deep(.intel-select-selector) {
    border-radius: 6px 0 0 6px;
  }
  .select-wrap {
    width: calc(100% - 72px);
  }
  .text-btn {
    margin: 0;
  }
}
.text-btn {
  width: 72px;
  height: 30px;
  margin: 0 -11px;
  border-radius: 0 6px 6px 0;
  padding: 0;
  .vertical-center;
}
</style>
