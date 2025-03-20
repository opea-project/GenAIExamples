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
    <a-form-item label="Name" name="name">
      <a-input
        v-model:value.trim="form.name"
        :maxlength="30"
        :disabled="disabledName"
      />
      <FormTooltip title="The name identifier of the pipeline" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Basic">
import type { FormInstance } from "ant-design-vue";
import { reactive, ref, computed } from "vue";

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
    { required: true, message: "Please input name", trigger: "blur" },
    {
      min: 2,
      max: 30,
      message: "Name should be between 2 and 30 characters",
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
