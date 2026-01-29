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
    <div class="generator-wrap" v-for="(item, index) in form.generator" :key="`generator-${index}`">
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
          <a-radio value="local">{{ $t("pipeline.config.local") }}</a-radio>
        </a-radio-group>
      </a-form-item>
      <!-- vLLM -->
      <template v-if="item.inference_type === 'vllm'">
        <a-form-item
          :name="['generator', index, 'vllm_endpoint']"
          :rules="getVllmEndpointRules(index)"
        >
          <template #label>
            {{ $t("pipeline.config.vllm_url") }}
            <span class="eg-wrap">{{ $t("pipeline.valid.vllm_url") }}</span>
          </template>

          <a-input
            v-model:value="item.vllm_endpoint"
            :placeholder="$t('pipeline.valid.vllm_url')"
            @change="() => handleVllmEndpointChange(index)"
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
                @click="handleQueryVllmModels(index)"
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
              @change="() => handleVllmModeChange(index)"
              @dropdownVisibleChange="v => handleVllmModelVisible(v, index)"
            >
              <a-select-option
                v-for="item in generatorStates[index].vllmModelList"
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
              @click="handleTestVllmEndpoint(index)"
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
            @dropdownVisibleChange="value => handleLocalModelVisible(value, index)"
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
            @dropdownVisibleChange="value => handleDeviceVisible(value, index)"
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

        <a-form-item
          :label="$t('pipeline.config.weights')"
          :name="['generator', index, 'model', 'weight']"
          :rules="rules.weight"
        >
          <a-select
            v-model:value="item.model.weight"
            showSearch
            :placeholder="$t('pipeline.valid.weights')"
            @dropdownVisibleChange="value => handleWeightVisible(value, index)"
          >
            <a-select-option
              v-for="item in generatorStates[index].weightList"
              :key="item"
              :value="item"
            >
              {{ item }}
            </a-select-option>
          </a-select>
          <FormTooltip :title="t('pipeline.desc.weights')" />
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
  import { getModelList, getModelWeight, getRunDevice, requestUrlVllm } from "@/api/pipeline";
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
    prompt_path?: string;
    model: ModelType;
  }

  interface GeneratorState {
    protocol: string;
    isEndpointValid: boolean;
    isConnected: boolean;
    isEndpointTested: boolean;
    vllmModelList: string[];
    localModelList: string[];
    deviceList: string[];
    weightList: string[];
  }

  const formRef = ref<FormInstance>();
  const generatorList = Generator;

  const createDefaultGenerator = (data: any = {}): GeneratorConfig => {
    const {
      generator_type = "chatqna",
      inference_type = "vllm",
      vllm_endpoint = `${host}:8086`,
      model = {
        model_id: undefined,
        model_path: "",
        device: "AUTO",
        weight: undefined,
      },
      prompt_path = "./default_prompt.txt",
    } = data;

    return {
      generator_type,
      inference_type,
      vllm_endpoint: formatUrl(vllm_endpoint || `${host}:8086`),
      prompt_path,
      model,
    };
  };

  const initGenerators = (): GeneratorConfig[] => {
    const list = Array.isArray(props.formData?.generator) ? props.formData.generator : [];
    return list.length
      ? list.map(index => createDefaultGenerator(index))
      : [createDefaultGenerator()];
  };

  const form = reactive<FormType>({
    generator: initGenerators(),
  });

  const getOptionIntroduction = (value: string) =>
    generatorList.find(item => item.value === value)?.describe;

  const createDefaultState = (endpoint?: string, connected = false): GeneratorState => ({
    protocol: DEFAULT_PROTOCOL,
    isEndpointValid: !!endpoint,
    isConnected: connected,
    isEndpointTested: false,
    vllmModelList: [],
    localModelList: [],
    deviceList: [],
    weightList: [],
  });

  const generatorStates = reactive<GeneratorState[]>([]);

  const initStatesByForm = () => {
    generatorStates.splice(0);
    form.generator.forEach(item => {
      generatorStates.push(createDefaultState(item.vllm_endpoint));
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
    weight: [
      {
        required: true,
        message: t("pipeline.valid.weights"),
        trigger: "change",
      },
    ],
  });

  const resetGenerator = (index: number, resetEndpoint = false) => {
    Object.assign(form.generator[index].model, { model_id: undefined, weight: undefined });
    generatorStates[index] = createDefaultState(
      resetEndpoint ? undefined : form.generator[index].vllm_endpoint
    );
  };

  const handleInferenceTypeChange = (index: number) => resetGenerator(index);
  const handleVllmEndpointChange = (index: number) => resetGenerator(index, true);

  const handleLocalModelChange = (index: number) => {
    form.generator[index].model.weight = undefined;
    generatorStates[index].weightList = [];
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

  const handleWeightVisible = async (visible: boolean, index: number) => {
    if (visible) {
      try {
        const data: any = await getModelWeight(form.generator[index].model.model_id!);
        generatorStates[index].weightList = data;
      } catch (err) {
        console.error(err);
      }
    }
  };

  const getVllmEndpointRules = (index: number): FormRules => [
    {
      validator: (_: any, value: string) => {
        if (!value) return Promise.reject(t("pipeline.valid.vllmUrlValid1"));
        if (!validateServiceAddress(generatorStates[index].protocol + value))
          return Promise.reject(t("pipeline.valid.vllmUrlValid2"));
        generatorStates[index].isEndpointValid = true;
        return Promise.resolve();
      },
      trigger: ["change", "blur"],
      required: true,
    },
  ];

  const handleQueryVllmModels = async (index: number) => {
    const data: any = await getModelList("vLLM", {
      server_address: generatorStates[index].protocol + form.generator[index].vllm_endpoint,
    });
    generatorStates[index].vllmModelList = data || [];
    generatorStates[index].isConnected = !!data?.length;
  };

  const handleTestVllmEndpoint = async (index: number) => {
    const res: any = await requestUrlVllm({
      server_address: generatorStates[index].protocol + form.generator[index].vllm_endpoint,
      model_name: form.generator[index].model.model_id,
    });
    generatorStates[index].isEndpointTested = res?.status === "200";
  };

  const handleVllmModeChange = (index: number) => {
    generatorStates[index].isEndpointTested = false;
  };

  const handleVllmModelVisible = (visible: boolean, index: number) => {
    if (visible) {
      try {
        if (!generatorStates[index].isConnected) {
          antNotification("warning", t("common.prompt"), t("pipeline.valid.modelTip"));
          return;
        }
        handleQueryVllmModels(index);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const getSelectedTypes = () => form.generator.map(item => item.generator_type);

  const isGeneratorTypeDisabled = (value: string, index: number) =>
    getSelectedTypes().includes(value) && form.generator[index].generator_type !== value;

  const showAddIcon = () => generatorList.some(item => !getSelectedTypes().includes(item.value));

  const handleAdd = () => {
    const type = generatorList.find(item => !getSelectedTypes().includes(item.value));
    if (!type) return;
    const item = createDefaultGenerator({ generator_type: type.value });
    form.generator.push(item);
    generatorStates.push(createDefaultState(item.vllm_endpoint));
  };

  const handleDelete = (index: number) => {
    form.generator.splice(index, 1);
    generatorStates.splice(index, 1);
  };

  const handleModelPath = (modelId: string, weights?: string, prefix: string = "./models/") => {
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

  const hasUntestedVllmEndpoint = computed(() => {
    return form.generator.some((gen, index) => {
      const state = generatorStates[index];
      return gen.inference_type === "vllm" && !state.isEndpointTested;
    });
  });

  const isProceed = computed(() => !hasUntestedVllmEndpoint.value);
  // Format parameter
  const formatFormParam = () => {
    const { generator } = form;
    return generator.map((item, index) => {
      const { inference_type, vllm_endpoint, model, ...params } = item;
      const { model_id, weight } = model;
      model.model_path = handleModelPath(model_id!, weight);
      return {
        ...params,
        inference_type,
        model: inference_type === "vllm" ? { model_id } : model,
        vllm_endpoint:
          inference_type === "vllm" ? generatorStates[index].protocol + vllm_endpoint : undefined,
      };
    });
  };

  // Validate the form, throw results form
  const handleValidate = (): Promise<object> => {
    return new Promise(resolve => {
      formRef.value
        ?.validate()
        .then(() => {
          if (hasUntestedVllmEndpoint.value) {
            antNotification("warning", t("common.prompt"), t("pipeline.valid.vllmUrlValid5"));
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
      if (item.inference_type === "vllm") {
        formRef.value?.validateFields([["generator", index, "vllm_endpoint"]]);
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
