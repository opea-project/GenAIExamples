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
    <a-form-item :label="$t('pipeline.isActive')" name="active">
      <a-radio-group v-model:value="form.active">
        <a-radio :value="true">{{ $t("pipeline.activated") }}</a-radio>
        <a-radio :value="false">{{ $t("pipeline.inactive") }}</a-radio>
      </a-radio-group>
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Basic">
import type { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
});

interface FormType {
  active: boolean;
}
const { active = false } = props.formData;

const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  active,
});
const rules: FormRules = reactive({
  active: [{ required: true, trigger: "change" }],
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
