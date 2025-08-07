<template>
  <a-modal
    v-model:open="modelVisible"
    width="700px"
    centered
    destroyOnClose
    :title="dialogTitle"
    :keyboard="false"
    :maskClosable="false"
    @cancel="handleCancel"
  >
    <a-form
      :model="form"
      :rules="rules"
      name="form"
      ref="formRef"
      autocomplete="off"
      :label-col="{ style: { width: '100px' } }"
    >
      <a-form-item :label="$t('knowledge.name')" name="name">
        <a-input
          v-model:value.trim="form.name"
          :maxlength="30"
          :disabled="isEdit"
          :placeholder="$t('knowledge.nameValid1')"
        />
      </a-form-item>
      <a-form-item :label="$t('knowledge.des')">
        <a-textarea
          v-model:value.trim="form.description"
          :placeholder="$t('knowledge.desValid')"
          :rows="3"
          :autoSize="false"
        />
      </a-form-item>
      <a-form-item :label="$t('pipeline.isActive')" name="active">
        <a-radio-group v-model:value="form.active" :disabled="isActivated">
          <a-radio :value="true">{{ $t("pipeline.activated") }}</a-radio>
          <a-radio :value="false">{{ $t("pipeline.inactive") }}</a-radio>
        </a-radio-group>
      </a-form-item>
    </a-form>
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

<script lang="ts" setup name="CreateDialog">
import {
  requestKnowledgeBaseCreate,
  requestKnowledgeBaseUpdate,
} from "@/api/knowledgeBase";
import { isValidName } from "@/utils/validate";
import { FormInstance } from "ant-design-vue";
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps({
  dialogData: {
    type: Object,
    default: () => {},
  },
  dialogType: {
    type: String,
    default: "create",
  },
});
interface FormType {
  name: string;
  description: string;
  active: boolean;
}

const validateName = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("knowledge.nameValid1"));
  }
  const len = value.length;
  if (len < 2 || len > 30) {
    return Promise.reject(t("knowledge.nameValid2"));
  }
  console.log(isValidName(value));
  if (!isValidName(value)) {
    return Promise.reject(t("knowledge.nameValid3"));
  }
  return Promise.resolve();
};

const { t } = useI18n();
const emit = defineEmits(["close", "switch"]);
const typeMap = {
  create: t("knowledge.create"),
  edit: t("knowledge.edit"),
} as const;
const dialogTitle = computed(() => {
  return typeMap[props.dialogType as keyof typeof typeMap];
});
const isEdit = computed(() => {
  return props.dialogType === "edit";
});
const isActivated = computed(() => {
  return props.dialogData?.active;
});
const modelVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const formRef = ref<FormInstance>();
const { name = "", description = "", active = false } = props.dialogData;
const form = reactive<FormType>({
  name,
  description,
  active,
});

const rules = reactive({
  name: [
    {
      required: true,
      validator: validateName,
      trigger: ["blur", "change"],
    },
  ],
  active: [
    {
      required: true,
      message: t("knowledge.activeValid"),
      trigger: "change",
    },
  ],
});
// Submit
const handleSubmit = () => {
  formRef.value?.validate().then(() => {
    submitLoading.value = true;
    const { name } = form;
    const apiUrl =
      props.dialogType === "edit"
        ? requestKnowledgeBaseUpdate
        : requestKnowledgeBaseCreate;

    apiUrl(form)
      .then(() => {
        emit("switch", name);
        handleCancel();
      })
      .catch((error: any) => {
        console.error(error);
      })
      .finally(() => {
        submitLoading.value = false;
      });
  });
};

//close
const handleCancel = () => {
  emit("close");
};
</script>

<style scoped lang="less">
textarea {
  resize: none;
}
</style>
