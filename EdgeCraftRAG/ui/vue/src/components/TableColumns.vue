<template>
  <div class="column-selector">
    <a-popover v-model:open="popoverVisible" trigger="click" placement="bottomRight">
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
          <a-divider class="divider-wrap" />
          <div class="column-tree">
            <template v-for="column in props.columns" :key="column.key">
              <div v-if="column.children && column.children.length">
                <a-checkbox
                  :checked="isParentAllChecked(column)"
                  :indeterminate="isParentIndeterminate(column)"
                  @change="e => handleParentChange(column, e.target.checked)"
                  :disabled="column.disabled"
                >
                  {{ column.title }}
                </a-checkbox>

                <div class="children-columns">
                  <a-checkbox
                    v-for="child in column.children"
                    :key="child.key"
                    :checked="checkedKeys.includes(child.key)"
                    @change="e => handleChildChange(child, e.target.checked)"
                    :disabled="child.disabled"
                  >
                    <span class="child-title">{{ child.title }}</span>
                  </a-checkbox>
                </div>
              </div>
              <a-checkbox
                v-else
                :key="column.key"
                :checked="checkedKeys.includes(column.key)"
                @change="e => handleChange(column, e.target.checked)"
                :disabled="column.disabled"
              >
                {{ column.title }}
              </a-checkbox>
            </template>
          </div>
        </div>
      </template>
      <div class="icon-button">
        <SvgIcon name="icon-collocation" :size="22" />
      </div>
    </a-popover>
  </div>
</template>

