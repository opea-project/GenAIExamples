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
    <div class="column-wrap">
      <a-form-item :label="$t('pipeline.config.generatorType')" name="generator_type">
        <div class="flex-left">
          <a-select
            showSearch
            v-model:value="form.generator_type"
            :placeholder="$t('pipeline.valid.generatorType')"
          >
            <a-select-option v-for="item in generatorList" :key="item.value" :value="item.value">{{
              item.name
            }}</a-select-option>
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.generatorType')" />
        </div>
        <div class="option-introduction">
          <InfoCircleOutlined />
          {{ $t(optionIntroduction!) }}
        </div>
      </a-form-item>
    </div>
    <a-form-item :label="$t('pipeline.config.llm')" name="inference_type">
      <a-radio-group v-model:value="form.inference_type" @change="handleTypeChange">
        <a-radio value="vllm">{{ $t("pipeline.config.vllm") }}</a-radio>
        <a-radio value="local">{{ $t("pipeline.config.local") }}</a-radio>
      </a-radio-group>
    </a-form-item>
    <template v-if="isVllm">
      <a-form-item name="vllm_endpoint" :rules="rules.vllm_endpoint">
        <template #label>
          {{ $t("pipeline.config.vllm_url") }}
          <span class="eg-wrap"> {{ $t("pipeline.valid.vllm_url") }}</span>
        </template>
        <a-input
          v-model:value="form.vllm_endpoint"
          :placeholder="$t('pipeline.valid.vllm_url')"
          @change="handleUrlChange"
        >
          <template #addonBefore>
            <a-select v-model:value="protocol">
              <a-select-option value="http://">Http://</a-select-option>
              <a-select-option value="https://">Https://</a-select-option>
            </a-select>
          </template>
          <template #addonAfter>
            <a-button
              type="primary"
              class="text-btn"
              :disabled="!isPass"
              @click.stop="handleQueryVllmModel"
            >
              <CheckCircleFilled
                v-if="isConnected"
                :style="{ color: 'var(--color-success)', fontSize: '18px' }"
              />
              <span v-else> {{ $t("common.connect") }}</span>
            </a-button>
          </template>
        </a-input>
        <FormTooltip :title="$t('pipeline.desc.vllm_url')" />
      </a-form-item>
      <a-form-item
        :label="$t('pipeline.config.language')"
        :name="['model', 'model_id']"
        :rules="rules.model_id"
      >
        <div class="model-wrap">
          <a-select
            v-model:value="form.model.model_id"
            :placeholder="$t('pipeline.valid.language')"
            @dropdownVisibleChange="handleVllmModelVisible"
            allowClear
            showSearch
            class="select-wrap"
          >
            <a-select-option v-for="item in vllmModelList" :key="item" :value="item">{{
              item
            }}</a-select-option>
          </a-select>
          <a-button
            type="primary"
            class="text-btn"
            :disabled="!form.model.model_id"
            @click="handleTestUrl"
            enter-button
          >
            <CheckCircleFilled
              v-if="validatePass"
              :style="{ color: 'var(--color-success)', fontSize: '18px' }"
            />
            <span v-else> {{ $t("pipeline.desc.test") }}</span>
          </a-button>
        </div>
        <FormTooltip :title="$t('pipeline.desc.language')" />
      </a-form-item>
    </template>
    <template v-else>
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
          <a-select-option v-for="item in modelList" :key="item" :value="item">{{
            item
          }}</a-select-option>
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
          <a-select-option v-for="item in deviceList" :key="item" :value="item">{{
            item
          }}</a-select-option>
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
          <a-select-option v-for="item in generatorWeightList" :key="item" :value="item">{{
            item
          }}</a-select-option>
        </a-select>
        <FormTooltip :title="t('pipeline.desc.weights')" />
      </a-form-item>
    </template>
  </a-form>
</template>

