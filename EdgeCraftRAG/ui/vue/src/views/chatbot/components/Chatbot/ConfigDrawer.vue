<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="$t('generation.title')"
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
        <div class="module-title">
          <p>{{ $t("generation.retriever") }}</p>
          <div class="warning-wrap">
            <ExclamationCircleFilled />{{ $t("generation.tips") }}
          </div>
        </div>

        <a-form-item
          :label="$t('generation.config.top_n')"
          name="top_n"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.top_n"
            :min="0"
            :max="100"
            :marks="sliderMarks.top_n"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("generation.desc.top_n") }}
          </div>
        </a-form-item>
        <a-form-item
          :label="$t('pipeline.config.topk')"
          name="k"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.k"
            :min="0"
            :max="500"
            :marks="sliderMarks.k"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("pipeline.desc.topk") }}
          </div>
        </a-form-item>
      </div>
      <div class="module-wrap">
        <div class="module-title">{{ $t("generation.title") }}</div>
        <a-form-item
          :label="$t('generation.config.temperature')"
          name="temperature"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.temperature"
            :min="0"
            :max="1"
            :step="0.01"
            :marks="sliderMarks.temperature"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("generation.desc.temperature") }}
          </div>
        </a-form-item>
        <a-form-item
          :label="$t('generation.config.top_p')"
          name="top_p"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.top_p"
            :min="0"
            :max="1"
            :step="0.01"
            :marks="sliderMarks.temperature"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("generation.desc.top_p") }}
          </div>
        </a-form-item>
        <a-form-item
          :label="$t('generation.config.top_k')"
          name="top_k"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.top_k"
            :min="0"
            :max="200"
            :marks="sliderMarks.top_k"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("generation.desc.top_k") }}
          </div>
        </a-form-item>
        <a-form-item
          :label="$t('generation.config.penalty')"
          name="repetition_penalty"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.repetition_penalty"
            :min="1"
            :max="2"
            :step="0.01"
            :marks="sliderMarks.repetition_penalty"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("generation.desc.penalty") }}
          </div>
        </a-form-item>
        <a-form-item
          :label="$t('generation.config.maxToken')"
          name="max_tokens"
          class="slider-wrap"
        >
          <a-slider
            v-model:value="form.max_tokens"
            :min="1"
            :max="10240"
            :marks="sliderMarks.max_tokens"
          />
          <div class="tips-wrap">
            <InfoCircleFilled />{{ $t("generation.desc.maxToken") }}
          </div>
        </a-form-item>
      </div>
    </a-form>
    <template #footer>
      <a-button style="margin-right: 8px" @click="handleClose">{{
        $t("common.cancel")
      }}</a-button>
      <a-button type="primary" :loading="submitLoading" @click="handleSubmit">{{
        $t("common.confirm")
      }}</a-button>
    </template>
  </a-drawer>
</template>
<script lang="ts" setup name="DetailDrawer">
import {
  InfoCircleFilled,
  ExclamationCircleFilled,
} from "@ant-design/icons-vue";
import { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { ConfigType } from "../../type";

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
  top_n = 0,
  k = 0,
  temperature = 0.01,
  top_p = 0.95,
  top_k = 10,
  repetition_penalty = 1.03,
  max_tokens = 1024,
  stream = true,
} = props.drawerData;

const form = reactive<ConfigType>({
  top_n,
  k,
  temperature,
  top_p,
  top_k,
  repetition_penalty,
  max_tokens,
  stream,
});
const rules: FormRules = reactive({
  top_n: [{ required: true, trigger: "blur" }],
  k: [{ required: true, trigger: "blur" }],
  temperature: [{ required: true, trigger: "blur" }],
  top_p: [{ required: true, trigger: "blur" }],
  top_k: [{ required: true, trigger: "blur" }],
  repetition_penalty: [{ required: true, trigger: "blur" }],
  max_tokens: [{ required: true, trigger: "blur" }],
});
const sliderMarks = reactive<EmptyObjectType>({
  top_n: {
    0: "0",
    100: "100",
  },
  temperature: {
    0: "0",
    1: "1",
  },
  k: {
    0: "0",
    500: "500",
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
    10240: "10240",
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
  .warning-wrap {
    font-weight: 400;
    color: var(--color-second-warning);
    display: flex;
    gap: 6px;
    font-size: 12px;
    .anticon-exclamation-circle {
      margin-top: 0;
      font-size: 13px;
      color: var(--color-warning);
    }
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
