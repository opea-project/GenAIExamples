<template>
  <div class="setting-container">
    <a-affix :offset-top="450">
      <div class="chatbot-wrap" @click="jumpChatbot">
        <SvgIcon
          name="icon-chatbot"
          :size="40"
          :style="{ color: 'var(--color-big-icon)' }"
          inherit
        />
        <div>{{ $t("common.chatbot") }}</div>
      </div></a-affix
    >
    <!-- system status -->
    <System />
    <!-- pipelines list -->
    <Table
      :table-data="tableData"
      @create="handleCreate"
      @update="handleUpdate"
      @view="handleView"
      @import="handleImport"
      @search="handleSearch"
    />
    <!-- configuration -->
    <!-- <Configuration :json-data="jsonData" /> -->
    <!-- createDialog -->
    <CreateDialog
      v-if="createDialog.visible"
      @search="handleSearch"
      @close="createDialog.visible = false"
    />
    <!-- editDialog -->
    <EditDialog
      v-if="editDialog.visible"
      :dialog-data="editDialog.data"
      @search="handleSearch"
      @close="editDialog.visible = false"
    />
    <!-- detailDrawer -->
    <DetailDrawer
      v-if="detailDrawer.visible"
      :drawer-data="detailDrawer.data"
      @close="detailDrawer.visible = false"
    />
    <!-- importDialog -->
    <ImportDialog
      v-if="importDialog.visible"
      @close="importDialog.visible = false"
      @search="handleSearch"
    />
    <!-- QuickStart -->
    <QuickStart @create="handleCreate" />
  </div>
</template>

<script lang="ts" setup name="xxx">
import { getPipelineDetialByName, getPipelineList } from "@/api/pipeline";
import router from "@/router";
import { pipelineAppStore } from "@/store/pipeline";
import { useNotification } from "@/utils/common";
import { onMounted, reactive, ref } from "vue";
import {
  CreateDialog,
  DetailDrawer,
  EditDialog,
  ImportDialog,
  QuickStart,
  System,
  Table,
} from "./components";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const { antNotification } = useNotification();
const pipelineStore = pipelineAppStore();
const createDialog = reactive<DialogType>({
  visible: false,
});
const editDialog = reactive<DialogType>({
  visible: false,
  data: {},
});
const detailDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});
const importDialog = reactive<DialogType>({
  visible: false,
});

const tableData = ref<EmptyArrayType>([]);

const queryPipelineList = async () => {
  const data: any = await getPipelineList();

  tableData.value = [].concat(data);
};

//create
const handleCreate = () => {
  createDialog.visible = true;
};
//edit
const handleUpdate = async (row: EmptyObjectType) => {
  const data: any = await getPipelineDetialByName(row.name);

  editDialog.data = JSON.parse(data);
  editDialog.visible = true;
};
//detail
const handleView = async (row: EmptyObjectType) => {
  const data: any = await getPipelineDetialByName(row.name);

  detailDrawer.data = JSON.parse(data);
  detailDrawer.visible = true;
};
//search
const handleSearch = () => {
  queryPipelineList();
};
//import
const handleImport = () => {
  importDialog.visible = true;
};
//Jump Chatbot
const jumpChatbot = () => {
  if (pipelineStore.activatedPipeline) {
    router.push("/chatbot");
  } else {
    antNotification(
      "warning",
      t("common.prompt"),
      t("pipeline.notActivatedTip")
    );
  }
};
onMounted(() => {
  queryPipelineList();
});
</script>

<style scoped lang="less">
.setting-container {
  position: relative;

  .chatbot-wrap {
    padding: 12px 8px;
    position: absolute;
    transform: translateY(-50%);
    top: 40%;
    left: -80px;
    z-index: 99;
    background-color: var(--bg-content-color);
    box-shadow: 0px 2px 4px 0px var(--bg-box-shadow);
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: var(--font-main-color);
    &:hover {
      color: var(--color-primary);
    }
  }
  @media (max-width: 1100px) {
    .chatbot-wrap {
      left: 0;
    }
  }
}
</style>
