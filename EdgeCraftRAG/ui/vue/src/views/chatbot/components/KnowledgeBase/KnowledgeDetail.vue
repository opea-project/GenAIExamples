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
        <a-slider v-model:value="uploadedCount" :min="0" :max="totalFiles" disabled /><span
          >{{ uploadedCount }}/{{ totalFiles }}
          <span class="pl-8">
            {{ $t("knowledge.successfully") }}:
            <span class="is-success">{{ successCount }}</span>
            {{ $t("knowledge.failed") }}: <span class="is-failed">{{ failCount }}</span></span
          >
        </span>
      </div>
    </div>
    <div v-if="failedFiles.length" class="failed-container">
      <div class="failed-files-header">
        <span class="failed-title">
          {{ $t("knowledge.failedFile") }}
          <span class="tag-wrap"> {{ $t("common.count") }}: {{ failedFiles.length }}</span>
        </span>
        <div class="failed-button">
          <a-button
            type="primary"
            size="small"
            :icon="h(ReloadOutlined)"
            :disabled="isRetrying"
            @click="retryAllFailedFiles"
          >
            {{ $t("common.retryAll") }}
          </a-button>
          <a-button
            type="primary"
            size="small"
            :icon="h(SyncOutlined)"
            :disabled="isRetrying"
            @click="replaceAllFailedFiles"
          >
            {{ $t("common.replaceAll") }}
          </a-button>
          <a-button
            type="primary"
            size="small"
            :icon="h(StopOutlined)"
            :disabled="isRetrying"
            @click="ignoreAllFailedFiles"
          >
            {{ $t("common.ignoreAll") }}
          </a-button>
        </div>
      </div>
      <div class="failed-files-list">
        <div v-for="(file, index) in failedFiles" :key="index" class="failed-file-item">
          <div class="left-wrap">
            <div class="header-wrap">
              <ExceptionOutlined :style="{ color: 'var(--color-error)', fontSize: '20px' }" />
              <div class="file-info">
                <a-tooltip placement="topLeft" :title="file.name">
                  <div class="file-name">{{ file.name }}</div></a-tooltip
                >
                <div class="file-path"><BranchesOutlined class="path-icon" />{{ file.path }}</div>
                <a-tooltip placement="bottom" :title="file.error">
                  <div class="error-message">
                    <WarningOutlined class="error-icon" />{{ file.error }}
                  </div></a-tooltip
                >
              </div>
            </div>
          </div>
          <div class="right-wrap">
            <a-tooltip placement="topLeft" :title="$t('common.retry')">
              <ReloadOutlined class="file-icon" @click="retrySingleFile(file)" />
            </a-tooltip>
            <a-tooltip placement="topLeft" :title="$t('common.replace')">
              <SyncOutlined class="file-icon" @click="replaceSingleFile(file)"
            /></a-tooltip>
            <a-tooltip placement="topLeft" :title="$t('common.ignore')">
              <StopOutlined class="file-icon" @click="ignoreSingleFile(file)"
            /></a-tooltip>
          </div>
        </div>
      </div>
    </div>
    <PartialLoading :visible="loading" />
    <template v-if="!loading">
      <a-empty
        v-if="notFile && failedFiles.length === 0"
        :description="$t('knowledge.notFileTip')"
      />
      <div class="files-container" v-if="!notFile">
        <a-row type="flex" wrap :gutter="[20, 10]">
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
                  <DeleteFilled class="delete-icon" @click="handleFileDelete(value as string)" />
                </a-tooltip>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts" name="KnowledgeBaseDetail">
  import {
    getKnowledgeBaseDetailByName,
    requestFileDelete,
    requestKnowledgeBaseRelation,
    requestUploadFileUrl,
  } from "@/api/knowledgeBase";
  import { useNotification } from "@/utils/common";
  import eventBus from "@/utils/mitt";
  import {
    BranchesOutlined,
    CloseCircleFilled,
    DeleteFilled,
    ExceptionOutlined,
    ExclamationCircleFilled,
    FileDoneOutlined,
    ReloadOutlined,
    StopOutlined,
    SyncOutlined,
    WarningOutlined,
  } from "@ant-design/icons-vue";
  import { Modal, UploadFile, UploadProps } from "ant-design-vue";
  import JSZip from "jszip";
  import { computed, createVNode, h, inject, onMounted, reactive, ref } from "vue";
  import { useI18n } from "vue-i18n";

  interface KbType {
    name: string;
  }

  interface FailedFile {
    name: string;
    file: File;
    retrying: boolean;
    path: string;
    error: string;
  }

  const { t } = useI18n();
  const { antNotification } = useNotification();

  const kbInfo = inject<KbType>("kbInfo");
  const uploadFileList = ref<UploadFile[]>([]);
  const knowledgeData = reactive<EmptyObjectType>({});
  const pendingFiles = ref<any[]>([]);
  const failedFiles = ref<FailedFile[]>([]);
  const isUploading = ref<boolean>(false);
  const isRetrying = ref<boolean>(false);
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
      return false;
    }
    return isFileSize;
  };

  const handleZipParse = async (options: any) => {
    const origFile = options.file as File;
    try {
      const arrayBuffer = await origFile.arrayBuffer();
      const zip = await JSZip.loadAsync(arrayBuffer);
      const entries: JSZip.JSZipObject[] = [];
      zip.forEach((relativePath, fileEntry) => {
        entries.push(fileEntry);
      });

      const fileEntries = entries.filter(e => !e.dir);

      if (fileEntries.length === 0) {
        antNotification("error", t("common.error"), t("knowledge.zipNoFiles"));
        return;
      }

      const innerPromises = fileEntries.map(async entry => {
        const blob = await entry.async("blob");

        const filename = entry.name.split("/").pop() || entry.name;
        const innerFile = new File([blob], filename, {
          type: blob.type || "application/octet-stream",
        });

        const innerUid = `file_${filename}_${Date.now()}`;

        const newOption: any = {
          ...options,
          file: innerFile,
          uid: innerUid,
          onSuccess: options.onSuccess,
          onError: options.onError,
        };

        return newOption;
      });

      const innerOptions = await Promise.all(innerPromises);
      innerOptions.forEach((opt: any) => pendingFiles.value.push(opt));
      totalFiles.value += innerOptions.length;
    } catch (err) {
      console.error(err);
    }
  };

  const handleFailedFile = (file: File, path: string, error: string) => {
    const fileName = file.name;
    const existingIndex = failedFiles.value.findIndex(item => item.name === fileName);

    if (existingIndex === -1) {
      failedFiles.value.push({
        name: fileName,
        file: file,
        retrying: false,
        path,
        error,
      });
    } else {
      failedFiles.value[existingIndex].file = file;
      failedFiles.value[existingIndex].error = error;
      failedFiles.value[existingIndex].path = path;
    }
  };

  const removeFailedFileByName = (fileName: string) => {
    failedFiles.value = failedFiles.value.filter(f => f.name !== fileName);
  };

  const customRequest = async (options: any) => {
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
          const fileName = file.name;
          const { name } = knowledgeData;
          let res: any = null;

          try {
            res = await requestUploadFileUrl(name, { file });

            await requestKnowledgeBaseRelation(name, { local_path: res });

            onSuccess?.(res, uploadFile as any);
            handleSuccess(uploadFile);
            successCount.value += 1;

            removeFailedFileByName(fileName);
          } catch (error: any) {
            onError?.(error);
            failCount.value += 1;
            handleFailedFile(file, res, getErrorMessage(error));
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
    const fileName = file.name;
    uploadFileList.value = uploadFileList.value.filter(
      (item: UploadFile) => item.name !== fileName
    );
  };

  const retrySingleFile = async (failedFile: FailedFile) => {
    if (failedFile.retrying || isRetrying.value || !failedFile.path) {
      return;
    }

    failedFile.retrying = true;

    try {
      const { name } = knowledgeData;
      await requestKnowledgeBaseRelation(name, { local_path: failedFile.path });

      removeFailedFileByName(failedFile.name);
      queryKnowledgeBaseDetail();
      handleRefresh();
    } catch (error: any) {
      failedFile.retrying = false;
      failedFile.error = getErrorMessage(error);
    }
  };

  const replaceSingleFile = async (failedFile: FailedFile) => {
    if (failedFile.retrying || isRetrying.value || !failedFile.path) {
      return;
    }

    failedFile.retrying = true;

    try {
      const { name } = knowledgeData;

      await requestFileDelete(name, { local_path: failedFile.path });

      await requestKnowledgeBaseRelation(name, { local_path: failedFile.path });

      removeFailedFileByName(failedFile.name);
      queryKnowledgeBaseDetail();
      handleRefresh();
    } catch (error: any) {
      failedFile.retrying = false;
      failedFile.error = getErrorMessage(error);
    }
  };

  const ignoreSingleFile = async (failedFile: FailedFile) => {
    if (failedFile.retrying || isRetrying.value) {
      return;
    }

    failedFile.retrying = true;

    try {
      const index = failedFiles.value.findIndex(item => item.name === failedFile.name);
      if (index !== -1) {
        failedFiles.value.splice(index, 1);
      }
    } catch (error) {
      failedFile.retrying = false;
    }
  };

  const retryAllFailedFiles = async () => {
    if (isRetrying.value) return;

    isRetrying.value = true;

    try {
      const { name } = knowledgeData;
      await Promise.allSettled(
        failedFiles.value.map(async file => {
          try {
            await requestKnowledgeBaseRelation(name, { local_path: file.path });
            removeFailedFileByName(file.name);
            return { name: file.name, success: true };
          } catch (error: any) {
            file.retrying = false;
            file.error = getErrorMessage(error);
            return { name: file.name, success: false, error };
          }
        })
      );

      queryKnowledgeBaseDetail();
      handleRefresh();
    } catch (error) {
      console.error(error);
    } finally {
      isRetrying.value = false;
    }
  };

  const replaceAllFailedFiles = async () => {
    if (isRetrying.value) return;

    isRetrying.value = true;

    try {
      const { name } = knowledgeData;

      const deleteResults = await Promise.allSettled(
        failedFiles.value.map(async file => {
          try {
            await requestFileDelete(name, { local_path: file.path });
            return { name: file.name, success: true };
          } catch (error: any) {
            return { name: file.name, success: false, error };
          }
        })
      );

      const filesToRetry = failedFiles.value.filter((file, index) => {
        const result = deleteResults[index];
        return result.status === "fulfilled" && result.value.success;
      });

      if (filesToRetry.length) {
        await Promise.allSettled(
          filesToRetry.map(async file => {
            try {
              await requestKnowledgeBaseRelation(name, { local_path: file.path });
              removeFailedFileByName(file.name);
              return { name: file.name, success: true };
            } catch (error: any) {
              file.retrying = false;
              file.error = getErrorMessage(error);
              return { name: file.name, success: false, error };
            }
          })
        );
      }

      queryKnowledgeBaseDetail();
      handleRefresh();
    } catch (error) {
      console.error(error);
    } finally {
      isRetrying.value = false;
    }
  };

  const ignoreAllFailedFiles = () => {
    if (isRetrying.value) return;
    failedFiles.value = [];
  };

  const getErrorMessage = (error: any) => {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    return t("knowledge.retryFailed");
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

  .failed-container {
    .p-16;
    border-radius: 8px;
    margin: 0 16px;
    background-color: var(--bg-content-color);

    .failed-files-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .failed-title {
        font-weight: 500;
        font-size: 16px;
        color: var(--font-main-color);
        display: flex;
        align-items: center;
        gap: 6px;
        .tag-wrap {
          background-color: var(--color-errorBg);
          color: var(--color-error);
          padding: 1px 8px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 400;
        }
      }
    }

    .failed-files-list {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 10px 20px;

      .failed-file-item {
        padding: 8px;
        background-color: rgb(from var(--bg-main-color) r g b / 0.4);
        border-radius: 6px;
        border: 1px solid var(--border-main-color);
        .flex-between;
        gap: 4px;
        min-width: 0;

        &:hover {
          border: 1px solid var(--border-error);
          .card-shadow;
        }

        .left-wrap {
          .flex-column;
          flex: 1;
          min-width: 0;
          width: 0;

          .header-wrap {
            display: flex;
            min-width: 0;
            width: 100%;
            gap: 6px;
            .file-info {
              .flex-column;
              flex: 1;
              min-width: 0;
              width: 0;
              .file-name {
                color: var(--font-main-color);
                flex: 1;
                font-weight: 600;
                .single-ellipsis;
                direction: rtl;
                text-align: left;
              }
              .file-path {
                font-size: 12px;
                color: var(--font-tip-color);
                .single-ellipsis;
                .path-icon {
                  color: var(--font-main-color);
                  .mr-4;
                }
              }
              .error-message {
                font-size: 12px;
                color: var(--color-error-hover);
                .single-ellipsis;
                .error-icon {
                  color: var(--color-error);
                  .mr-4;
                }
              }
            }
          }
        }

        .right-wrap {
          .flex-column;
          width: 18px;
          height: 100%;
          flex-shrink: 0;
          padding-right: 1px;
          .file-icon {
            flex: 1;
            .vertical-center;
            color: var(--font-text-color);
            &:hover {
              color: var(--color-primary-hover);
            }
          }
        }
      }
    }
  }

  .files-container {
    flex: 1;
    width: 100%;
    padding: 18px;
    .file-item {
      padding: 12px;
      background-color: var(--bg-content-color);
      border: 1px solid var(--border-main-color);
      border-radius: 6px;
      .flex-between;
      gap: 4px;
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
          direction: rtl;
          text-align: left;
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