<script lang="ts" setup name="Generator">
  import { getModelList, getModelWeight, getRunDevice, requestUrlVllm } from "@/api/pipeline";
  import { useNotification } from "@/utils/common";
  import { validateServiceAddress } from "@/utils/validate.ts";
  import { CheckCircleFilled, InfoCircleOutlined } from "@ant-design/icons-vue";
  import type { FormInstance } from "ant-design-vue";
  import { onMounted, reactive, ref } from "vue";
  import { useI18n } from "vue-i18n";
  import { Generator } from "../../enum.ts";
  import { ModelType } from "../../type.ts";

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
  }
  const host = window.location.hostname;
  const validateUnique = async (rule: any, value: string) => {
    if (!value) {
      return Promise.reject(t("pipeline.valid.vllmUrlValid1"));
    }
    const serverUrl = protocol.value + value;
    if (!validateServiceAddress(serverUrl)) {
      return Promise.reject(t("pipeline.valid.vllmUrlValid2"));
    }

    isPass.value = true;
    return Promise.resolve();
  };
  const handleUrlFormat = (url: string) => {
    if (!url) return "";
    return url.replace(/https?:\/\//g, "");
  };
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
  } = props.formData?.generator || {};

  const isPass = ref<boolean>(false);
  const validatePass = ref<boolean>(false);
  const isConnected = ref<boolean>(false);

  const protocol = ref<string>("http://");
  const formRef = ref<FormInstance>();
  const form = reactive<FormType>({
    generator_type,
    inference_type,
    vllm_endpoint: handleUrlFormat(vllm_endpoint),
    model,
  });
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
    vllm_endpoint: [
      {
        required: true,
        validator: validateUnique,
        trigger: "blur",
      },
    ],
  });
  const generatorList = Generator;
  const generatorWeightList = ref<EmptyArrayType>([]);
  const modelList = ref<EmptyArrayType>([]);
  const vllmModelList = ref<EmptyArrayType>([]);
  const deviceList = ref<EmptyArrayType>([]);

  const isVllm = computed(() => {
    return form.inference_type === "vllm";
  });
  const isCreate = computed(() => props.formType === "create");
  const optionIntroduction = computed(() => {
    return Generator.find(item => item.value === form.generator_type)?.describe;
  });
  // Complete model_cath
  const handleModelChange = () => {
    form.model.weight = undefined;
  };
  // Reset  model_ID
  const handleTypeChange = () => {
    form.model.model_id = undefined;
    form.model.weight = undefined;
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

  const handleQueryVllmModel = async () => {
    try {
      const server_address = protocol.value + form.vllm_endpoint;
      const data: any = await getModelList("vLLM", {
        server_address,
      });
      vllmModelList.value = [].concat(data);
      isConnected.value = vllmModelList.value.length > 0;

      if (!isCreate.value) return;

      if (isConnected.value) {
        antNotification("success", t("common.success"), t("request.pipeline.connectSucc"));
      } else {
        antNotification("warning", t("common.prompt"), t("request.pipeline.connectError"));
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Handling Model Folding Events
  const handleVllmModelVisible = async (visible: boolean) => {
    if (visible) {
      if (!isConnected.value) {
        antNotification("warning", t("common.prompt"), t("pipeline.valid.modelTip"));
        return;
      }
    }
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
        const data: any = await getModelWeight(model_id!);
        generatorWeightList.value = [].concat(data);
      } catch (err) {
        console.error(err);
      }
    }
  };
  const handleUrlChange = () => {
    isPass.value = false;
    validatePass.value = false;
    isConnected.value = false;
    form.model.model_id = undefined;
    vllmModelList.value = [];
  };
  // Format parameter
  const formatFormParam = () => {
    const { generator_type, inference_type, model, vllm_endpoint } = form;
    const { model_id, weight } = model;
    model.model_path = handleModelPath(model_id!, weight);
    return {
      generator_type,
      inference_type,
      prompt_path: "./default_prompt.txt",
      model: isVllm.value ? { model_id } : model,
      vllm_endpoint: isVllm.value ? protocol.value + vllm_endpoint : undefined,
    };
  };

  const handleTestUrl = async () => {
    const { model_id } = form.model;
    if (!model_id) return;
    const server_address = protocol.value + form.vllm_endpoint;

    const { status = "" } = (await requestUrlVllm({
      server_address,
      model_name: model_id,
    })) as any;
    if (status !== "200") {
      antNotification("error", t("common.error"), t("pipeline.valid.vllmUrlValid3"));
      return;
    }
    validatePass.value = true;
    antNotification("success", t("common.success"), t("pipeline.valid.vllmUrlValid4"));
  };
  // Validate the form, throw results form
  const handleValidate = (): Promise<object> => {
    return new Promise(resolve => {
      formRef.value
        ?.validate()
        .then(() => {
          if (isVllm.value && !validatePass.value) {
            antNotification("warning", t("common.prompt"), t("pipeline.valid.vllmUrlValid5"));
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
    if (props.formType === "update" && isVllm.value) {
      isConnected.value = true;
      isPass.value = validatePass.value = true;
      handleQueryVllmModel();
    } else if (form.vllm_endpoint) {
      formRef.value?.validateFields([["vllm_endpoint"]]);
    }
  });
</script>

<style scoped lang="less">
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
