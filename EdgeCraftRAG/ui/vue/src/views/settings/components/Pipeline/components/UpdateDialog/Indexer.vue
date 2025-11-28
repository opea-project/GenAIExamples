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
      <a-form-item
        :label="$t('pipeline.config.indexerType')"
        class="row-item"
        name="indexer_type"
      >
        <div class="flex-left">
          <a-select
            showSearch
            v-model:value="form.indexer_type"
            :placeholder="$t('pipeline.valid.indexerType')"
            @change="handleTypeChange"
          >
            <a-select-option
              v-for="item in indexerList"
              :key="item.value"
              :value="item.value"
              >{{ item.name }}</a-select-option
            >
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
        <a-select-option v-for="item in modelList" :key="item" :value="item">{{
          item
        }}</a-select-option>
      </a-select>
      <FormTooltip :title="$t('pipeline.desc.embedding')" />
    </a-form-item>
    <a-form-item
      name="embedding_url"
      :rules="rules.embedding_url"
      v-if="isKbadmin"
    >
      <template #label>
        {{ $t("pipeline.config.embeddingUrl") }}
        <span class="eg-wrap"> {{ $t("pipeline.valid.embeddingUrl") }}</span>
      </template>
      <a-input
        v-model:value="form.embedding_url"
        :placeholder="$t('pipeline.valid.embeddingUrl')"
      >
        <template #addonBefore>
          <a-select v-model:value="modelProtocol">
            <a-select-option value="http://">Http://</a-select-option>
            <a-select-option value="https://">Https://</a-select-option>
          </a-select>
        </template>
      </a-input>
      <FormTooltip :title="$t('pipeline.desc.embeddingUrl')" />
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
        <a-select-option v-for="item in deviceList" :key="item" :value="item">{{
          item
        }}</a-select-option>
      </a-select>
      <FormTooltip :title="$t('pipeline.desc.embeddingDevice')" />
    </a-form-item>
    <a-form-item
      name="vector_url"
      :rules="rules.vector_url"
      v-if="isMilvus || isKbadmin"
    >
      <template #label>
        {{ $t("pipeline.config.vector_url") }}
        <span class="eg-wrap">
          {{ $t(`${TIP_MESSAGES[form.indexer_type]}`) }}</span
        >
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
      <FormTooltip :title="$t('pipeline.desc.vector_url')" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Indexer">
import { getRunDevice, getModelList, requestUrlVerify } from "@/api/pipeline";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref, onMounted } from "vue";
import { Indexer } from "../../enum.ts";
import { ModelType } from "../../type.ts";
import { InfoCircleOutlined, CheckCircleFilled } from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";
import { validateServiceAddress } from "@/utils/validate.ts";
import { useNotification } from "@/utils/common";
import { SelectValue } from "ant-design-vue/es/select/index";
import { RuleObject } from "ant-design-vue/es/form/interface";

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
  indexer_type: string;
  vector_url?: string;
  embedding_url?: string;
  embedding_model: ModelType;
}

const host = window.location.hostname;
const {
  indexer_type = "faiss_vector",
  vector_url = "",
  embedding_url = `${host}:13020`,
  embedding_model = {
    model_id: "BAAI/bge-small-en-v1.5",
    model_path: "./models/BAAI/bge-small-en-v1.5",
    device: "AUTO",
    weight: "INT4",
  },
} = props.formData?.indexer || {};
const { parser_type = "" } = props.formData?.node_parser || {};
const TIP_MESSAGES = {
  kbadmin_indexer: "pipeline.valid.kb_vector_url",
  milvus_vector: "pipeline.valid.vector_url",
} as const;
const VALIDATION_MESSAGES = {
  vector: {
    required: "pipeline.valid.urlValid1",
    format: "pipeline.valid.urlValid2",
  },
  model: {
    required: "pipeline.valid.modelRequired",
    format: "pipeline.valid.modelFormat",
  },
} as const;
const validateUnique = (type: "vector" | "model") => {
  return async (rule: RuleObject, value: string) => {
    const messages = VALIDATION_MESSAGES[type];
    if (!value) {
      return Promise.reject(new Error(t(messages.required)));
    }
    const serverUrl = protocol.value + value;
    if (!validateServiceAddress(serverUrl)) {
      return Promise.reject(new Error(t(messages.format)));
    }
    isPass.value = true;
    return Promise.resolve();
  };
};

const validateIndeserType = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("pipeline.valid.indexerType"));
  }
  if (parser_type === "kbadmin_parser" && value !== "kbadmin_indexer") {
    return Promise.reject(t("pipeline.valid.indexerTypeValid1"));
  }
  return Promise.resolve();
};

