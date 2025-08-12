<template>
  <div class="column-selector">
    <a-popover
      v-model:open="popoverVisible"
      trigger="click"
      placement="bottomRight"
    >
      <template #content>
        <div class="column-selector-popover">
          <div class="header-wrap">
            <a-checkbox
              v-model:checked="checkAll"
              :indeterminate="indeterminate"
              @change="handleCheckAll"
            >
              {{ $t("common.all") }}
            </a-checkbox>
            <a-button type="link" size="small" @click="handleReset">
              {{ $t("common.reset") }}
            </a-button>
          </div>
          <a-divider style="margin: 8px 0" />
          <a-checkbox-group
            v-model:value="checkedKeys"
            style="display: flex; flex-direction: column"
          >
            <a-checkbox
              v-for="column in props.columns"
              :key="column.key"
              :value="column.key"
              :disabled="column.disabled"
            >
              {{ column.title }}
            </a-checkbox>
          </a-checkbox-group>
        </div>
      </template>
      <div class="icon-button">
        <SvgIcon name="icon-collocation" :size="22" />
      </div>
    </a-popover>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from "vue";
import SvgIcon from "./SvgIcon.vue";

const props = defineProps({
  columns: {
    type: Array<TableColumns>,
    required: true,
    default: () => [],
  },
});
const emit = defineEmits(["change"]);

const popoverVisible = ref(false);
const checkedKeys = ref<string[]>([]);

const getAvailableColumns = () => {
  return props.columns.filter((column) => !column.disabled);
};

const getDisabledCheckedKeys = () => {
  return props.columns
    .filter((column) => column.disabled && column.visible)
    .map((column) => column.key);
};

const getInitialCheckedKeys = () => {
  return [
    ...getAvailableColumns()
      .filter((column) => column.visible !== false)
      .map((column) => column.key),
    ...getDisabledCheckedKeys(),
  ];
};

const checkAll = computed({
  get: () => {
    const availableColumns = getAvailableColumns();
    return (
      checkedKeys.value.length ===
      availableColumns.length + getDisabledCheckedKeys().length
    );
  },
  set: (val) => {
    const allKeysToSet = val
      ? [
          ...getAvailableColumns().map((column) => column.key),
          ...getDisabledCheckedKeys(),
        ]
      : getDisabledCheckedKeys();
    checkedKeys.value = Array.from(new Set(allKeysToSet));
    handleCheck();
  },
});

const indeterminate = computed(() => {
  const availableColumns = getAvailableColumns();
  return (
    checkedKeys.value.length > 0 &&
    checkedKeys.value.length <
      availableColumns.length + getDisabledCheckedKeys().length
  );
});

const handleCheckAll = (e: any) => {
  checkAll.value = e.target.checked;
};

const handleReset = () => {
  checkedKeys.value = props.columns
    .filter((column) => column.visible !== false)
    .map((column) => column.key);

  handleCheck();
};

const handleCheck = () => {
  const updatedColumns = props.columns.map((column) => ({
    ...column,
    visible: checkedKeys.value.includes(column.key),
  }));
  const showColumns = updatedColumns.filter((item) => item.visible);
  emit("change", showColumns);
};

watch(
  () => props.columns,
  () => {
    checkedKeys.value = getInitialCheckedKeys();
    handleCheck();
  },
  { immediate: true, deep: true }
);

watch(checkedKeys, handleCheck);
</script>

<style scoped lang="less">
.column-selector-popover {
  min-width: 200px;
  max-height: 320px;
  overflow-y: auto;
  margin-right: -8px;
  .header-wrap {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px;
    .intel-btn-link:hover {
      color: var(--color-primary);
    }
  }
}
.icon-button {
  width: 32px;
  height: 32px;
}
</style>
