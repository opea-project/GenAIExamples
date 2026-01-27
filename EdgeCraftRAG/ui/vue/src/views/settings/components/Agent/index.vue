<template>
  <div class="agent-container">
    <Table
      :loading
      :table-data="tableData"
      @create="handleCreate"
      @search="handleSearch"
      @update="handleUpdate"
      @view="handleView"
    />
    <!-- updateDialog -->
    <UpdateDialog
      v-if="updateDialog.visible"
      :dialog-data="updateDialog.data"
      :dialog-type="updateDialog.type"
      @search="handleSearch"
      @close="updateDialog.visible = false"
    />
    <!-- detailDrawer -->
    <DetailDrawer
      v-if="detailDrawer.visible"
      :drawer-data="detailDrawer.data"
      @viewPipeline="handlePipelineView"
      @close="detailDrawer.visible = false"
    />
    <!-- detailDrawer -->
    <PipelineDetailDrawer
      v-if="pipelineDetailDrawer.visible"
      :drawer-data="pipelineDetailDrawer.data"
      @close="pipelineDetailDrawer.visible = false"
    />
  </div>
</template>

<script lang="ts" setup name="Agent">
import { getAgentDetailByName, getAgentList } from "@/api/agent";
import { getPipelineDetailById } from "@/api/pipeline";
import { onMounted, reactive, ref } from "vue";
import {
  DetailDrawer,
  PipelineDetailDrawer,
  Table,
  UpdateDialog,
} from "./components";

const loading = ref<boolean>(true);
const updateDialog = reactive<DialogType>({
  visible: false,
  data: {},
  type: "create",
});

const detailDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});
const pipelineDetailDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});
const tableData = ref<EmptyArrayType>([]);

const queryAgentList = async () => {
  try {
    loading.value = true;
    const data: any = await getAgentList();
    tableData.value = Object.values(data);
  } catch (error) {
    console.log(error);
  } finally {
    loading.value = false;
  }
};

//create
const handleCreate = () => {
  updateDialog.visible = true;
  updateDialog.type = "create";
  updateDialog.data = {};
};
//edit
const handleUpdate = async (row: EmptyObjectType) => {
  try {
    const data: any = await getAgentDetailByName(row.name);
    updateDialog.data = { ...updateDialog.data, ...data };
    updateDialog.visible = true;
    updateDialog.type = "edit";
  } catch (error) {
    console.log(error);
  }
};
//detail
const handleView = async (row: EmptyObjectType) => {
  try {
    const data: any = await getAgentDetailByName(row.name);

    detailDrawer.data = { ...detailDrawer.data, ...data };
    detailDrawer.visible = true;
  } catch (error) {
    console.log(error);
  }
};
//pipeline detail
const handlePipelineView = async (row: EmptyObjectType) => {
  try {
    const data: any = await getPipelineDetailById(row.pipeline_idx);

    pipelineDetailDrawer.data = JSON.parse(data);
    pipelineDetailDrawer.visible = true;
  } catch (error) {
    console.log(error);
  }
};

//search
const handleSearch = () => {
  queryAgentList();
};

onMounted(() => {
  queryAgentList();
});
</script>

<style scoped lang="less">
.agent-container {
  // .mt-24;
}
</style>
