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
const rules = reactive({
  name: [
    {
      required: true,
      message: t("pipeline.valid.nameValid1"),
      trigger: "blur",
    },
    {
      min: 2,
      max: 30,
      message: t("pipeline.valid.nameValid2"),
      trigger: "blur",
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
