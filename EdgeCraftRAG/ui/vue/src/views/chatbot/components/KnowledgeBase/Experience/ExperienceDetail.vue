<template>
  <div class="experience-container">
    <div class="table-container">
      <div class="header-wrap">
        <span class="title"></span>
        <div class="btn-wrap">
          <a-config-provider :theme="antTheme.subTheme">
            <a-button
              type="primary"
              :icon="h(CloudUploadOutlined)"
              @click="handleImport()"
              >{{ $t("experience.import") }}</a-button
            >
          </a-config-provider>
          <a-button type="primary" @click="handleCreate()">
            <template #icon>
              <PlusOutlined />
            </template>
            {{ $t("experience.create") }}</a-button
          >
        </div>
      </div>
      <a-table
        :columns="tableColumns"
        :data-source="tableList"
        :pagination="false"
        :row-key="(record) => record?.question"
      >
        <template #expandColumnTitle>
          <div class="expand-column">{{ $t("experience.detail") }}</div>
        </template>
        <template #expandedRowRender="{ record }">
          <p v-for="(item, index) in record.content" class="experience-item">
            {{ index + 1 }}.
            {{ item }}
          </p>
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'operation'">
            <a-space wrap>
              <a-button
                type="primary"
                ghost
                size="small"
                :icon="h(EditFilled)"
                :disabled="record.status?.active"
                @click="handleUpdate(record)"
              >
                {{ $t("common.update") }}</a-button
              >
              <a-button
                danger
                size="small"
                :icon="h(DeleteFilled)"
                :disabled="record.status?.active"
                @click="handleDelete(record)"
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
      <!-- UpdateDialog -->
      <UpdateDialog
        v-if="updateDialog.visible"
        :dialog-data="updateDialog.data"
        :dialog-type="updateDialog.type"
        @search="handleSearch"
        @close="updateDialog.visible = false"
      />
      <!-- importDialog -->
      <ImportDialog
        v-if="importDialog.visible"
        @close="importDialog.visible = false"
        @search="handleSearch"
      />
    </div>
  </div>
</template>

<script lang="ts" setup name="ExperienceDetail">
import { createVNode, h, ref, onMounted } from "vue";
import { antTheme } from "@/utils/antTheme";
import {
  CloseCircleFilled,
  CloudUploadOutlined,
  PlusOutlined,
  EditFilled,
  DeleteFilled,
} from "@ant-design/icons-vue";
import { Modal } from "ant-design-vue";
import {
  getExperienceDetailByName,
  getExperienceList,
  requestExperienceDelete,
} from "@/api/knowledgeBase";
import { UpdateDialog, ImportDialog } from "./index.ts";
import { useI18n } from "vue-i18n";
import eventBus from "@/utils/mitt";

const { t } = useI18n();
const tableData = ref<EmptyArrayType>([]);
const tableColumns = computed<EmptyArrayType>(() => [
  {
    title: t("experience.label.experience"),
    dataIndex: "question",
    ellipsis: true,
  },
  {
    title: t("experience.operation"),
    dataIndex: "operation",
    width: "180px",
    fixed: "right",
  },
]);

const paginationData = reactive<paginationType>({
  total: 0,
  pageNum: 1,
  pageSize: 10,
});
const updateDialog = reactive<DialogType>({
  visible: false,
  type: "create",
  data: [],
});
const importDialog = reactive<DialogType>({
  visible: false,
});
const tableList = computed(() => {
  const { pageNum, pageSize } = paginationData;
  const start = (pageNum - 1) * pageSize;
  const end = start + pageSize;
  return tableData.value.slice(start, end);
});
const queryExperienceList = async () => {
  const data: any = await getExperienceList();

  tableData.value = [].concat(data || []);
};
//create
const handleCreate = () => {
  updateDialog.type = "create";
  updateDialog.data = [];
  updateDialog.visible = true;
};
//edit
const handleUpdate = async (row: EmptyObjectType) => {
  const { question } = row;
  const data: any = await getExperienceDetailByName({ question });

  updateDialog.type = "edit";
  updateDialog.data = [data];
  updateDialog.visible = true;
};
//import
const handleImport = () => {
  importDialog.visible = true;
};
//delete
const handleDelete = (row: EmptyObjectType) => {
  Modal.confirm({
    title: t("common.delete"),
    icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
    content: t("experience.deleteTip"),
    okText: t("common.confirm"),
    okType: "danger",
    async onOk() {
      const { question } = row;
      await requestExperienceDelete({ question });
      paginationData.pageNum = 1;
      handleSearch();
    },
  });
};

//search
const handleSearch = () => {
  queryExperienceList();
  eventBus.emit("refresh");
};
onMounted(() => {
  queryExperienceList();
});
</script>

<style scoped lang="less">
.experience-container {
  padding: 24px;
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
    .experience-item {
      color: var(--font-text-color);
      .pl-8;
    }
    .expand-column {
      width: 80px;
    }
  }
}
</style>
