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
      <a-form-item
        :label="$t('knowledge.type')"
        name="comp_subtype"
        v-if="!isExperience"
      >
        <a-radio-group
          v-model:value="form.comp_subtype"
          @change="handleTypeChange"
          :disabled="isEdit"
        >
          <a-radio value="origin_kb">{{ $t("knowledge.original") }}</a-radio>
          <a-radio value="kbadmin_kb">{{ $t("knowledge.kbadmin") }}</a-radio>
        </a-radio-group>
      </a-form-item>
      <a-form-item :label="$t('knowledge.name')" name="name" v-if="isOriginal">
        <a-input
          v-model:value.trim="form.name"
          :maxlength="30"
          :disabled="isEdit || isExperience"
          :placeholder="$t('knowledge.nameValid1')"
        />
      </a-form-item>
      <a-form-item
        :label="$t('knowledge.name')"
        :rules="rules.kbName"
        name="name"
        v-else
      >
        <a-select
          showSearch
          v-model:value="form.name"
          :placeholder="$t('knowledge.nameRequired')"
          :disabled="isEdit || isExperience"
        >
          <a-select-option v-for="item in kbList" :key="item" :value="item">{{
            item
          }}</a-select-option>
        </a-select>
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
        <a-radio-group v-model:value="form.active">
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
  getkbadminList,
} from "@/api/knowledgeBase";
import { isValidName } from "@/utils/validate";
import { FormInstance } from "ant-design-vue";
import { computed, ref, onMounted } from "vue";
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
  dialogFlag: {
    type: String,
    default: "knowledge",
  },
});
interface FormType {
  name: string | undefined;
  description: string;
  comp_type: string;
  active: boolean;
  comp_subtype: string;
}

const validateName = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("knowledge.nameValid1"));
  }
  const len = value.length;
  if (len < 2 || len > 30) {
    return Promise.reject(t("knowledge.nameValid2"));
  }
  if (!isValidName(value)) {
    return Promise.reject(t("knowledge.nameValid3"));
  }
  return Promise.resolve();
};

const { t } = useI18n();
const emit = defineEmits(["close", "switch"]);
const { dialogFlag } = props;

const typeMap = {
  create: t(`${dialogFlag}.create`),
  edit: t(`${dialogFlag}.edit`),
} as const;
const dialogTitle = computed(() => {
  return typeMap[props.dialogType as keyof typeof typeMap];
});
const isEdit = computed(() => {
  return props.dialogType === "edit";
});
const isExperience = computed(() => {
  return props.dialogFlag === "experience";
});

const isOriginal = computed(() => {
  return form.comp_subtype === "origin_kb";
});
const modelVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const formRef = ref<FormInstance>();
const {
  comp_subtype = "origin_kb",
  name = undefined,
  description = "",
  active = false,
  experience_active = false,
} = props.dialogData;
const form = reactive<FormType>({
  comp_subtype,
  name: isExperience.value ? "Experience" : name,
  description,
  comp_type: dialogFlag,
  active: isExperience.value ? experience_active : active,
});
const kbList = ref<EmptyArrayType>([]);
const rules: FormRules = reactive({
  comp_subtype: [
    {
      required: true,
      message: t("knowledge.typeValid"),
      trigger: "change",
    },
  ],
  name: [
    {
      required: true,
      validator: validateName,
      trigger: ["blur", "change"],
    },
  ],
  kbName: [
    {
      required: true,
      message: t("knowledge.nameRequired"),
      trigger: "change",
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
const handleTypeChange = () => {
  form.name = undefined;
};
const queryKbadmin = async () => {
  const data: any = await getkbadminList();
  kbList.value = [].concat(data);
};
// Format parameter
const formatFormParam = () => {
  const { name, description, comp_type, active, comp_subtype } = form;
  return {
    name,
    description,
    comp_type,
    comp_subtype: !isExperience.value ? comp_subtype : undefined,
    active: !isExperience.value ? active : undefined,
    experience_active: isExperience.value ? active : undefined,
  };
};
// Submit
const handleSubmit = () => {
  formRef.value?.validate().then(() => {
    submitLoading.value = true;
    const { name } = form;

    const apiUrl = isEdit.value
      ? requestKnowledgeBaseUpdate
      : requestKnowledgeBaseCreate;

    apiUrl(formatFormParam())
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
onMounted(() => {
  queryKbadmin();
});
</script>

<style scoped lang="less">
textarea {
  resize: none;
}
</style>
