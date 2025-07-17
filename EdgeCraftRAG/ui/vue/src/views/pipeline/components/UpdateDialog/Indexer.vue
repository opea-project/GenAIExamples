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
    <a-form-item :label="$t('pipeline.config.indexerType')" name="indexer_type">
      <a-select
        showSearch
        v-model:value="form.indexer_type"
        :placeholder="$t('pipeline.valid.indexerType')"
      >
        <a-select-option
          v-for="item in indexerList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip :title="$t('pipeline.desc.indexerType')" />
    </a-form-item>
    <div class="option-introduction">
      <InfoCircleOutlined />
      {{ $t(optionIntroduction!) }}
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
      :label="$t('pipeline.config.vector_uri')"
      name="vector_uri"
      :rules="rules.vector_uri"
      v-if="form.indexer_type === 'milvus_vector'"
    >
      <a-input
        v-model:value="form.vector_uri"
        :addon-before="protocol"
        :placeholder="$t('pipeline.valid.vector_uri')"
        @change="handleUriChange"
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
      <FormTooltip :title="$t('pipeline.desc.vector_uri')" />
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
  indexer_type: string;
  vector_uri?: string;
  embedding_model: ModelType;
}
const validateUnique = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("pipeline.valid.urlValid1"));
  }
  if (!validateIpPort(value)) {
    return Promise.reject(t("pipeline.valid.urlValid2"));
  }
  isPass.value = true;
  return Promise.resolve();
};
const handleUrlFormat = (url: string) => {
  if (!url) return "";
  return url.replace(/http:\/\//g, "");
};
const {
  indexer_type = "faiss_vector",
  vector_uri = "",
  embedding_model = {
    model_id: "BAAI/bge-small-en-v1.5",
    model_path: "./models/BAAI/bge-small-en-v1.5",
    device: "AUTO",
    weight: "INT4",
  },
} = props.formData?.indexer || {};

const isPass = ref<boolean>(false);
const validatePass = ref<boolean>(false);
const protocol = ref<string>("http://");
const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  indexer_type,
  vector_uri: handleUrlFormat(vector_uri),
  embedding_model,
});
const rules = reactive({
  indexer_type: [
    {
      required: true,
      message: t("pipeline.valid.indexerType"),
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
  vector_uri: [
    {
      required: true,
      validator: validateUnique,
      trigger: "blur",
    },
  ],
});
const indexerList = Indexer;
const deviceList = ref<EmptyArrayType>([]);
const modelList = ref<EmptyArrayType>([]);

const optionIntroduction = computed(() => {
  const { indexer_type } = form;

  return indexerList.find((item) => item.value === indexer_type)?.describe;
});

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
      const data: any = await getModelList("embedding");
      modelList.value = [].concat(data);
    } catch (err) {
      console.error(err);
    }
  }
};
//Complete model_cath
const handleModelChange = (value: string) => {
  form.embedding_model.model_path = `./models/${value}`;
};
const handleTestUrl = async () => {
  const vector_uri = protocol.value + form.vector_uri;
  const { status = "" } = await requestUrlVerify({ vector_uri });

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
  const { indexer_type, vector_uri, embedding_model } = form;

  return {
    indexer_type,
    embedding_model,
    vector_uri:
      indexer_type === "milvus_vector"
        ? protocol.value + vector_uri
        : undefined,
  };
};
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        if (form.indexer_type === "milvus_vector" && !validatePass.value) {
          antNotification(
            "warning",
            t("common.prompt"),
            t("pipeline.valid.urlValid5")
          );
          return;
        }
        resolve({
          result: true,
          data: { indexer: formatFormParam() },
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
