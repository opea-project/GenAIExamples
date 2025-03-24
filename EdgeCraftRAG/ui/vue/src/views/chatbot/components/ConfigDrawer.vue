<template>
  <a-drawer
    v-model:open="drawerVisible"
    title="Ceneration Configuration"
    destroyOnClose
    width="600px"
    :keyboard="false"
    :maskClosable="false"
    @close="handleClose"
  >
    <a-form
      :model="form"
      :rules="rules"
      name="basic"
      layout="vertical"
      ref="formRef"
      autocomplete="off"
      class="form-wrap"
    >
      <div class="module-wrap">
        <div class="module-title">Retriever Configuration</div>
        <a-form-item label="Rerank top n" name="top_n" class="slider-wrap">
          <a-slider
            v-model:value="form.top_n"
            :min="1"
            :max="10"
            :marks="sliderMarks.top_n"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />Number of rerank results
          </div>
        </a-form-item>
      </div>
      <div class="module-wrap">
        <div class="module-title">Generation Configuration</div>
        <a-form-item label="Temperature" name="temperature" class="slider-wrap">
          <a-slider
            v-model:value="form.temperature"
            :min="0"
            :max="1"
            :step="0.1"
            :marks="sliderMarks.temperature"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />Higher values produce more diverse outputs
          </div>
        </a-form-item>
        <a-form-item
          label="Top-p (nucleus sampling)"
          name="top_p"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.top_p"
            :min="0"
            :max="1"
            :step="0.1"
            :marks="sliderMarks.temperature"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />Sample from the smallest possible set of tokens
            whose cumulative probability exceeds top_p. Set to 1 to disable and
            sample from all tokens.
          </div>
        </a-form-item>
        <a-form-item label="Top-k" name="top_k" class="slider-wrap">
          <a-slider
            v-model:value="form.top_k"
            :min="0"
            :max="200"
            :marks="sliderMarks.top_k"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />Sample from a shortlist of top-k tokens — 0 to
            disable and sample from all tokens.
          </div>
        </a-form-item>
        <a-form-item
          label="Repetition Penalty"
          name="repetition_penalty"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.repetition_penalty"
            :min="1"
            :max="2"
            :step="0.1"
            :marks="sliderMarks.repetition_penalty"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />Penalize repetition — 1.0 to disable.
          </div>
        </a-form-item>
        <a-form-item
          label="Max Token Number"
          name="max_tokens"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.max_tokens"
            :min="1"
            :max="8192"
            :marks="sliderMarks.max_tokens"
          />
          <div class="tips-wrap"><InfoCircleFilled />Set Max Output Token.</div>
        </a-form-item>
      </div>
    </a-form>
    <template #footer>
      <a-button style="margin-right: 8px" @click="handleClose">Cancel</a-button>
      <a-button type="primary" :loading="submitLoading" @click="handleSubmit"
        >Confirm</a-button
      >
    </template>
  </a-drawer>
</template>
<script lang="ts" setup name="DetailDrawer">
import { InfoCircleFilled } from "@ant-design/icons-vue";
import { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { ConfigType } from "../type";

const props = defineProps({
  drawerData: {
    type: Object,
    required: true,
    default: () => {},
  },
});
const emit = defineEmits(["close", "update"]);

const formRef = ref<FormInstance>();
const drawerVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const {
  top_n = 5,
  temperature = 0.1,
  top_p = 1,
  top_k = 50,
  repetition_penalty = 1.1,
  max_tokens = 512,
  stream = true,
} = props.drawerData;

const form = reactive<ConfigType>({
  top_n,
  temperature,
  top_p,
  top_k,
  repetition_penalty,
  max_tokens,
  stream,
});
const rules = reactive({
  top_n: [{ required: true, trigger: "blur" }],
  temperature: [{ required: true, trigger: "blur" }],
  top_p: [{ required: true, trigger: "blur" }],
  top_k: [{ required: true, trigger: "blur" }],
  repetition_penalty: [{ required: true, trigger: "blur" }],
  max_tokens: [{ required: true, trigger: "blur" }],
});
const sliderMarks = reactive<EmptyObjectType>({
  top_n: {
    1: "1",
    10: "10",
  },
  temperature: {
    0: "0",
    1: "1",
  },
  top_k: {
    0: "0",
    200: "200",
  },
  repetition_penalty: {
    1: "1",
    2: "2",
  },
  max_tokens: {
    1: "1",
    8192: "8192",
  },
});
const handleClose = () => {
  emit("close");
};
const handleSubmit = () => {
  formRef.value?.validate().then(() => {
    emit("update", form);
    handleClose();
  });
};
</script>
<style scoped lang="less">
.form-wrap {
  .slider-wrap .intel-slider {
    width: calc(100% - 20px);
  }
  :deep(.intel-form-item-control-input-content) {
    display: block;
    .intel-slider-with-marks {
      margin-bottom: 20px;
    }
  }
  :deep(.intel-form-item) {
    margin-bottom: 0;
  }
}
.module-wrap {
  padding: 16px;
  border: 1px solid var(--border-main-color);
  position: relative;
  border-radius: 6px;
  &:not(:last-child) {
    margin-bottom: 16px;
  }
  .card-shadow;
  .module-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 12px;
  }
  .tips-wrap {
    display: flex;
    color: var(--font-info-color);
    gap: 6px;
    font-size: 12px;
    .anticon-info-circle {
      margin-top: 0;
      font-size: 13px;
    }
  }
}
</style>
