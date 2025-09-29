<template>
  <a-modal
    v-model:open="modelVisible"
    width="500px"
    centered
    destroyOnClose
    :title="$t('pipeline.import')"
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
      :before-upload="handleBeforeUpload"
      @change="handleChange"
    >
      <SvgIcon
        name="icon-cloudupload-fill"
        :size="40"
        :style="{ color: 'var(--color-primary)' }"
      />
      <p class="intel-upload-text">{{ $t("common.uploadTip") }}</p>
      <p class="intel-upload-hint">
        {{ $t("pipeline.pipelineFormatTip") }}
      </p>
      <a-button type="primary" class="mt-12">{{
        $t("common.import")
      }}</a-button>
    </a-upload-dragger>
  </a-modal>
</template>

<script lang="ts" setup name="ImportDialog">
import { importUrl } from "@/api/pipeline";
import { ref } from "vue";
import { useNotification } from "@/utils/common";
import { NextLoading } from "@/utils/loading";
import { useI18n } from "vue-i18n";
import { message, UploadProps } from "ant-design-vue";

const { t } = useI18n();
const { antNotification } = useNotification();

const emit = defineEmits(["search", "close"]);
const modelVisible = ref<boolean>(true);
const fileList = ref([]);

const handleBeforeUpload = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 10;

  if (!isFileSize) {
    message.error(t("pipeline.pipelineFormatTip"));
    return;
  }

  return isFileSize;
};
const handleChange = (info: any) => {
  const el = <HTMLElement>document.querySelector(".loading-next");
  if (!el) NextLoading.start();
  try {
    const status = info.file.status;

    if (status === "done") {
      emit("search");
      handleClose();
      NextLoading.done();
      antNotification(
        "success",
        t("common.success"),
        t("pipeline.importSuccTip")
      );
    } else if (status === "error") {
      NextLoading.done();
      antNotification("error", t("common.error"), t("pipeline.importErrTip"));
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
