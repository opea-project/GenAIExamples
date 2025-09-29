<template>
  <a-modal
    v-model:open="modelVisible"
    width="500px"
    centered
    destroyOnClose
    :title="$t('experience.import')"
    :keyboard="false"
    :maskClosable="false"
    :footer="null"
    @cancel="handleClose"
    class="import-dialog"
  >
    <a-upload-dragger
      v-model:fileList="fileList"
      name="file"
      :action="uploadFileApi"
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
        {{ $t("experience.fileFormatTip") }}
      </p>
      <a-button type="primary" class="mt-12">{{
        $t("common.import")
      }}</a-button>
    </a-upload-dragger>
  </a-modal>
</template>

<script lang="ts" setup name="ImportDialog">
import { requestExperienceRelation, uploadFileUrl } from "@/api/knowledgeBase";
import { ref, inject } from "vue";
import { useNotification } from "@/utils/common";
import { NextLoading } from "@/utils/loading";
import { useI18n } from "vue-i18n";
import { message, UploadProps } from "ant-design-vue";

const { t } = useI18n();
const { antNotification } = useNotification();

interface KbType {
  name: string;
}
const emit = defineEmits(["search", "close"]);
const kbInfo = inject<KbType>("kbInfo");
const modelVisible = ref<boolean>(true);
const fileList = ref([]);
const uploadFileApi = computed(() => {
  return uploadFileUrl + kbInfo?.name;
});
const handleBeforeUpload = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 100;

  if (!isFileSize) {
    message.error(t("experience.uploadValid"));
    return;
  }

  return isFileSize;
};
const handleChange = async (info: any) => {
  const el = <HTMLElement>document.querySelector(".loading-next");
  if (!el) NextLoading.start();
  try {
    const { response, status } = info.file;

    if (status === "done") {
      const { name = "" } = kbInfo;
      await requestExperienceRelation({
        name,
        local_path: response,
      });
      emit("search");
      handleClose();
      NextLoading.done();
    } else if (status === "error") {
      NextLoading.done();
      antNotification("error", t("common.error"), t("experience.importErrTip"));
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
