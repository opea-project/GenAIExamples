<template>
  <a-modal
    v-model:open="modelVisible"
    width="800px"
    centered
    destroyOnClose
    :title="dialogTitle"
    :keyboard="false"
    :maskClosable="false"
    @cancel="handleCancel"
    class="experience-dialog"
  >
    <div class="enter-wrap">
      <a-form
        :model="form"
        :rules="rules"
        name="form"
        ref="formRef"
        autocomplete="off"
        class="form-wrap"
        layout="vertical"
      >
        <div
          class="item-wrap"
          v-for="(item, index) in form.experience"
          :key="index"
        >
          <a-form-item
            :label="`${$t('experience.label.experience')} ${
              isEdit ? '' : `${index + 1}`
            }`"
            :name="['experience', index, 'question']"
            :rules="rules.experience"
          >
            <a-textarea
              v-model:value="item.question"
              :placeholder="$t('experience.placeholder.experience')"
              :auto-size="{ minRows: 1, maxRows: 2 }"
              :disabled="isEdit"
            />
          </a-form-item>
          <a-form-item
            :label="$t('experience.label.contents')"
            :name="['experience', index, 'content']"
            :rules="rules.contentList"
            class="gt-wrap"
          >
            <div
              v-for="(contentItem, k) in item.content"
              :key="k"
              class="item-wrap content-wrap flex-left"
            >
              <a-form-item
                :label="`${$t('experience.label.content')} ${k + 1}`"
                :name="['experience', index, 'content', k]"
                :rules="rules.text"
                class="flex-item"
              >
                <a-textarea
                  v-model:value="item.content[k]"
                  :placeholder="$t('experience.placeholder.content')"
                  :auto-size="{ minRows: 1, maxRows: 3 }"
                />
              </a-form-item>

              <div class="icon-wrap">
                <a-tooltip
                  placement="topRight"
                  arrow-point-at-center
                  :title="$t('experience.delContent')"
                  v-if="item.content?.length > 1"
                >
                  <DeleteOutlined
                    @click="handleContentDelete(item.content, k)"
                  />
                </a-tooltip>
              </div>
            </div>
            <div class="add-wrap" @click="handleContentAdd(item.content)">
              <PlusOutlined /> {{ $t("experience.addContent") }}
            </div>
          </a-form-item>
          <div class="icon-wrap">
            <a-tooltip
              placement="topRight"
              arrow-point-at-center
              :title="$t('experience.delExperience')"
              v-if="form.experience?.length > 1"
            >
              <MinusCircleOutlined @click="handleDelete(index)" />
            </a-tooltip>
          </div>
        </div>
        <div v-if="!isEdit" class="operate-wrap" @click="handleAdd">
          <PlusOutlined />
          {{ $t("experience.addExperience") }}
        </div>
      </a-form>
    </div>
    <template #footer>
      <a-button type="primary" ghost @click="handleCancel">{{
        $t("common.cancel")
      }}</a-button>
      <a-button
        key="submit"
        type="primary"
        :loading="submitLoading"
        @click="handleSubmit"
        >{{ $t("common.submit") }}</a-button
      >
    </template>
  </a-modal>
</template>

<script lang="ts" setup name="UpdateDialog">
import {
  requestExperienceConfirm,
  requestExperienceCreate,
  requestExperienceUpdate,
} from "@/api/knowledgeBase";
import {
  MinusCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
} from "@ant-design/icons-vue";
import { FormInstance, Modal } from "ant-design-vue";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { RuleObject } from "ant-design-vue/es/form/interface";
import { useNotification } from "@/utils/common";

interface FormRules {
  [key: string]: RuleObject | RuleObject[];
}

interface FormType {
  experience: ExperienceType[];
}

interface ExperienceType {
  question: string;
  content: string[];
}

const props = defineProps({
  dialogData: {
    type: Array as PropType<ExperienceType[]>,
    default: () => [],
  },
  dialogType: {
    type: String,
    default: "create",
  },
});

const defaultExperienceList = [
  {
    question: "",
    content: [""],
  },
];

const { t } = useI18n();
const { antNotification } = useNotification();
const emit = defineEmits(["close", "search"]);
const typeMap = {
  create: t("experience.create"),
  edit: t("experience.edit"),
} as const;
const dialogTitle = computed(() => {
  return typeMap[props.dialogType as keyof typeof typeMap];
});
const isEdit = computed(() => {
  return props.dialogType === "edit";
});

const modelVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const formRef = ref<FormInstance>();

const form = reactive<FormType>({
  experience: props.dialogData.length
    ? props.dialogData
    : defaultExperienceList,
});

const rules: FormRules = reactive({
  question: [
    {
      required: true,
      message: t("experience.valid.experience"),
      trigger: "change",
    },
  ],
  contentList: [
    {
      required: true,
      type: "array",
      message: t("experience.valid.content"),
      trigger: "change",
    },
  ],
  text: [
    {
      required: true,
      message: t("experience.valid.content"),
      trigger: "change",
    },
  ],
});

const handleAdd = () => {
  form.experience.push({
    question: "",
    content: [""],
  });
};
const handleDelete = (index: number) => {
  form.experience.splice(index, 1);
};
const handleContentAdd = (content: string[]) => {
  content.push("");
};
const handleContentDelete = (content: string[], index: number) => {
  content.splice(index, 1);
};

// Submit
const handleSubmit = () => {
  formRef.value?.validate().then(() => {
    submitLoading.value = true;
    const { experience } = form;
    const apiUrl = isEdit.value
      ? requestExperienceUpdate(experience[0])
      : requestExperienceCreate(experience);
    apiUrl
      .then((data: any) => {
        const { code } = data;
        if (code === 2001) {
          handleSelectMode();
        } else {
          handleRefresh();

          if (!isEdit.value)
            antNotification(
              "success",
              t("common.success"),
              t("request.experience.createSucc")
            );
        }
      })
      .catch((error: any) => {
        console.error(error);
      })
      .finally(() => {
        submitLoading.value = false;
      });
  });
};
const handleSelectMode = () => {
  const { experience } = form;
  Modal.confirm({
    title: t("common.prompt"),
    content: t("experience.selectTip"),
    okText: t("experience.cover"),
    cancelText: t("experience.increase"),
    centered: true,
    async onOk() {
      const flag = false;
      await requestExperienceConfirm(flag, experience);
      handleRefresh();
    },
    async onCancel() {
      const flag = true;
      await requestExperienceConfirm(flag, experience);
      handleRefresh();
    },
  });
};

//close
const handleCancel = () => {
  emit("close");
};

//close
const handleRefresh = () => {
  emit("search");
  handleCancel();
};
</script>

<style scoped lang="less">
.enter-wrap {
  width: 100%;
  // max-height: 500px;
  // overflow-y: auto;
  .title-wrap {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--font-main-color);
  }
  .form-wrap {
    .item-wrap {
      padding: 16px 32px 16px 16px;
      border: 1px solid var(--border-main-color);
      position: relative;
      margin-bottom: 16px;
      border-radius: 6px;
      .gt-wrap {
        margin-bottom: 0;
        :deep(.intel-form-item-control-input-content) {
          display: block;
        }
        .flex-item {
          flex: 1;
          :deep(.intel-form-item-control-input-content) {
            display: flex;
            align-items: center;
            gap: 6px;
          }
        }
      }
      .content-wrap {
        background-color: var(--bg-card-color);
        gap: 12px;
        padding-right: 16px;
        padding-bottom: 8px;
        margin-bottom: 12px;
        :deep(.intel-form-item) {
          flex: 1;
        }
        .icon-wrap {
          justify-content: end;
        }
      }
      .add-wrap {
        .flex-end;
        gap: 6px;
        cursor: pointer;
        color: var(--color-primary);
        &:hover {
          color: var(--color-primary-hover);
        }
      }
      .flex-wrap {
        display: flex;
        gap: 6px;
        align-items: start;
      }
      .icon-wrap {
        position: absolute;
        top: 16px;
        right: 12px;
        cursor: pointer;
        display: inline-flex;
        gap: 8px;
        width: 42px;
        .anticon {
          font-size: 16px;
          &:hover {
            color: var(--color-primary);
          }
          &.anticon-delete {
            &:hover {
              color: var(--color-error) !important;
            }
          }
          &.anticon-minus-circle {
            &:hover {
              color: var(--color-error) !important;
            }
          }
        }
      }
    }
  }
  .operate-wrap {
    height: 28px;
    border-radius: 4px;
    cursor: pointer;
    gap: 4px;
    border: 1px dashed var(--border-main-color);
    .vertical-center;
    &:hover {
      border: 1px dashed var(--color-primary-hover);
      color: var(--color-primary-hover);
    }
  }
}
</style>
