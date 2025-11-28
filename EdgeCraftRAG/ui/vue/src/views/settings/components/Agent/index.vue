<template>
  <div class="agent-container">
    <Table
      :loading
      :table-data="tableData"
      @create="handleCreate"
      @search="handleSearch"
      @update="handleUpdate"
    />
    <!-- updateDialog -->
    <UpdateDialog
      v-if="updateDialog.visible"
      :dialog-data="updateDialog.data"
      :dialog-type="updateDialog.type"
      @search="handleSearch"
      @close="updateDialog.visible = false"
    />
  </div>
</template>

<script lang="ts" setup name="Agent">
import { getAgentList, getAgentDetailByName } from "@/api/agent";
import { onMounted, reactive, ref } from "vue";
import { UpdateDialog, Table } from "./components";

const loading = ref<boolean>(true);
const updateDialog = reactive<DialogType>({
  visible: false,
  data: {},
  type: "create",
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
  const data: any = await getAgentDetailByName(row.name);
  updateDialog.data = { ...updateDialog.data, ...data };
  updateDialog.visible = true;
  updateDialog.type = "edit";
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
  .mt-24;
}
</style>
