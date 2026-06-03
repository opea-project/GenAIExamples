<template>
  <div class="table-container">
    <div class="header-wrap">
      <span class="title">{{ $t("agent.agent") }}</span>
      <div class="btn-wrap">
        <a-button type="primary" @click="handleCreate">
          <template #icon>
            <PlusOutlined />
          </template>
          {{ $t("agent.create") }}</a-button
        >
      </div>
    </div>
    <a-table
      :columns="tableColumns"
      :data-source="tableList"
      :pagination="false"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'name'">
          <span @click="handleView(record)" class="click-link">{{ record.name }}</span>
        </template>
        <template v-if="column.dataIndex === 'type'">
          {{ getEnumField(AgentType, record.type) }}
        </template>
        <template v-if="column.dataIndex === 'active'">
          <span>
            <a-tag :bordered="false" :color="record.active ? 'success' : 'default'">
              {{ record.active ? $t("agent.activated") : $t("agent.inactive") }}
            </a-tag>
          </span>
        </template>
        <template v-if="column.dataIndex === 'configs'">
          <span v-if="!Object.keys(record?.configs || {}).length">--</span>
          <div class="tag-wrap" v-else>
            <a-popover placement="rightBottom">
              <FileSearchOutlined class="detail-icon" />
              <template #content>
                <div class="configs-wrap">
                  <div class="title-wrap">
                    <span>{{ $t("agent.label.configs") }}</span>
                    <a-tooltip placement="top" :title="$t('common.copy')">
                      <span class="icon-style" @click="handleCopyResponses(record?.configs)">
                        <CopyOutlined /></span
                    ></a-tooltip>
                  </div>
                  <div class="json-wrap">
                    <JsonPretty
                      :data="record?.configs"
                      :theme="currentTheme"
                      :show-toggle="false"
                    />
                  </div>
                </div>
              </template>
            </a-popover>
          </div>
        </template>
        <template v-else-if="column.dataIndex === 'operation'">
          <a-space class="operation-actions">
            <a-button
              type="primary"
              ghost
              size="small"
              :disabled="record.active"
              @click="handleUpdate(record)"
            >
              {{ $t("common.update") }}</a-button
            >
            <a-button
              v-if="!record.active"
              size="small"
              class="intel-btn-success"
              @click="handleSwitchState(record)"
              >{{ $t("common.active") }}</a-button
            >
            <a-button
              v-if="record.active"
              size="small"
              class="intel-btn-warning"
              @click="handleSwitchState(record)"
              >{{ $t("common.deactivate") }}</a-button
            >
            <a-button danger size="small" :disabled="record.active" @click="handleDelete(record)"
              >{{ $t("common.delete") }}
            </a-button>
          </a-space>
        </template>
      </template>
    </a-table>
    <a-pagination
      v-if="paginationData.total > 10"
      v-model:current="paginationData.pageNum"
      v-model:pageSize="paginationData.pageSize"
      showSizeChanger
      :total="paginationData.total"
      :show-total="total => `${$t('common.total')}: ${total}`"
    />
  </div>
</template>

<script lang="ts" setup name="Table">
  import { requestAgentDelete, requestAgentSetActive } from "@/api/agent";
  import { themeAppStore } from "@/store/theme";
  import { useClipboard } from "@/utils/clipboard";
  import { getEnumField } from "@/utils/common";
  import {
    CloseCircleFilled,
    CopyOutlined,
    FileSearchOutlined,
    PlusOutlined,
  } from "@ant-design/icons-vue";
  import { Modal } from "ant-design-vue";
  import { createVNode } from "vue";
  import { useI18n } from "vue-i18n";
  import JsonPretty from "vue-json-pretty";
  import "vue-json-pretty/lib/styles.css";
  import getTableColumns from "../columnsList";
  import { AgentType } from "../enum";

  const themeStore = themeAppStore();
  const { t } = useI18n();
  const { copy } = useClipboard();

  const props = defineProps({
    tableData: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Boolean,
      default: false,
    },
  });

  const emit = defineEmits(["create", "update", "search", "view"]);
  const paginationData = reactive<PaginationType>({
    total: 0,
    pageNum: 1,
    pageSize: 10,
  });
  const tableColumns = computed(() => getTableColumns(t));
  const tableList = computed(() => {
    const { pageNum, pageSize } = paginationData;
    const start = (pageNum - 1) * pageSize;
    const end = start + pageSize;
    return props.tableData.slice(start, end);
  });
  const currentTheme = computed(() => {
    return themeStore.theme;
  });
  //create
  const handleCreate = () => {
    emit("create");
  };
  //edit
  const handleUpdate = (row: EmptyObjectType) => {
    emit("update", row);
  };
  //activate / deactivate
  const handleSwitchState = (row: EmptyObjectType) => {
    const willActivate = !row.active;
    const text = willActivate ? t("agent.activeTip") : t("agent.deactivateTip");
    Modal.confirm({
      title: t("common.prompt"),
      content: text,
      okText: t("common.confirm"),
      async onOk() {
        await requestAgentSetActive(row.name, willActivate);
        emit("search");
      },
    });
  };
  //detail
  const handleView = (row: EmptyObjectType) => {
    emit("view", row);
  };
  //delete
  const handleDelete = (row: EmptyObjectType) => {
    Modal.confirm({
      title: t("common.delete"),
      icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
      content: t("agent.deleteTip"),
      okText: t("common.confirm"),
      okType: "danger",
      async onOk() {
        await requestAgentDelete(row.name);
        paginationData.pageNum = 1;
        emit("search");
      },
    });
  };
  const handleCopyResponses = async (configs: EmptyObjectType) => {
    console.log(configs);
    await copy(JSON.stringify(configs));
  };
  watch(
    () => props.tableData,
    newData => {
      paginationData.total = newData.length;
    },
    { immediate: true }
  );
</script>

<style scoped lang="less">
  .table-container {
    .p-16;
    .pb-24;
    border-radius: 8px;
    background-color: var(--bg-content-color);

    .header-wrap {
      .flex-between;
      .mb-20;
    }
    .title {
      .fs-16;
      font-weight: 600;
      color: var(--font-main-color);
    }
    .btn-wrap {
      display: flex;
      gap: 12px;
    }
    .intel-tag {
      border-radius: 10px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      line-height: 18px;
    }
    .tag-wrap {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .tag-item {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  .click-link {
    color: var(--color-primary);
    cursor: pointer;
    transition: color 0.3s;
    &:hover {
      color: var(--color-primary-hover);
      text-decoration: underline;
    }
  }

  :deep(.operation-actions) {
    flex-wrap: nowrap;
    white-space: nowrap;
  }

  .not-configs {
    padding: 16px 0;
    width: 100%;
    :deep(.intel-empty-image) {
      height: 60px;
    }
  }
  .detail-icon {
    font-size: 16px;
    cursor: pointer;
    color: var(--color-primary-hover);
    &:hover {
      color: var(--color-primary-second);
    }
  }
  .configs-wrap {
    .flex-column;
    width: 600px;
    gap: 12px;
    max-height: 450px;
    .title-wrap {
      .flex-between;
      .pb-8;
      border-bottom: 1px solid var(--border-main-color);
      font-weight: 500;
      color: var(--font-main-color);

      .icon-style {
        cursor: pointer;
        &:hover {
          color: var(--color-primary-hover);
        }
      }
    }
    .json-wrap {
      flex: 1;
      overflow-y: auto;
    }
  }
  :deep(.vjs-tree) {
    .vjs-value-string {
      color: var(--color-success);
    }
  }
</style>
