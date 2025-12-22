<template>
  <a-modal
    v-model:open="modelVisible"
    width="800px"
    centered
    destroyOnClose
    :title="$t('pipeline.edit')"
    :keyboard="false"
    :maskClosable="false"
    :closable="false"
    :footer="null"
    class="edit-dialog"
  >
    <div class="edit-container">
      <div class="menu-container">
        <div
          v-for="step in stepList"
          :key="step.index"
          :class="[
            'step-wrap',
            currentStep === step.index ? 'step-active' : '',
          ]"
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
          <a-button type="primary" ghost @click="handleCancel">{{
            $t("common.cancel")
          }}</a-button>
          <a-button
            key="submit"
            type="primary"
            :loading="submitLoading"
            @click="handleSubmit"
            >{{ $t("common.update") }}</a-button
          >
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script lang="ts" setup name="EditDialog">
import { requestPipelineUpdate } from "@/api/pipeline";
import _ from "lodash";
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

const props = defineProps({
  dialogData: {
    type: Object,
    default: () => {},
  },
  dialogId: {
    type: String,
    default: "",
  },
});

const { t } = useI18n();
const emit = defineEmits(["search", "close"]);
const modelVisible = ref<boolean>(true);
const formData = _.cloneDeep(props.dialogData);
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

const currentTitle = computed(() => {
  return stepList.value.find((item) => item.index === currentStep.value)?.label;
});
//last
const handleCancel = () => {
  emit("close");
};

//next，update form
const handleSelect = async (value?: number) => {
  if (pipelineRef.value) {
    const { result = false, data = {} } = await pipelineRef.value?.validate();
    if (result) {
      await Object.assign(formData, data);
      if (value) currentStep.value = value;
      return true;
    } else {
      console.log(t("pipeline.validErr"));
      return false;
    }
  }
  return false;
};
// Submit
const handleSubmit = async () => {
  const isValid = await handleSelect();
  if (!isValid) return;
  submitLoading.value = true;

  requestPipelineUpdate(props.dialogId, formData)
    .then(() => {
      emit("search");
      handleCancel();
    })
    .catch((error) => {
      console.error(error);
    })
    .finally(() => {
      submitLoading.value = false;
    });
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
