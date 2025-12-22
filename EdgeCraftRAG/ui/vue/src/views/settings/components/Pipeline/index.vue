<template>
  <div class="pipeline-container">
    <Table
      :loading
      :table-data="tableData"
      @create="handleCreate"
      @update="handleUpdate"
      @view="handleView"
      @import="handleImport"
      @search="handleSearch"
    />
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
      :dialog-id="editDialog.id"
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
  </div>
</template>

<script lang="ts" setup name="Pipeline">
  import { getPipelineDetailById, getPipelineList } from "@/api/pipeline";
  import { onMounted, reactive, ref } from "vue";
  import { CreateDialog, DetailDrawer, EditDialog, ImportDialog, Table } from "./components";

  const loading = ref<boolean>(true);
  const createDialog = reactive<DialogType>({
    visible: false,
  });
  const editDialog = reactive<DialogType>({
    visible: false,
    id: "",
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
    try {
      loading.value = true;
      const data: any = await getPipelineList();
      tableData.value = [].concat(data);
    } catch (error) {
      console.log(error);
    } finally {
      loading.value = false;
    }
  };

  //create
  const handleCreate = () => {
    createDialog.visible = true;
  };
  //edit
  const handleUpdate = async (row: EmptyObjectType) => {
    const data: any = await getPipelineDetailById(row.idx);
    editDialog.id = row.idx;
    editDialog.data = JSON.parse(data);
    editDialog.visible = true;
  };
  //detail
  const handleView = async (row: EmptyObjectType) => {
    const data: any = await getPipelineDetailById(row.idx);

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

  onMounted(() => {
    queryPipelineList();
  });
</script>

<style scoped lang="less">
  .pipeline-container {
    // .mt-24;
  }
</style>
