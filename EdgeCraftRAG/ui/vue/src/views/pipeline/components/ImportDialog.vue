<template>
  <a-modal
    v-model:open="modelVisible"
    width="500px"
    centered
    destroyOnClose
    title="Import Pipeline"
    :keyboard="false"
    :maskClosable="false"
    :footer="null"
    @cancel="handleClose"
    class="import-dialog"
  >
    <a-upload-dragger
      v-model:fileList="fileList"
      name="file"
      :action="importUrl"
      accept=".json"
      :showUploadList="false"
      @change="handleChange"
    >
      <SvgIcon
        name="icon-cloudupload-fill"
        :size="40"
        :style="{ color: 'var(--color-primary)' }"
      />
      <p class="intel-upload-text">Click or drag file to this area to upload</p>
      <p class="intel-upload-hint">
        Supports JSON format, with file size not exceeding 10M.
      </p>
      <a-button type="primary" class="mt-12">Import</a-button>
    </a-upload-dragger>
  </a-modal>
</template>

<script lang="ts" setup name="ImportDialog">
import { importUrl } from "@/api/pipeline";
import { ref } from "vue";
import { useNotification } from "@/utils/common";
import { NextLoading } from "@/utils/loading";

const { antNotification } = useNotification();

const emit = defineEmits(["search", "close"]);
const modelVisible = ref<boolean>(true);
const fileList = ref([]);

const handleChange = (info: any) => {
  const el = <HTMLElement>document.querySelector(".loading-next");
  if (!el) NextLoading.start();
  try {
    const status = info.file.status;

    if (status === "done") {
      emit("search");
      handleClose();
      NextLoading.done();
      antNotification("success", "Success", "Files upload successful!");
    } else if (status === "error") {
      NextLoading.done();
      antNotification("error", "Error", "Files upload failed!");
    }
  } catch (error) {
    console.error(error);
    if (NextLoading) NextLoading.done();
  }
};

const handleClose = () => {
  emit("close");
};
</script>

<style scoped lang="less"></style>
