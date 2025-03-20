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
    <a-form-item label="Indexer Type" name="indexer_type">
      <a-select
        showSearch
        v-model:value="form.indexer_type"
        placeholder="please select Indexer Type"
      >
        <a-select-option
          v-for="item in indexerList"
          :key="item.value"
          :value="item.value"
          >{{ item.name }}</a-select-option
        >
      </a-select>
      <FormTooltip
        title="The type of index structure responsible for building based on the parsed nodes"
      />
    </a-form-item>
    <div class="option-introduction">
      <InfoCircleOutlined />
      {{ optionIntroduction }}
    </div>
    <a-form-item
      label="Embedding Model"
      :name="['embedding_model', 'model_id']"
      :rules="rules.model_id"
    >
      <a-select
        showSearch
        v-model:value="form.embedding_model.model_id"
        placeholder="please select Embedding Model"
        @change="handleModelChange"
        @dropdownVisibleChange="handleModelVisible"
      >
        <a-select-option v-for="item in modelList" :key="item" :value="item">{{
          item
        }}</a-select-option>
      </a-select>
      <FormTooltip
        title="Embed the text data to represent it and build a vector index"
      />
    </a-form-item>
    <a-form-item
      label="Embedding run device"
      :name="['embedding_model', 'device']"
      :rules="rules.device"
    >
      <a-select
        showSearch
        v-model:value="form.embedding_model.device"
        placeholder="please select Embedding run device"
        @dropdownVisibleChange="handleDeviceVisible"
      >
        <a-select-option v-for="item in deviceList" :key="item" :value="item">{{
          item
        }}</a-select-option>
      </a-select>
      <FormTooltip title="The device used by the Embedding Model" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Indexer">
import { getRunDevice, getModelList } from "@/api/pipeline";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { Indexer } from "../../enum.ts";
import { ModelType } from "../../type.ts";
import { InfoCircleOutlined } from "@ant-design/icons-vue";

const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
});
interface FormType {
  indexer_type: string;
  embedding_model: ModelType;
}
const {
  indexer_type = "faiss_vector",
  embedding_model = {
    model_id: "BAAI/bge-small-en-v1.5",
    model_path: "./models/BAAI/bge-small-en-v1.5",
    device: "AUTO",
    weight: "INT4",
  },
} = props.formData?.indexer || {};

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  indexer_type,
  embedding_model,
});
const rules = reactive({
  indexer_type: [
    {
      required: true,
      message: "please select Indexer Type",
      trigger: "change",
    },
  ],
  model_id: [
    {
      required: true,
      message: "Please select Embedding Model",
      trigger: "change",
    },
  ],
  device: [
    {
      required: true,
      message: "Please select device",
      trigger: "change",
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
  // form.embedding_model.model_path = `/home/edgeai/media/models/${value}`;
  form.embedding_model.model_path = `./models/${value}`;
};
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        resolve({
          result: true,
          data: { indexer: form },
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
