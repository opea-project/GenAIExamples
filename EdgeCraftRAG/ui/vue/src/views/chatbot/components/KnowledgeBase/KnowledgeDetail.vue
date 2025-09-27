<template>
  <div>
    <div class="upload-wrap">
      <a-upload-dragger
        v-model:file-list="uploadFileList"
        name="file"
        multiple
        :showUploadList="false"
        :action="uploadFileApi"
        accept=".csv,.doc,.docx,.enex,.epub,.html,.md,.odt,.pdf,.ppt,.pptx,.txt,"
        :before-upload="handleBeforeUpload"
        @change="handleChange"
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
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts" name="KnowledgeBaseDetail">
import { ref, reactive, createVNode, inject, onMounted } from "vue";
import {
  requestKnowledgeBaseRelation,
  getKnowledgeBaseDetailByName,
  requestFileDelete,
  uploadFileUrl,
} from "@/api/knowledgeBase";
import { useNotification } from "@/utils/common";
import {
  CloseCircleFilled,
  DeleteFilled,
  FileDoneOutlined,
} from "@ant-design/icons-vue";
import { message, Modal, UploadFile, UploadProps } from "ant-design-vue";
import { useI18n } from "vue-i18n";
import { NextLoading } from "@/utils/loading";
import eventBus from "@/utils/mitt";

interface KbType {
  name: string;
}
const { t } = useI18n();
const kbInfo = inject<KbType>("kbInfo");
const { antNotification } = useNotification();
const uploadFileList = ref([]);
const knowledgeData = reactive<EmptyObjectType>({});
const notFile = computed(() => {
  const { file_map = {} } = knowledgeData;
  return Object.keys(file_map).length === 0;
});
const uploadFileApi = computed(() => {
  return uploadFileUrl + knowledgeData.name;
});

const queryKnowledgeBaseDetail = async () => {
  const data: any = await getKnowledgeBaseDetailByName(kbInfo?.name!);
  Object.assign(knowledgeData, data);
};
const handleBeforeUpload = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 200;

  if (!isFileSize) {
    message.error(t("knowledge.uploadValid"));
    return;
  }

  return isFileSize;
};
const handleChange = async ({
  fileList,
  file,
}: {
  fileList: UploadFile[];
  file: UploadFile;
}) => {
  const el = <HTMLElement>document.querySelector(".loading-next");
  if (!el) NextLoading.start();
  const { response, status } = file;
  const { name } = knowledgeData;
  try {
    if (status === "done") {
      await requestKnowledgeBaseRelation(name, {
        local_path: response,
      });
      handleSuccess(file);
    } else if (status === "error") {
      antNotification("error", t("common.error"), response.detail);
    }

    const isAllEnd = fileList.every((file: any) => file.status !== "uploading");

    if (isAllEnd) {
      NextLoading.done();
      setTimeout(() => {
        queryKnowledgeBaseDetail();
        handleRefresh();
      }, 100);
    }
  } catch (error) {
    console.error(error);
    if (NextLoading) NextLoading.done();
  }
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
  queryKnowledgeBaseDetail();
});
</script>

<style lang="less" scoped>
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
</style>
