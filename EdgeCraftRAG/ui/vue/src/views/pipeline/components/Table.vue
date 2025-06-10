<template>
  <div class="table-container">
    <div class="header-wrap">
      <span class="title">{{ $t("pipeline.pipelines") }}</span>
      <div class="btn-wrap">
        <a-config-provider :theme="antTheme.subTheme">
          <a-button
            type="primary"
            :icon="h(CloudUploadOutlined)"
            @click="handleImport()"
            >{{ $t("pipeline.import") }}</a-button
          ></a-config-provider
        >
        <a-button type="primary" @click="handleCreate">
          <template #icon>
            <PlusOutlined />
          </template>
          {{ $t("pipeline.create") }}</a-button
        >
      </div>
    </div>
    <a-table
      :columns="tableColumns"
      :data-source="tableList"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'name'">
          <span @click="handleView(record)" class="click-link">{{
            record.name
          }}</span>
        </template>
        <template v-if="column.dataIndex === 'status'">
          <span>
            <a-tag
              :bordered="false"
              :color="record.status?.active ? 'success' : 'default'"
            >
              {{
                record.status?.active
                  ? $t("pipeline.activated")
                  : $t("pipeline.inactive")
              }}
            </a-tag>
          </span>
        </template>
        <template v-else-if="column.dataIndex === 'operation'">
          <a-space wrap>
            <a-button
              type="primary"
              ghost
              size="small"
              :disabled="record.status?.active"
              @click="handleUpdate(record)"
            >
              {{ $t("common.update") }}</a-button
            >
            <a-button
              v-if="!record.status?.active"
              size="small"
              class="intel-btn-success"
              @click="handleSwitchState(record)"
              >{{ $t("common.active") }}</a-button
            >
            <a-button
              v-if="record.status?.active"
              size="small"
              class="intel-btn-warning"
              @click="handleSwitchState(record)"
              >{{ $t("common.deactivate") }}</a-button
            >
            <a-button
              danger
              size="small"
              :disabled="record.status?.active"
              @click="handleDelete(record)"
              >{{ $t("common.delete") }}
            </a-button>
            <a-button
              v-if="record.status?.active"
              type="primary"
              size="small"
              :icon="h(CommentOutlined)"
              @click="jumpChatbot"
              >{{ $t("common.jump") }}</a-button
            >
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
import {
  requestPipelineDelete,
  requestPipelineSwitchState,
} from "@/api/pipeline";
import router from "@/router";
import { pipelineAppStore } from "@/store/pipeline";
import { antTheme } from "@/utils/antTheme";
import {
  CloseCircleFilled,
  CloudUploadOutlined,
  CommentOutlined,
  PlusOutlined,
} from "@ant-design/icons-vue";
import { Modal } from "ant-design-vue";
import { createVNode, h, ref } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const pipelineStore = pipelineAppStore();

const props = defineProps({
  tableData: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update", "create", "view", "import", "search"]);
const paginationData = reactive<paginationType>({
  total: props.tableData.length || 0,
  pageNum: 1,
  pageSize: 10,
});
const tableColumns = ref<TableColumns[]>([
  {
    title: t("pipeline.name"),
    dataIndex: "name",
    width: "25%",
  },
  {
    title: t("pipeline.id"),
    dataIndex: "idx",
    width: "25%",
    ellipsis: true,
  },
  {
    title: t("pipeline.status"),
    dataIndex: "status",
    width: "20%",
  },
  {
    title: t("pipeline.operation"),
    dataIndex: "operation",
    width: "30%",
    fixed: "right",
  },
]);
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
//activate/deactivate
const handleSwitchState = (row: EmptyObjectType) => {
  const { active } = row?.status;

  const text = active ? t("pipeline.deactivateTip") : t("pipeline.activeTip");
  Modal.confirm({
    title: t("common.prompt"),
    content: text,
    okText: t("common.confirm"),
    async onOk() {
      await requestPipelineSwitchState(row.name, { active: !active });
      pipelineStore.setPipelineActivate(active ? "" : row.name);
      emit("search");
    },
  });
};
//delete
const handleDelete = (row: EmptyObjectType) => {
  Modal.confirm({
    title: t("common.delete"),
    icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
    content: t("pipeline.deleteTip"),
    okText: t("common.confirm"),
    okType: "danger",
    async onOk() {
      await requestPipelineDelete(row.name);
      paginationData.pageNum = 1;
      emit("search");
    },
  });
};

//import
const handleImport = () => {
  emit("import");
};
//Jump Chatbot
const jumpChatbot = () => {
  router.push("/chatbot");
};

watch(
  () => props.tableData,
  (tableData) => {
    const activatedPipeline: EmptyObjectType =
      tableData?.find((item: any) => item.status?.active) || {};

    const { name = "" } = activatedPipeline;
    pipelineStore.setPipelineActivate(name);
  },
  { immediate: true, deep: true }
);
</script>

<style scoped lang="less">
.table-container {
  .p-16;
  .pb-24;
  .mt-20;
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
</style>
