<template>
  <div class="detail-wrap">
    <div class="upload-wrap">
      <a-upload-dragger
        v-model:file-list="uploadFileList"
        name="file"
        multiple
        :showUploadList="false"
        accept=".csv,.doc,.docx,.enex,.epub,.html,.md,.odt,.pdf,.ppt,.pptx,.txt,.zip"
        :before-upload="handleBeforeUpload"
        :custom-request="customRequest"
      >
        <SvgIcon
          name="icon-cloudupload-fill"
          :size="50"
          :style="{ color: 'var(--font-tip-color)' }"
        />
        <p class="upload-text">{{ $t("common.uploadTip") }}</p>
        <div class="upload-tip">
          <p>
            {{ $t("knowledge.uploadTip") }}
          </p>
        </div>
      </a-upload-dragger>
    </div>
    <div class="tip-wrap" v-if="startUpload">
      <div class="tip-text">
        <ExclamationCircleFilled :style="{ fontSize: '14px' }" />
        <span>{{ $t("knowledge.waitTip") }}</span>
      </div>
      <div class="rated-wrap slider-wrap">
        <span>{{ $t("knowledge.done") }}:</span>
        <a-slider
          v-model:value="uploadedCount"
          :min="0"
          :max="totalFiles"
          disabled
        /><span
          >{{ uploadedCount }}/{{ totalFiles }}
          <span class="pl-8">
            {{ $t("knowledge.successfully") }}:
            <span class="is-success">{{ successCount }}</span>
            {{ $t("knowledge.failed") }}:
            <span class="is-failed">{{ failCount }}</span></span
          >
        </span>
      </div>
    </div>
    <PartialLoading :visible="loading" />
    <template v-if="!loading">
      <a-empty v-if="notFile" :description="$t('knowledge.notFileTip')" />
      <div class="files-container" v-else>
        <a-row type="flex" wrap :gutter="[20, 20]">
          <a-col
            :span="8"
            v-for="[key, value] in Object.entries(knowledgeData.file_map)"
            :key="key"
          >
            <div class="file-item">
              <div class="left-wrap">
                <FileDoneOutlined
                  :style="{
                    color: 'var(--color-success)',
                    fontSize: '20px',
                  }"
                />
                <a-tooltip placement="topLeft" :title="key">
                  <div class="file-name">{{ key }}</div>
                </a-tooltip>
              </div>
              <div class="right-wrap">
                <a-tooltip placement="top" :title="$t('common.delete')">
                  <DeleteFilled
                    class="delete-icon"
                    @click="handleFileDelete(value as string)"
                  />
                </a-tooltip>
              </div>
            </div>
          </a-col>
        </a-row></div
    ></template>
  </div>
</template>

<script setup lang="ts" name="KnowledgeBaseDetail">
import { ref, reactive, createVNode, inject, onMounted, computed } from "vue";
import JSZip from "jszip";
import {
  requestKnowledgeBaseRelation,
  getKnowledgeBaseDetailByName,
  requestFileDelete,
  requestUploadFileUrl,
} from "@/api/knowledgeBase";
import {
  CloseCircleFilled,
  DeleteFilled,
  FileDoneOutlined,
  ExclamationCircleFilled,
} from "@ant-design/icons-vue";
import { message, Modal, UploadFile, UploadProps } from "ant-design-vue";
import { useI18n } from "vue-i18n";
import eventBus from "@/utils/mitt";
import type { UploadRequestOption } from "ant-design-vue/lib/upload/interface";
import { useNotification } from "@/utils/common";

interface KbType {
  name: string;
}
const { t } = useI18n();
const { antNotification } = useNotification();

const kbInfo = inject<KbType>("kbInfo");
const uploadFileList = ref<UploadFile[]>([]);
const knowledgeData = reactive<EmptyObjectType>({});
const pendingFiles = ref<UploadRequestOption[]>([]);
let isUploading = ref<boolean>(false);
const totalFiles = ref<number>(0);
const uploadedCount = ref<number>(0);
const successCount = ref<number>(0);
const failCount = ref<number>(0);
const startUpload = ref<boolean>(false);
const loading = ref<boolean>(false);

const notFile = computed(() => {
  const { file_map = {} } = knowledgeData;
  return Object.keys(file_map).length === 0;
});

const queryKnowledgeBaseDetail = async () => {
  getKnowledgeBaseDetailByName(kbInfo?.name!)
    .then((data: any) => {
      Object.assign(knowledgeData, data);
    })
    .catch((error: any) => {
      console.error(error);
    })
    .finally(() => {
      loading.value = false;
    });
};

const handleBeforeUpload = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 200;
  if (!isFileSize) {
    antNotification("error", t("common.error"), t("knowledge.uploadValid"));

    return;
  }
  return isFileSize;
};

const handleZipParse = async (options: UploadRequestOption) => {
  const origFile = options.file as File;
  try {
    const arrayBuffer = await origFile.arrayBuffer();
    const zip = await JSZip.loadAsync(arrayBuffer);
    const entries: JSZip.JSZipObject[] = [];
    zip.forEach((relativePath, fileEntry) => {
      entries.push(fileEntry);
    });

    const fileEntries = entries.filter((e) => !e.dir);

    if (fileEntries.length === 0) {
      antNotification("error", t("common.error"), t("knowledge.zipNoFiles"));
      return;
    }

    const innerPromises = fileEntries.map(async (entry) => {
      const blob = await entry.async("blob");

      const filename = entry.name.split("/").pop() || entry.name;
      const innerFile = new File([blob], filename, {
        type: blob.type || "application/octet-stream",
      });

      const newOption: UploadRequestOption = {
        ...options,
        file: innerFile,
        uid: `${(options as any).uid || Date.now()}_${filename}`,
      } as UploadRequestOption;

      return newOption;
    });

    const innerOptions = await Promise.all(innerPromises);

    innerOptions.forEach((opt: any) => pendingFiles.value.push(opt));

    totalFiles.value += innerOptions.length;
  } catch (err) {
    console.error(err);
  }
};

