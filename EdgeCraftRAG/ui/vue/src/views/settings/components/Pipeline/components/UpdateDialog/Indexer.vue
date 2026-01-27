<template>
  <a-form
    :model="form"
    :rules="rules"
    name="indexer"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <div class="column-wrap">
      <a-form-item :label="$t('pipeline.config.indexerType')" class="row-item" name="indexer_type">
        <div class="flex-left">
          <a-select
            showSearch
            v-model:value="form.indexer_type"
            :placeholder="$t('pipeline.valid.indexerType')"
            @change="handleTypeChange"
          >
            <a-select-option v-for="item in indexerList" :key="item.value" :value="item.value">
              {{ item.name }}
            </a-select-option>
          </a-select>
          <FormTooltip :title="$t('pipeline.desc.indexerType')" />
        </div>

        <div class="option-introduction">
          <InfoCircleOutlined />
          {{ $t(optionIntroduction!) }}
        </div>
      </a-form-item>
    </div>
    <a-form-item
      v-if="!isKbadmin"
      :label="$t('pipeline.config.embeddingType')"
      name="inference_type"
    >
      <a-radio-group v-model:value="form.inference_type" @change="handleInferenceTypeChange">
        <a-radio value="vllm">{{ $t("pipeline.config.vllm") }}</a-radio>
        <a-radio value="local">{{ $t("pipeline.config.local") }}</a-radio>
      </a-radio-group>
    </a-form-item>
    <a-form-item name="embedding_url" :rules="rules.embedding_url" v-if="isKbadmin">
      <template #label>
        {{ $t("pipeline.config.embeddingUrl") }}
        <span class="eg-wrap">
          {{ $t("pipeline.valid.embeddingUrl") }}
        </span>
      </template>
      <a-input v-model:value="form.embedding_url" :placeholder="$t('pipeline.valid.embeddingUrl')">
        <template #addonBefore>
          <a-select v-model:value="modelProtocol">
            <a-select-option value="http://">Http://</a-select-option>
            <a-select-option value="https://">Https://</a-select-option>
          </a-select>
        </template>
      </a-input>
      <FormTooltip :title="$t('pipeline.desc.embeddingUrl')" />
    </a-form-item>
    <template v-if="isVllm">
      <a-form-item :name="['embedding_model', 'api_base']" :rules="rules.embedding_url">
        <template #label>
          {{ $t("pipeline.config.embeddingUrl") }}
          <span class="eg-wrap">
            {{ $t("pipeline.valid.embeddingvllmUrl") }}
          </span>
        </template>
        <a-input
          v-model:value="form.embedding_model.api_base"
          :placeholder="$t('pipeline.valid.embeddingvllmUrl')"
          @change="handleUrlChange"
        >
          <template #addonBefore>
            <a-select v-model:value="modelProtocol">
              <a-select-option value="http://">Http://</a-select-option>
              <a-select-option value="https://">Https://</a-select-option>
            </a-select>
          </template>
          <template #addonAfter>
            <a-button
              type="primary"
              class="text-btn"
              :disabled="!isModelUrlPass"
              @click="handleQueryModel"
            >
              <CheckCircleFilled
                v-if="isConnected"
                :style="{ color: 'var(--color-success)', fontSize: '18px' }"
              />
              <span v-else>{{ $t("common.connect") }}</span>
            </a-button>
          </template>
        </a-input>
        <FormTooltip :title="$t('pipeline.desc.embeddingUrl')" />
      </a-form-item>
      <a-form-item
        :label="$t('pipeline.config.embedding')"
        :name="['embedding_model', 'model_id']"
        :rules="rules.model_id"
      >
        <div class="model-wrap">
          <a-select
            showSearch
            v-model:value="form.embedding_model.model_id"
            :placeholder="$t('pipeline.valid.embedding')"
            @change="handleEmbeddingModelChange"
            @dropdownVisibleChange="handleEmbeddingModelVisible"
            class="select-wrap"
          >
            <a-select-option v-for="item in vllmModelList" :key="item" :value="item">
              {{ item }}
            </a-select-option>
          </a-select>
          <a-button
            type="primary"
            class="text-btn"
            :disabled="!form.embedding_model.model_id"
            @click="handleTestModelUrl"
            enter-button
          >
            <CheckCircleFilled
              v-if="vllmValidatePass"
              :style="{ color: 'var(--color-success)', fontSize: '18px' }"
            />
            <span v-else>{{ $t("pipeline.desc.test") }}</span>
          </a-button>
        </div>
        <FormTooltip :title="$t('pipeline.desc.embedding')" /> </a-form-item
    ></template>
    <template v-else>
      <a-form-item
        :label="$t('pipeline.config.embedding')"
        :name="['embedding_model', 'model_id']"
        :rules="rules.model_id"
      >
        <a-select
          showSearch
          v-model:value="form.embedding_model.model_id"
          :placeholder="$t('pipeline.valid.embedding')"
          @change="handleModelChange"
          @dropdownVisibleChange="handleModelVisible"
        >
          <a-select-option v-for="item in modelList" :key="item" :value="item">
            {{ item }}
          </a-select-option>
        </a-select>

        <FormTooltip :title="$t('pipeline.desc.embedding')" />
      </a-form-item>
      <a-form-item
        v-if="!isKbadmin"
        :label="$t('pipeline.config.embeddingDevice')"
        :name="['embedding_model', 'device']"
        :rules="rules.device"
      >
        <a-select
          showSearch
          v-model:value="form.embedding_model.device"
          :placeholder="$t('pipeline.valid.embeddingDevice')"
          @dropdownVisibleChange="handleDeviceVisible"
        >
          <a-select-option v-for="item in deviceList" :key="item" :value="item">
            {{ item }}
          </a-select-option>
        </a-select>
        <FormTooltip :title="$t('pipeline.desc.embeddingDevice')" />
      </a-form-item>
    </template>
    <a-form-item name="vector_url" :rules="rules.vector_url" v-if="isMilvus || isKbadmin">
      <template #label>
        {{ $t("pipeline.config.vector_url") }}
        <span class="eg-wrap">
          {{ $t(`${TIP_MESSAGES[form.indexer_type]}`) }}
        </span>
      </template>
      <a-input
        v-model:value="form.vector_url"
        :placeholder="$t(`${TIP_MESSAGES[form.indexer_type]}`)"
        @change="handleUriChange"
      >
        <template #addonBefore>
          <a-select v-model:value="protocol">
            <a-select-option value="http://">Http://</a-select-option>
            <a-select-option value="https://">Https://</a-select-option>
          </a-select>
        </template>
        <template #addonAfter v-if="isMilvus">
          <a-button
            type="primary"
            class="text-btn"
            :disabled="!isVectorUrlPass"
            @click="handleTestUrl"
          >
            <CheckCircleFilled
              v-if="validatePass"
              :style="{ color: 'var(--color-success)', fontSize: '18px' }"
            />
            <span v-else>{{ $t("pipeline.desc.test") }}</span>
          </a-button>
        </template>
      </a-input>
      <FormTooltip :title="$t('pipeline.desc.vector_url')" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Indexer">
  import { getModelList, getRunDevice, requestUrlVerify, requestUrlVllm } from "@/api/pipeline";
  import { useNotification } from "@/utils/common";
  import { validateServiceAddress } from "@/utils/validate.ts";
  import { CheckCircleFilled, InfoCircleOutlined } from "@ant-design/icons-vue";
  import type { FormInstance, RadioChangeEvent } from "ant-design-vue";
  import { RuleObject } from "ant-design-vue/es/form/interface";
  import { SelectValue } from "ant-design-vue/es/select/index";
  import { computed, onMounted, reactive, ref } from "vue";
  import { useI18n } from "vue-i18n";
  import { Indexer } from "../../enum.ts";
  import { ModelType } from "../../type.ts";

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

  interface FormType {
    indexer_type: string;
    inference_type: string;
    vector_url?: string;
    embedding_url?: string;
    embedding_model: ModelType;
  }

  const TIP_MESSAGES = {
    kbadmin_indexer: "pipeline.valid.kb_vector_url",
    milvus_vector: "pipeline.valid.vector_url",
  } as any;

  const host = window.location.hostname;
  const { parser_type = "" } = props.formData?.node_parser || {};
  const {
    indexer_type = "faiss_vector",
    inference_type = "local",
    vector_url = "",
    embedding_url = `${host}:13020`,
    embedding_model = {
      api_base: `${host}:8087`,
      model_id: undefined,
      model_path: "",
      device: "AUTO",
      weight: "INT4",
    },
  } = props.formData?.indexer || {};

  const formRef = ref<FormInstance>();
  const protocol = ref<string>("http://");
  const modelProtocol = ref<string>("http://");

  const isVectorUrlPass = ref<boolean>(false);
  const isModelUrlPass = ref<boolean>(false);
  const validatePass = ref<boolean>(false);
  const vllmValidatePass = ref<boolean>(false);
  const isConnected = ref<boolean>(false);

  const deviceList = ref<EmptyArrayType>([]);
  const modelList = ref<EmptyArrayType>([]);
  const vllmModelList = ref<EmptyArrayType>([]);

  const handleUrlFormat = (url: string) => {
    return url ? url.replace(/https?:\/\//g, "") : "";
  };

  const initialFormData: FormType = {
    indexer_type,
    inference_type,
    vector_url: vector_url
      ? handleUrlFormat(vector_url)
      : `${host}:${indexer_type === "kbadmin_indexer" ? "29530" : "19530"}`,
    embedding_url: handleUrlFormat(embedding_url),
    embedding_model: {
      ...embedding_model,
      api_base: handleUrlFormat(embedding_model.api_base),
      model_id:
        props.formType === "update"
          ? embedding_model?.model_id
          : indexer_type === "kbadmin_indexer"
          ? undefined
          : embedding_model?.model_id,
    },
  };

  const form = reactive<FormType>(initialFormData);

  const isCreate = computed(() => props.formType === "create");
  const isKbadmin = computed(() => form.indexer_type === "kbadmin_indexer");
  const isMilvus = computed(() => form.indexer_type === "milvus_vector");
  const isVllm = computed(() => form.inference_type === "vllm");

  const indexerList = computed(() => {
    if (isCreate.value) return Indexer;
    return Indexer.filter(item =>
      isKbadmin.value ? item.value === "kbadmin_indexer" : item.value !== "kbadmin_indexer"
    );
  });

  const optionIntroduction = computed(() => {
    return Indexer.find(item => item.value === form.indexer_type)?.describe;
  });

  const validateIndeserType = async (_rule: RuleObject, value: string) => {
    if (!value) {
      return Promise.reject(t("pipeline.valid.indexerType"));
    }

    if (parser_type === "kbadmin_parser" && value !== "kbadmin_indexer") {
      return Promise.reject(t("pipeline.valid.indexerTypeValid1"));
    }

    return Promise.resolve();
  };

  const validateUnique = (urlType: "vector" | "model") => {
    const messages = {
      vector: {
        required: "pipeline.valid.urlValid1",
        format: "pipeline.valid.urlValid2",
      },
      model: {
        required: "pipeline.valid.modelRequired",
        format: "pipeline.valid.modelFormat",
      },
    }[urlType];

    return async (_rule: RuleObject, value: string) => {
      if (!value) {
        return Promise.reject(new Error(t(messages.required)));
      }

      const serverUrl = (urlType === "vector" ? protocol.value : modelProtocol.value) + value;
      if (!validateServiceAddress(serverUrl)) {
        return Promise.reject(new Error(t(messages.format)));
      }

      if (urlType === "model") {
        isModelUrlPass.value = true;
      } else {
        isVectorUrlPass.value = true;
      }

      return Promise.resolve();
    };
  };

  const rules: FormRules = reactive({
    indexer_type: [
      {
        required: true,
        validator: validateIndeserType,
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
        message: t("pipeline.valid.embedding"),
        trigger: "change",
      },
    ],
    device: [
      {
        required: true,
        message: t("pipeline.valid.embeddingDevice"),
        trigger: "change",
      },
    ],
    vector_url: [
      {
        required: true,
        validator: validateUnique("vector"),
        trigger: "blur",
      },
    ],
    embedding_url: [
      {
        required: true,
        validator: validateUnique("model"),
        trigger: "change",
      },
    ],
  });

  const queryModelList = async (modelType: string, params?: any) => {
    try {
      const data = await getModelList(modelType, params);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error(`Failed to load ${modelType} model list:`, error);
      return [];
    }
  };

  const handleTypeChange = (value: SelectValue) => {
    isVectorUrlPass.value = false;
    validatePass.value = false;
    isConnected.value = false;
    isModelUrlPass.value = false;
    vllmValidatePass.value = false;

    if (isCreate.value) {
      form.embedding_model.model_id = undefined;
      form.embedding_model.model_path = "";
    }
    if (value === "kbadmin_indexer") {
      form.inference_type = "local";
      form.vector_url = `${host}:${value === "kbadmin_indexer" ? "29530" : "19530"}`;
      antNotification("warning", t("common.prompt"), t("pipeline.valid.indexerTypeTip"));
    } else {
      form.inference_type = "vllm";
      form.embedding_model.api_base = `${host}:8087`;
      nextTick(() => {
        formRef.value?.validateFields([["embedding_model", "api_base"]]);
        formRef.value?.validateFields([["vector_url"]]);
      });
    }
  };

  const handleInferenceTypeChange = (e: RadioChangeEvent) => {
    form.embedding_model.model_id = undefined;
    form.embedding_model.weight = undefined;

    if (e.target?.value === "vllm") {
      nextTick(() => formRef.value?.validateFields([["embedding_model", "api_base"]]));
    }
  };

  const handleUrlChange = () => {
    isModelUrlPass.value = false;
    vllmValidatePass.value = false;
    isConnected.value = false;
    form.embedding_model.model_id = undefined;
    vllmModelList.value = [];
  };

  const handleUriChange = () => {
    isVectorUrlPass.value = false;
    validatePass.value = false;
  };

  const handleEmbeddingModelChange = () => {
    vllmValidatePass.value = false;
  };

  const handleModelChange = (value: SelectValue) => {
    form.embedding_model.model_path = `./models/${value}`;
  };

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
  const handleModelVisible = async (visible: boolean) => {
    if (visible) {
      const modelType = isKbadmin.value ? "kbadmin_embedding_model" : "embedding";
      modelList.value = await queryModelList(modelType);
    }
  };

  const handleEmbeddingModelVisible = async (visible: boolean) => {
    if (visible && !isConnected.value) {
      antNotification("warning", t("common.prompt"), t("pipeline.valid.modelTip"));
    }
  };

  const handleQueryModel = async () => {
    try {
      const server_address = protocol.value + form.embedding_model.api_base;
      const data: any = await queryModelList("vLLM_embedding", { server_address });
      vllmModelList.value = [].concat(data);
      isConnected.value = vllmModelList.value.length > 0;

      if (!isCreate.value) return;

      if (isConnected.value) {
        antNotification("success", t("common.success"), t("request.pipeline.connectSucc"));
      } else {
        antNotification("warning", t("common.prompt"), t("request.pipeline.connectError"));
      }
    } catch (error) {
      console.error("Failed to query model:", error);
    }
  };

  const handleTestModelUrl = async () => {
    const { model_id, api_base } = form.embedding_model;
    if (!model_id) return;

    try {
      const server_address = protocol.value + api_base;
      const response: any = await requestUrlVllm({
        server_address,
        model_name: model_id,
      });

      if (response?.status === "200") {
        vllmValidatePass.value = true;
        antNotification("success", t("common.success"), t("pipeline.valid.vllmUrlValid4"));
      } else {
        antNotification("error", t("common.error"), t("pipeline.valid.vllmUrlValid3"));
      }
    } catch (error) {
      console.error("Failed to test model URL:", error);
      antNotification("error", t("common.error"), t("pipeline.valid.vllmUrlValid3"));
    }
  };

  const handleTestUrl = async () => {
    try {
      const vector_url = protocol.value + form.vector_url;
      const response: any = await requestUrlVerify({ vector_url });

      if (response?.status === "200") {
        validatePass.value = true;
        antNotification("success", t("common.success"), t("pipeline.valid.urlValid4"));
      } else {
        antNotification("error", t("common.error"), t("pipeline.valid.urlValid3"));
      }
    } catch (error) {
      console.error("Failed to test URL:", error);
      antNotification("error", t("common.error"), t("pipeline.valid.urlValid3"));
    }
  };

  const formatFormParam = () => {
    const { indexer_type, inference_type, vector_url, embedding_url, embedding_model } = form;

    return {
      indexer_type,
      inference_type,
      embedding_model: {
        ...embedding_model,
        api_base: isVllm.value ? modelProtocol.value + embedding_model.api_base : undefined,
      },
      vector_url: isMilvus.value || isKbadmin.value ? protocol.value + vector_url : undefined,
      embedding_url: isKbadmin.value ? modelProtocol.value + embedding_url : undefined,
    };
  };
  const generateFormData = () => {
    const baseData = { indexer: formatFormParam() };
    const { retriever = {} } = props.formData || {};

    if (isKbadmin.value && parser_type !== "kbadmin_parser") {
      return {
        ...baseData,
        node_parser: { parser_type: "kbadmin_parser" },
        retriever: { ...retriever, retriever_type: "kbadmin_retriever" },
      };
    }

    return baseData;
  };

  const handleValidate = (): Promise<object> => {
    return new Promise(resolve => {
      formRef.value
        ?.validate()
        .then(() => {
          if (isMilvus.value && !validatePass.value) {
            antNotification("warning", t("common.prompt"), t("pipeline.valid.urlValid5"));
            return;
          } else if (isVllm.value && !vllmValidatePass.value) {
            antNotification("warning", t("common.prompt"), t("pipeline.valid.vllmUrlValid5"));
            return;
          }
          resolve({
            result: true,
            data: generateFormData(),
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
      if (isMilvus.value) {
        isVectorUrlPass.value = validatePass.value = true;
        isConnected.value = true;
      }

      if (isVllm.value) {
        isConnected.value = true;
        isModelUrlPass.value = vllmValidatePass.value = true;
        handleQueryModel();
      }
    } else {
      if (form.vector_url) formRef.value?.validateFields([["vector_url"]]);
      if (form.embedding_model.api_base)
        formRef.value?.validateFields([["embedding_model", "api_base"]]);
      if (form.embedding_url) formRef.value?.validateFields([["embedding_url"]]);
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