const handleUrlFormat = (url: string) => {
  if (!url) return "";
  return url.replace(/https?:\/\//g, "");
};

const isPass = ref<boolean>(false);
const validatePass = ref<boolean>(false);
const protocol = ref<string>("http://");
const modelProtocol = ref<string>("http://");
const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  indexer_type,
  vector_url: vector_url
    ? handleUrlFormat(vector_url)
    : `${host}:${indexer_type === "kbadmin_indexer" ? "29530" : "19530"}`,
  embedding_url: handleUrlFormat(embedding_url),
  embedding_model: {
    ...embedding_model,
    model_id:
      props.formType === "update"
        ? embedding_model.model_id
        : indexer_type === "kbadmin_indexer"
        ? undefined
        : embedding_model.model_id,
  },
});
const rules: FormRules = reactive({
  indexer_type: [
    {
      required: true,
      validator: validateIndeserType,
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

const deviceList = ref<EmptyArrayType>([]);
const modelList = ref<EmptyArrayType>([]);
const isCreate = computed(() => {
  return props.formType === "create";
});
const isKbadmin = computed(() => {
  return form.indexer_type === "kbadmin_indexer";
});
const isMilvus = computed(() => {
  return form.indexer_type === "milvus_vector";
});
const indexerList = computed(() => {
  if (isCreate.value) {
    return Indexer;
  }
  return isKbadmin.value
    ? Indexer.filter((item) => item.value === "kbadmin_indexer")
    : Indexer.filter((item) => item.value !== "kbadmin_indexer");
});
const optionIntroduction = computed(() => {
  const { indexer_type } = form;

  return Indexer.find((item) => item.value === indexer_type)?.describe;
});

const handleTypeChange = (value: SelectValue) => {
  if (value === "kbadmin_indexer") {
    antNotification(
      "warning",
      t("common.prompt"),
      t("pipeline.valid.indexerTypeTip")
    );
  }
  if (isCreate.value) {
    form.embedding_model.model_id = undefined;
    form.embedding_model.model_path = "";
    form.vector_url = `${host}:${isKbadmin.value ? "29530" : "19530"}`;
    if (value === "milvus_vector") {
      nextTick(() => formRef.value?.validateFields([["vector_url"]]));
    }
  }
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
// Handling Model Folding Events
const handleModelVisible = async (visible: boolean) => {
  if (visible) {
    try {
      const modelType = isKbadmin.value
        ? "kbadmin_embedding_model"
        : "embedding";
      const data: any = await getModelList(modelType);
      modelList.value = [].concat(data);
    } catch (err) {
      console.error(err);
    }
  }
};
//Complete model_cath
const handleModelChange = (value: SelectValue) => {
  form.embedding_model.model_path = `./models/${value}`;
};
const handleTestUrl = async () => {
  const vector_url = protocol.value + form.vector_url;
  const { status = "" } = (await requestUrlVerify({ vector_url })) as any;

  if (status !== "200") {
    antNotification("error", t("common.error"), t("pipeline.valid.urlValid3"));
    return;
  }
  validatePass.value = true;
  antNotification(
    "success",
    t("common.success"),
    t("pipeline.valid.urlValid4")
  );
};
const handleUriChange = () => {
  isPass.value = false;
  validatePass.value = false;
};
// Format parameter
const formatFormParam = () => {
  const { indexer_type, vector_url, embedding_url, embedding_model } = form;

  return {
    indexer_type,
    embedding_model: embedding_model,
    vector_url:
      isMilvus.value || isKbadmin.value
        ? protocol.value + vector_url
        : undefined,
    embedding_url: isKbadmin.value
      ? modelProtocol.value + embedding_url
      : undefined,
  };
};
const generateFormData = () => {
  const baseData = { indexer: formatFormParam() };
  const { retriever } = props.formData;

  if (isKbadmin.value && parser_type !== "kbadmin_parser") {
    return {
      ...baseData,
      node_parser: { parser_type: "kbadmin_parser" },
      retriever: { ...retriever, retriever_type: "kbadmin_retriever" },
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
        if (isMilvus.value && !validatePass.value) {
          antNotification(
            "warning",
            t("common.prompt"),
            t("pipeline.valid.urlValid5")
          );
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
  if (isMilvus.value) {
    if (props.formType === "update") {
      isPass.value = validatePass.value = true;
    } else {
      formRef.value?.validateFields([["vector_url"]]);
    }
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
.text-btn {
  width: 72px;
  height: 30px;
  margin: 0 -11px;
  border-radius: 0 6px 6px 0;
}
</style>
