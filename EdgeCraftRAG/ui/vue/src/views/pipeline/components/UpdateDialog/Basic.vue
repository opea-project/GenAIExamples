<template>
  <a-form
    :model="form"
    :rules="rules"
    name="basic"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <a-form-item :label="$t('pipeline.name')" name="name">
      <a-input
        v-model:value.trim="form.name"
        :maxlength="30"
        :disabled="disabledName"
      />
      <FormTooltip :title="$t('pipeline.desc.name')" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Basic">
import { isValidPipelineName } from "@/utils/validate";
import type { FormInstance } from "ant-design-vue";
import { reactive, ref, computed } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
  formType: {
    type: String,
    default: "create",
  },
});
const validateName = async (rule: any, value: string) => {
  if (!value) {
    return Promise.reject(t("pipeline.valid.nameValid1"));
  }
  const len = value.length;
  if (len < 2 || len > 30) {
    return Promise.reject(t("pipeline.valid.nameValid2"));
  }
  if (!isValidPipelineName(value)) {
    return Promise.reject(t("pipeline.valid.nameValid3"));
  }
  return Promise.resolve();
};
const disabledName = computed(() => {
  const { formType } = props;
  return formType === "update";
});
interface FormType {
  name: string;
}
const { name = "default" } = props.formData;

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  name,
});
const rules: FormRules = reactive({
  name: [
    {
      required: true,
      validator: validateName,
      trigger: ["blur", "change"],
    },
  ],
});
// Validate the form, throw results form
const handleValidate = (): Promise<object> => {
  return new Promise((resolve) => {
    formRef.value
      ?.validate()
      .then(() => {
        resolve({
          result: true,
          data: form,
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
