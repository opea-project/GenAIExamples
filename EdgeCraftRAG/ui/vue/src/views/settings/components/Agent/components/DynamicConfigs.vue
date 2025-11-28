<template>
  <div class="dynamic-configs-form">
    <a-form
      :model="form"
      layout="vertical"
      autocomplete="off"
      class="form-wrap"
      name="Configs"
    >
      <template v-for="field in schema" :key="field.key">
        <a-form-item :label="field.label" class="slider-wrap">
          <div v-if="field.type === 'number'" class="flex-left">
            <a-slider
              v-model:value="form[field.key]"
              :min="0"
              :max="200"
              :marks="sliderMarks"
            />
            <a-form-item noStyle>
              <a-input-number
                v-model:value="form[field.key]"
                :min="0"
                :max="200"
              />
            </a-form-item>
          </div>
          <template v-else-if="field.type === 'boolean'">
            {{ $t("common.no") }}
            <a-switch v-model:checked="form[field.key]" size="small" />
            {{ $t("common.yes") }}
          </template>
          <a-input
            v-else
            allowClear
            v-model:value="form[field.key]"
            :placeholder="$t('common.inputTip')"
          />
        </a-form-item>
      </template>
    </a-form>
  </div>
</template>

<script lang="ts" setup name="DynamicConfigs">
import { formatTextStrict } from "@/utils/common";
import { computed, reactive, watch } from "vue";
import type { PropType } from "vue";

type RawConfigValue = number | boolean | string | { [k: string]: any };

const props = defineProps({
  configs: {
    type: Object as PropType<EmptyObjectType>,
    default: () => ({}),
    required: true,
  },
  modelValue: {
    type: Object as PropType<EmptyObjectType>,
    default: () => ({}),
  },
});
const emit = defineEmits(["update:modelValue"]);

const typeMap: Record<string, Field["type"]> = {
  string: "string",
  number: "number",
  boolean: "boolean",
};
type Field = {
  key: string;
  label: string;
  type: "number" | "boolean" | "string";
  params: EmptyObjectType;
};

const sliderMarks = reactive({ 0: "0", 200: "200" });

const inferField = (key: string, value: RawConfigValue): Field => {
  const valueType = typeof value;
  const type = typeMap[valueType] || "string";
  const params = { default: value };

  const label = formatTextStrict(key);
  return { key, label, type, params };
};

const schema = computed(() =>
  Object.entries(props.configs).map(([k, v]) => inferField(k, v))
);

const form = reactive<EmptyObjectType>({ ...props.modelValue });

watch(
  () => props.modelValue,
  (data) => {
    Object.assign(form, data);
  },
  { deep: true }
);

watch(form, (newForm) => emit("update:modelValue", { ...newForm }), {
  deep: true,
});
</script>

<style scoped lang="less">
.slider-wrap {
  .flex-left {
    gap: 6px;
  }
  .intel-input-number {
    position: relative;
    top: -10px;
  }
}
</style>
