<template>
  <a-modal
    v-model:open="modelVisible"
    width="800px"
    centered
    destroyOnClose
    :title="$t('knowledge.edit')"
    :keyboard="false"
    :maskClosable="false"
    :closable="false"
    :footer="null"
    class="edit-dialog"
  >
    <div class="edit-container">
      <div class="menu-container">
        <div
          v-for="step in visibleSteps"
          :key="step.index"
          :class="['step-wrap', currentStep === step.index ? 'step-active' : '']"
          @click="handleSelect(step.index)"
        >
          <SvgIcon :name="step.icon" :size="16" inherit />
          {{ step.label }}
        </div>
      </div>

      <div class="body-container">
        <div class="module-title">{{ currentTitle }}</div>
        <keep-alive>
          <component
            :is="currentComponent"
            :form-data="formData"
            form-type="update"
            ref="pipelineRef"
            class="component-wrap"
          />
        </keep-alive>

        <div class="footer-wrap">
          <a-button type="primary" ghost @click="handleCancel">
            {{ $t("common.cancel") }}
          </a-button>
          <a-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ $t("common.update") }}
          </a-button>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup name="EditDialog">
  import { requestKnowledgeBaseUpdate } from "@/api/knowledgeBase";
  import _ from "lodash";
  import { computed, markRaw, reactive, ref, watch } from "vue";
  import { useI18n } from "vue-i18n";
  import { Activated, Basic, Indexer, NodeParser } from "./index";

  const { t } = useI18n();
  const emit = defineEmits(["switch", "close"]);

  const props = defineProps({
    dialogData: {
      type: Object,
      default: () => ({}),
    },
    dialogId: {
      type: String,
      default: "",
    },
  });

  const modelVisible = ref(true);
  const submitLoading = ref(false);
  const currentStep = ref(1);
  const pipelineRef = ref<any>(null);
  const formData = reactive(_.cloneDeep(props.dialogData));

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
      return allSteps.filter(step => step.index !== 2);
    }

    return allSteps;
  });

  const currentComponent = computed(() => {
    return visibleSteps.value.find(step => step.index === currentStep.value)?.component;
  });

  const currentTitle = computed(() => {
    return visibleSteps.value.find(step => step.index === currentStep.value)?.label;
  });

  const handleSelect = async (targetStep?: number) => {
    if (!pipelineRef.value) return false;

    const { result = false, data = {} } = await pipelineRef.value.validate();

    if (!result) {
      console.log(t("pipeline.validErr"));
      return false;
    }

    Object.assign(formData, data);

    if (targetStep) {
      currentStep.value = targetStep;
    }

    return true;
  };

  const handleSubmit = async () => {
    const isValid = await handleSelect();
    if (!isValid) return;

    submitLoading.value = true;
    const { name } = formData;
    try {
      await requestKnowledgeBaseUpdate(formData);
      emit("switch", name);
      handleCancel();
    } finally {
      submitLoading.value = false;
    }
  };

  const handleCancel = () => {
    emit("close");
  };

  watch(
    visibleSteps,
    steps => {
      const exists = steps.some(s => s.index === currentStep.value);
      if (!exists) {
        currentStep.value = steps[0].index;
      }
    },
    { immediate: true }
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
  .edit-container {
    display: grid;
    grid-template-columns: 1fr 3fr;
    border-radius: 6px;
    overflow: hidden;
    min-height: 500px;
    .menu-container {
      padding: 10px 16px;
      background-color: var(--bg-card-color);

      .step-wrap {
        height: 40px;
        line-height: 40px;
        color: var(--font-text-color);
        padding: 0 8px;
        border-radius: 4px;
        margin-bottom: 4px;
        cursor: pointer;
        &:hover {
          background-color: var(--color-primaryBg);
        }

        &.step-active {
          color: var(--color-primary);
          font-weight: 600;
          background-color: var(--color-primaryBg);
          position: relative;
          i {
            font-weight: 500;
          }
        }
      }
    }
    .body-container {
      overflow: auto;
      position: relative;
      display: flex;
      flex-direction: column;
      .component-wrap {
        flex: 1;
        padding: 10px 20px 20px 20px;
      }
      .module-title {
        padding: 12px 20px 0 20px;
        font-size: 18px;
        font-weight: 500;
        color: var(--font-main-color);
      }
      .footer-wrap {
        width: 100%;
        padding: 10px 24px;
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        align-items: center;
        border-top: 1px solid var(--border-main-color);
      }
    }
  }
</style>
