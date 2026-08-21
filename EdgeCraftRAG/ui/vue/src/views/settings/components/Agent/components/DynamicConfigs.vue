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
        <a-form-item
          :label="field.label"
          class="slider-wrap"
          :validate-status="jsonErrors[field.key] ? 'error' : undefined"
          :help="jsonErrors[field.key]"
        >
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
          <div v-else class="instruction-field">
            <div
              v-if="!expandedFields.has(field.key)"
              class="instruction-preview"
              @click="handleExpand(field)"
            >
              <span class="text-wrap">{{ getDisplayValue(field) }}</span>
              <span class="expand-btn">
                <EditOutlined :style="{ fontSize: '16px' }" />
              </span>
            </div>
            <a-textarea
              v-else-if="field.type === 'json'"
              allowClear
              v-model:value="jsonText[field.key]"
              :placeholder="$t('common.inputTip')"
              :rows="6"
              :auto-size="false"
              @blur="handleJsonBlur(field.key)"
            />
            <a-textarea
              v-else
              allowClear
              v-model:value="form[field.key]"
              :placeholder="$t('common.inputTip')"
              :rows="4"
              :auto-size="false"
              @blur="expandedFields.delete(field.key)"
            />
          </div>
        </a-form-item>
      </template>
    </a-form>
  </div>
</template>

<script lang="ts" setup name="DynamicConfigs">
import { formatTextStrict } from "@/utils/common";
import { EditOutlined } from "@ant-design/icons-vue";
import type { PropType } from "vue";
import { computed, reactive, watch } from "vue";
import { useI18n } from "vue-i18n";

type JsonConfigValue = Record<string, any> | any[];
type RawConfigValue = number | boolean | string | JsonConfigValue;

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
const { t } = useI18n();

const typeMap: Record<string, Field["type"]> = {
  string: "string",
  number: "number",
  boolean: "boolean",
};
type Field = {
  key: string;
  label: string;
  type: "number" | "boolean" | "string" | "json";
  params: EmptyObjectType;
};

const sliderMarks = reactive({ 0: "0", 200: "200" });
const expandedFields = reactive(new Set<string>());
const jsonText = reactive<Record<string, string>>({});
const jsonErrors = reactive<Record<string, string>>({});

const isJsonConfigValue = (value: unknown): value is JsonConfigValue =>
  typeof value === "object" && value !== null;

const stringifyJsonValue = (value: unknown) => {
  try {
    return JSON.stringify(value, null, 2);
  } catch (err) {
    console.error(err);
    return "";
  }
};

const inferField = (key: string, value: RawConfigValue): Field => {
  const valueType = typeof value;
  const type = isJsonConfigValue(value)
    ? "json"
    : typeMap[valueType] || "string";
  const params = { default: value };

  const label = formatTextStrict(key);
  return { key, label, type, params };
};

const schema = computed(() =>
  Object.entries(props.configs).map(([k, v]) => inferField(k, v)),
);

const form = reactive<EmptyObjectType>({ ...props.modelValue });

const parseJsonField = (key: string) => {
  try {
    const value = JSON.parse(jsonText[key] || "");
    if (!isJsonConfigValue(value)) {
      throw new Error("JSON config value must be an object or array.");
    }
    form[key] = value;
    delete jsonErrors[key];
    return true;
  } catch (err) {
    console.error(err);
    jsonErrors[key] = t("common.jsonInvalid");
    return false;
  }
};

const handleExpand = (field: Field) => {
  if (field.type === "json") {
    jsonText[field.key] = stringifyJsonValue(form[field.key]);
  }
  expandedFields.add(field.key);
};

const handleJsonBlur = (key: string) => {
  if (parseJsonField(key)) {
    expandedFields.delete(key);
  }
};

const validate = () => {
  return schema.value.every((field) => {
    if (field.type !== "json" || !expandedFields.has(field.key)) return true;
    return parseJsonField(field.key);
  });
};

const getDisplayValue = (field: Field) => {
  return isJsonConfigValue(form[field.key])
    ? stringifyJsonValue(form[field.key])
    : form[field.key];
};

defineExpose({ validate });

watch(
  () => props.modelValue,
  (data) => {
    Object.assign(form, data);
  },
  { deep: true },
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

.instruction-field {
  width: 100%;
}

.instruction-preview {
  padding: 4px 11px;
  border: 1px solid var(--border-info);
  border-radius: 6px;
  min-height: 32px;
  line-height: 1.5;
  cursor: pointer;
  word-break: break-word;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  &:hover {
    border: 1px solid var(--color-primary-hover);
  }

  .text-wrap {
    .single-ellipsis;
  }

  .expand-btn {
    flex-shrink: 0;
    padding: 0;
    height: auto;
    line-height: inherit;
    font-size: 12px;
    &:hover {
      color: var(--color-primary-hover);
    }
  }
}
</style>
