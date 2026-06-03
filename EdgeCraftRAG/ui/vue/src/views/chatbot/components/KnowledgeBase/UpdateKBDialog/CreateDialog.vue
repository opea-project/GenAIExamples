<template>
  <a-modal
    v-model:open="modelVisible"
    width="900px"
    centered
    destroyOnClose
    :title="$t('knowledge.create')"
    :keyboard="false"
    :maskClosable="false"
    @cancel="handleClose"
  >
    <div class="step-container">
      <div
        v-for="step in visibleSteps"
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
        <a-button v-if="hasPrev" type="primary" ghost @click="handleLast">
          {{ $t("common.prev") }}
        </a-button>
        <span v-else />

        <div>
          <span v-if="!isProceed" class="tips-wrap">
            <ExclamationCircleOutlined />
            {{ $t("pipeline.urlValidTip") }}
          </span>

          <a-button
            v-if="hasNext"
            type="primary"
            :disabled="!isProceed"
            @click="handleNext"
          >
            {{ $t("common.next") }}
          </a-button>

          <a-button
            v-else
            type="primary"
            :loading="submitLoading"
            @click="handleSubmit"
          >
            {{ $t("common.submit") }}
          </a-button>
        </div>
      </div>
    </template>
  </a-modal>
</template>

<script lang="ts" setup name="CreateDialog">
import { requestKnowledgeBaseCreate } from "@/api/knowledgeBase";
import { ExclamationCircleOutlined } from "@ant-design/icons-vue";
import { computed, markRaw, reactive, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { Activated, Basic, Indexer, NodeParser } from "./index";

const { t } = useI18n();
const emit = defineEmits(["switch", "close"]);

const modelVisible = ref(true);
const submitLoading = ref(false);
const currentStep = ref(1);
const pipelineRef = ref<any>(null);
const isProceed = ref(true);
const formData = reactive<Record<string, any>>({});

const allSteps = [
  {
    label: t("knowledge.general"),
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
    label: t("pipeline.isActive"),
    index: 4,
    icon: "icon-active",
    component: markRaw(Activated),
  },
];

const visibleSteps = computed(() => {
  const isKbadmin = formData.comp_subtype === "kbadmin_kb";

  if (isKbadmin) {
    return allSteps.filter((step) => step.index !== 2);
  }

  return allSteps;
});

const currentComponent = computed(() => {
  return visibleSteps.value.find((step) => step.index === currentStep.value)
    ?.component;
});

const getCurrentStepPos = () =>
  visibleSteps.value.findIndex((s) => s.index === currentStep.value);

const hasPrev = computed(() => getCurrentStepPos() > 0);
const hasNext = computed(
  () => getCurrentStepPos() < visibleSteps.value.length - 1,
);

const handleLast = () => {
  const pos = getCurrentStepPos();
  if (pos > 0) {
    currentStep.value = visibleSteps.value[pos - 1].index;
    isProceed.value = true;
  }
};

const handleNext = async () => {
  if (!pipelineRef.value) return;

  const { result = false, data = {} } = await pipelineRef.value.validate();

  if (!result) return;

  Object.assign(formData, data);

  const pos = getCurrentStepPos();
  const next = visibleSteps.value[pos + 1];

  if (next) {
    currentStep.value = next.index;
    isProceed.value = isProceed.value = true;
  }
};

const handleSubmit = async () => {
  await handleNext();
  submitLoading.value = true;
  const { name } = formData;
  try {
    await requestKnowledgeBaseCreate(formData);
    emit("switch", name);
    handleClose();
  } finally {
    submitLoading.value = false;
  }
};

const handleClose = () => {
  emit("close");
};

watch(
  visibleSteps,
  (steps) => {
    const exists = steps.some((s) => s.index === currentStep.value);
    if (!exists) {
      currentStep.value = steps[0].index;
    }
  },
  { immediate: true },
);

watch(
  () => pipelineRef.value?.isProceed,
  (val) => {
    if (val !== undefined) {
      isProceed.value = val;
    }
  },
);
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
.tips-wrap {
  .mr-6;
  display: inline-flex;
  font-size: 12px;
  gap: 4px;
  color: var(--color-second-warning);
}
</style>
