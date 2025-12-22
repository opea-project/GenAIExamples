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
      :scroll="{ x: 'max-content' }"
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
            <a-tag v-for="(value, key) in record?.configs" color="processing" class="tag-item">
              {{ key }}: {{ value }}
            </a-tag>
          </div>
        </template>
        <template v-else-if="column.dataIndex === 'operation'">
          <a-space wrap>
            <a-button
              type="primary"
              ghost
              size="small"
              :disabled="record.active"
              @click="handleUpdate(record)"
            >
              {{ $t("common.update") }}</a-button
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
    />
  </div>
</template>

<script lang="ts" setup name="Table">
  import { requestAgentDelete } from "@/api/agent";
  import { getEnumField } from "@/utils/common";
  import { CloseCircleFilled, PlusOutlined } from "@ant-design/icons-vue";
  import { Modal } from "ant-design-vue";
  import { createVNode } from "vue";
  import { useI18n } from "vue-i18n";
  import getTableColumns from "../columnsList";
  import { AgentType } from "../enum";

  const { t } = useI18n();

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
  const paginationData = reactive<paginationType>({
    total: props.tableData.length || 0,
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
  //create
  const handleCreate = () => {
    emit("create");
  };
  //edit
  const handleUpdate = (row: EmptyObjectType) => {
    emit("update", row);
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
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 8px;
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

  .custom-benchmark {
    position: absolute;
    top: -40px;
    height: 36px;
    z-index: 20;

    .container {
      padding: 8px 16px;
    }

    h2 {
      font-size: 14px;
      padding: 0;
      font-weight: 500;
      color: #595959;
      justify-content: end;
    }
  }
  .not-configs {
    padding: 16px 0;
    width: 100%;
    :deep(.intel-empty-image) {
      height: 60px;
    }
  }
</style>