const customRequest = async (options: UploadRequestOption) => {
  const file = options.file as File;
  const fileName = file && file.name ? file.name.toLowerCase() : "";

  if (fileName.endsWith(".zip")) {
    startUpload.value = true;
    await handleZipParse(options);

    if (!isUploading.value) {
      isUploading.value = true;
      uploadInBatches();
    }
    return;
  }

  pendingFiles.value.push(options);
  totalFiles.value += 1;
  startUpload.value = true;

  if (!isUploading.value) {
    isUploading.value = true;
    uploadInBatches();
  }
};

const uploadInBatches = async () => {
  while (pendingFiles.value.length > 0) {
    const batch = pendingFiles.value.splice(0, 20);

    await Promise.all(
      batch.map(async (options: any) => {
        const { file, onSuccess, onError } = options;
        const uploadFile = file as UploadFile;

        try {
          const { name } = knowledgeData;
          const res = await requestUploadFileUrl(name, { file });
          await requestKnowledgeBaseRelation(name, { local_path: res });

          onSuccess?.(res, uploadFile as any);
          handleSuccess(uploadFile);
          successCount.value += 1;
        } catch (err: any) {
          onError?.(err);
          failCount.value += 1;
        } finally {
          uploadedCount.value += 1;
        }
      })
    );
    queryKnowledgeBaseDetail();
  }
  handleRefresh();
  isUploading.value = false;
  setTimeout(() => {
    startUpload.value = false;
    totalFiles.value = 0;
    uploadedCount.value = 0;
    successCount.value = 0;
    failCount.value = 0;
  }, 5000);
};

const handleSuccess = (file: UploadFile) => {
  uploadFileList.value = uploadFileList.value.filter(
    (item: UploadFile) => item.uid !== file.uid
  );
};
const handleFileDelete = (local_path: string) => {
  Modal.confirm({
    title: t("common.delete"),
    icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
    content: t("knowledge.deleteFileTip"),
    okText: t("common.confirm"),
    okType: "danger",
    async onOk() {
      const { name } = knowledgeData;
      await requestFileDelete(name, { local_path });
      queryKnowledgeBaseDetail();
      handleRefresh();
    },
  });
};

const handleRefresh = () => {
  eventBus.emit("refresh");
};

onMounted(() => {
  loading.value = true;
  queryKnowledgeBaseDetail();
});
</script>

<style lang="less" scoped>
.detail-wrap {
  height: 100%;
  .flex-column;
}
.upload-wrap {
  padding: 16px;
  :deep(.intel-upload-drag) {
    background-color: var(--bg-content-color);
  }
  .upload-text {
    color: var(--font-text-color);
    margin: 8px 0;
    font-weight: 500;
    font-size: 16px;
  }
  .upload-tip {
    color: var(--font-tip-color);
    font-size: 12px;
    line-height: 1.4;
    margin-top: 12px;
  }
}
.files-container {
  flex: 1;
  width: 100%;
  padding: 12px 16px;
  .file-item {
    padding: 12px;
    background-color: var(--bg-content-color);
    border: 1px solid var(--border-main-color);
    border-radius: 6px;
    .flex-between;
    &:hover {
      .card-shadow;
    }
    .left-wrap {
      flex: 1;
      min-width: 0;
      .flex-left;
      gap: 6px;
      .file-name {
        flex: 1;
        color: var(--font-main-color);
        .single-ellipsis;
      }
    }
    .right-wrap {
      .delete-icon {
        color: var(--font-tip-color);
        &:hover {
          color: var(--color-error);
        }
      }
    }
  }
}
.intel-empty {
  margin: 200px auto;
}
.tip-wrap {
  margin: 0 20px;
  border: 1px solid var(--border-warning);
  border-left: 3px solid var(--color-second-warning);
  background-color: var(--color-warningBg);
  color: var(--color-second-warning);
  padding: 8px 12px 0 12px;
  border-radius: 0 4px 4px 0;
  margin-bottom: 12px;
  font-size: 12px;
  .flex-between;
  .tip-text {
    display: flex;
    gap: 4px;
    align-items: center;
  }
  .rated-wrap {
    width: 400px;
    display: flex;
    gap: 4px;
    align-items: center;
    :deep(.intel-slider-horizontal) {
      flex: 1;
      top: -2px;
      .intel-slider-rail {
        height: 8px;
        border-radius: 4px;
      }
      .intel-slider-track {
        height: 8px;
        border-radius: 4px;
        background-color: var(--color-primary-tip) !important;
      }
      .intel-slider-handle::after {
        top: 1px;
        box-shadow: 0 0 0 2px var(--color-primary-second) !important;
      }
    }
  }
  .is-success {
    .pr-6;
    color: var(--color-success);
  }
  .is-failed {
    color: var(--color-error);
  }
}
</style>