<script lang="ts" setup name="TableColumns">
  import { computed, ref, watch } from "vue";
  import SvgIcon from "./SvgIcon.vue";

  const props = defineProps({
    columns: {
      type: Array as () => TableColumns[],
      required: true,
      default: () => [],
    },
  });
  const emit = defineEmits(["change"]);

  const popoverVisible = ref(false);
  const checkedKeys = ref<string[]>([]);

  const getAvailableLeafKeys = (): string[] => {
    const keys: string[] = [];
    const traverse = (cols: TableColumns[]) => {
      cols.forEach(col => {
        if (col.children && col.children.length > 0) {
          traverse(col.children);
        } else if (!col.disabled) {
          keys.push(col.key);
        }
      });
    };
    traverse(props.columns);
    return keys;
  };

  const getDisabledCheckedKeys = (): string[] => {
    const keys: string[] = [];
    const traverse = (cols: TableColumns[]) => {
      cols.forEach(col => {
        if (col.children && col.children.length > 0) {
          traverse(col.children);
        } else if (col.disabled) {
          keys.push(col.key);
        }
      });
    };
    traverse(props.columns);
    return keys;
  };

  const getInitialCheckedKeys = (): string[] => {
    const keys: string[] = [];
    const traverse = (cols: TableColumns[]) => {
      cols.forEach(col => {
        if (col.children && col.children.length > 0) {
          traverse(col.children);
        } else if (col.visible !== false) {
          keys.push(col.key);
        }
      });
    };
    traverse(props.columns);
    return keys;
  };

  const isParentAllChecked = (parent: TableColumns): boolean => {
    if (!parent.children || parent.children.length === 0) return false;
    const availableChildren = parent.children.filter(child => !child.disabled);
    if (availableChildren.length === 0) return false;
    return availableChildren.every(child => checkedKeys.value.includes(child.key));
  };

  const isParentIndeterminate = (parent: TableColumns): boolean => {
    if (!parent.children || parent.children.length === 0) return false;
    const availableChildren = parent.children.filter(child => !child.disabled);
    if (availableChildren.length === 0) return false;
    const checkedChildren = availableChildren.filter(child =>
      checkedKeys.value.includes(child.key)
    );
    return checkedChildren.length > 0 && checkedChildren.length < availableChildren.length;
  };

  const handleParentChange = (parent: TableColumns, checked: boolean) => {
    if (!parent.children || parent.disabled) return;
    const newCheckedKeys = [...checkedKeys.value];
    const childKeys = parent.children.filter(child => !child.disabled).map(child => child.key);
    if (checked) {
      childKeys.forEach(key => {
        if (!newCheckedKeys.includes(key)) {
          newCheckedKeys.push(key);
        }
      });
    } else {
      childKeys.forEach(key => {
        const index = newCheckedKeys.indexOf(key);
        if (index > -1) {
          newCheckedKeys.splice(index, 1);
        }
      });
    }
    checkedKeys.value = newCheckedKeys;
  };

  const handleChildChange = (child: TableColumns, checked: boolean) => {
    if (child.disabled) return;
    const newCheckedKeys = [...checkedKeys.value];
    if (checked) {
      if (!newCheckedKeys.includes(child.key)) {
        newCheckedKeys.push(child.key);
      }
    } else {
      const index = newCheckedKeys.indexOf(child.key);
      if (index > -1) {
        newCheckedKeys.splice(index, 1);
      }
    }
    checkedKeys.value = newCheckedKeys;
  };

  const handleChange = (column: TableColumns, checked: boolean) => {
    if (column.disabled) return;
    const newCheckedKeys = [...checkedKeys.value];
    if (checked) {
      if (!newCheckedKeys.includes(column.key)) {
        newCheckedKeys.push(column.key);
      }
    } else {
      const index = newCheckedKeys.indexOf(column.key);
      if (index > -1) {
        newCheckedKeys.splice(index, 1);
      }
    }
    checkedKeys.value = newCheckedKeys;
  };

  const checkAll = computed({
    get: () => {
      const availableKeys = getAvailableLeafKeys();
      const disabledKeys = getDisabledCheckedKeys();
      const allKeys = [...availableKeys, ...disabledKeys];
      return allKeys.length > 0 && allKeys.every(key => checkedKeys.value.includes(key));
    },
    set: val => {
      if (val) {
        const availableKeys = getAvailableLeafKeys();
        const disabledKeys = getDisabledCheckedKeys();
        checkedKeys.value = [...availableKeys, ...disabledKeys];
      } else {
        checkedKeys.value = getDisabledCheckedKeys();
      }
    },
  });

  const indeterminate = computed(() => {
    const availableKeys = getAvailableLeafKeys();
    const disabledKeys = getDisabledCheckedKeys();
    const allKeys = [...availableKeys, ...disabledKeys];
    if (allKeys.length === 0) return false;
    const checkedCount = checkedKeys.value.filter(key => allKeys.includes(key)).length;
    return checkedCount > 0 && checkedCount < allKeys.length;
  });

  const handleCheckAll = (e: any) => {
    checkAll.value = e.target.checked;
  };

  const handleReset = () => {
    checkedKeys.value = getInitialCheckedKeys();
  };

  const handleCheck = () => {
    const buildVisibleColumns = (columns: TableColumns[]): TableColumns[] => {
      return columns.reduce((result: TableColumns[], column) => {
        if (column.children && column.children.length > 0) {
          const visibleChildren = buildVisibleColumns(column.children);
          if (visibleChildren.length > 0) {
            result.push({
              ...column,
              children: visibleChildren,
            });
          }
        } else {
          if (checkedKeys.value.includes(column.key)) {
            result.push(column);
          }
        }
        return result;
      }, []);
    };
    const visibleColumns = buildVisibleColumns(props.columns);
    emit("change", visibleColumns);
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
    min-width: 220px;
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
    .divider-wrap {
      margin: 4px 0 8px 0;
    }
    .column-tree {
      overflow-y: auto;
      max-height: 320px;
      .flex-column;
      .children-columns {
        .flex-column;
        padding-left: 20px;
        .child-title {
          color: var(--font-text-color);
          font-size: 12px;
        }
      }
    }
  }

  .icon-button {
    width: 32px;
    height: 32px;
  }
</style>
