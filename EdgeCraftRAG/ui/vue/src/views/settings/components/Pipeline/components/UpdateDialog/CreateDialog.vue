<template>
  <a-modal
    v-model:open="modelVisible"
    width="900px"
    centered
    destroyOnClose
    :title="$t('pipeline.create')"
    :keyboard="false"
    :maskClosable="false"
    @cancel="handleClose"
  >
    <div class="step-container">
      <div
        v-for="step in stepList"
        :key="step.index"
        :class="['step-wrap', currentStep === step.index ? 'step-active' : '']"
      >
        <SvgIcon :name="step.icon" :size="16" inherit />
        {{ step.label }}
      </div>
    </div>
    <div class="body-container">
      <component
        :is="currentComponent"
        :form-data="formData"
        ref="pipelineRef"
      />
    </div>
    <template #footer>
      <div class="flex-between">
        <a-button
          type="primary"
          ghost
          @click="handleLast"
          v-if="currentStep > 1 && currentStep <= 7"
          >{{ $t("common.prev") }}</a-button
        >
        <span v-else></span>
        <div>
          <a-button
            type="primary"
            @click="handleNext"
            v-if="currentStep >= 1 && currentStep < 7"
            >{{ $t("common.next") }}</a-button
          >
          <a-button
            key="submit"
            type="primary"
            :loading="submitLoading"
            @click="handleSubmit"
            v-else-if="currentStep === 7"
            >{{ $t("common.submit") }}</a-button
          >
        </div>
      </div>
    </template>
  </a-modal>
</template>

<script lang="ts" setup name="CreateDialog">
import { requestPipelineCreate } from "@/api/pipeline";
import { computed, markRaw, ref } from "vue";
import {
  Activated,
  Basic,
  Generator,
  Indexer,
  NodeParser,
  PostProcessor,
  Retriever,
} from "./index";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const emit = defineEmits(["search", "close"]);
const modelVisible = ref<boolean>(true);
const formData = reactive<EmptyObjectType>({});
const submitLoading = ref<boolean>(false);
const currentStep = ref<number>(1);
const pipelineRef = ref<any>(null);
const stepList = ref<EmptyArrayType>([
  {
    label: t("pipeline.config.basic"),
    index: 1,
    icon: "icon-basic",
    component: markRaw(Basic),
  },
  {
    label: t("pipeline.config.nodeParser"),
    index: 2,
    icon: "icon-node-parser",
    component: markRaw(NodeParser),
  },
  {
    label: t("pipeline.config.indexer"),
    index: 3,
    icon: "icon-indexer",
    component: markRaw(Indexer),
  },
  {
    label: t("pipeline.config.retriever"),
    index: 4,
    icon: "icon-retriever",
    component: markRaw(Retriever),
  },
  {
    label: t("pipeline.config.postProcessor"),
    index: 5,
    icon: "icon-post-processor",
    component: markRaw(PostProcessor),
  },
  {
    label: t("pipeline.config.generator"),
    index: 6,
    icon: "icon-generator",
    component: markRaw(Generator),
  },
  {
    label: t("pipeline.isActive"),
    index: 7,
    icon: "icon-active",
    component: markRaw(Activated),
  },
]);

const currentComponent = computed(() => {
  return stepList.value.find((item) => item.index === currentStep.value)
    ?.component;
});

//last
const handleLast = () => {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
};

//next，update form
const handleNext = async () => {
  if (pipelineRef.value) {
    const {
      result = false,
      data = {},
      dest = null,
    } = await pipelineRef.value?.validate();

    if (result) {
      Object.assign(formData, data);

      if (currentStep.value < 7) {
        currentStep.value = dest ? dest : currentStep.value + 1;
      }
    } else {
      console.log(t("pipeline.validErr"));
    }
  }
};
// Submit
const handleSubmit = async () => {
  await handleNext();

  submitLoading.value = true;
  requestPipelineCreate(formData)
    .then(() => {
      emit("search");
      handleClose();
    })
    .catch((error) => {
      console.error(error);
    })
    .finally(() => {
      submitLoading.value = false;
    });
};

//close
const handleClose = () => {
  emit("close");
};
</script>

<style scoped lang="less">
@keyframes expandBorder {
  to {
    width: 100%;
    left: 0;
    transform: none;
  }
}
.step-container {
  width: 100%;
  margin-bottom: 20px;
  border-radius: 6px 6px 0 0;
  overflow: hidden;
  display: flex;

  .step-wrap {
    flex: 1;
    background-color: var(--menu-bg);
    border-bottom: 1px solid var(--border-main-color);
    height: 38px;
    line-height: 38px;
    text-align: center;
    color: var(--font-text-color);
    i {
      position: relative;
      top: 1px;
    }

    &.step-active {
      color: var(--color-primary);
      font-weight: 600;
      background-color: var(--color-primaryBg);
      position: relative;
      i {
        font-weight: 500;
      }
      &::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 2px;
        background-color: var(--color-primary-hover);
        animation: expandBorder 1s forwards;
      }
    }
  }
}
.body-container {
  min-height: 400px;
}
</style>
