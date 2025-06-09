<template>
  <div class="kb-detial-container">
    <div class="header-wrap">
      <div class="info-wrap">
        <div class="name-wrap">{{ knowledgeData.name }}</div>
        <div class="des-wrap" v-if="knowledgeData.description">
          {{ knowledgeData.description }}
        </div>
      </div>
      <div class="button-wrap">
        <a-button
          type="primary"
          ghost
          :icon="h(RollbackOutlined)"
          @click="handleBack"
          >{{ $t("common.back") }}</a-button
        >
      </div>
    </div>
    <div class="upload-wrap">
      <a-upload-dragger
        v-model:file-list="uploadFileList"
        name="file"
        multiple
        :max-count="20"
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
              <SvgIcon
                name="icon-uploaded"
                :style="{ color: 'var(--color-primary-second)' }"
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

<script setup lang="ts" name="KnowledgeBaseDetial">
import { ref, reactive, createVNode, h } from "vue";
import {
  requestKnowledgeBaseRelation,
  getKnowledgeBaseDetialById,
  requestFileDelete,
  uploadFileUrl,
} from "@/api/knowledgeBase";
import { useNotification } from "@/utils/common";
import {
  CloseCircleFilled,
  DeleteFilled,
  RollbackOutlined,
} from "@ant-design/icons-vue";
import { message, Modal, UploadFile, UploadProps } from "ant-design-vue";
import { useI18n } from "vue-i18n";
import { NextLoading } from "@/utils/loading";
import eventBus from "@/utils/mitt";

const props = defineProps({
  kbId: {
    type: String,
    default: "",
  },
});

const { t } = useI18n();
const emit = defineEmits(["back"]);
const { antNotification } = useNotification();
const uploadFileList = ref([]);
const knowledgeData = reactive<EmptyObjectType>({});
const notFile = computed(() => {
  const { file_map = {} } = knowledgeData;
  return Object.keys(file_map).length === 0;
});
const uploadFileApi = computed(() => {
  return uploadFileUrl + knowledgeData.idx;
});

const queryKnowledgeBaseDetial = async () => {
  const data: any = await getKnowledgeBaseDetialById(props.kbId);
  Object.assign(knowledgeData, data);
};
const handleBeforeUpload = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 50;

  if (!isFileSize) {
    message.error(t("knowledge.uploadValid"));
  }

  return isFileSize;
};
const handleChange = ({
  fileList,
  file,
}: {
  fileList: UploadFile[];
  file: UploadFile;
}) => {
  const el = <HTMLElement>document.querySelector(".loading-next");
  if (!el) NextLoading.start();
  const { response, status } = file;
  const { idx } = knowledgeData;
  try {
    if (status === "done") {
      requestKnowledgeBaseRelation(idx, {
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
        queryKnowledgeBaseDetial();
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
      const { idx } = knowledgeData;
      await requestFileDelete(idx, { local_path });
      queryKnowledgeBaseDetial();
      handleRefresh();
    },
  });
};

const handleBack = () => {
  emit("back");
  eventBus.emit("reset");
};
const handleRefresh = () => {
  eventBus.emit("refresh");
};

watch(
  () => props.kbId,
  (kbId) => {
    if (kbId) queryKnowledgeBaseDetial();
  },
  { immediate: true, deep: true }
);
</script>

<style lang="less" scoped>
.kb-detial-container {
  display: block !important;
  .flex-column;
  .header-wrap {
    padding: 12px 16px;
    height: 60px;
    border-bottom: 1px solid var(--border-main-color);
    .flex-between;
    gap: 16px;
    min-width: 0;
    .info-wrap {
      flex: 1;
      .flex-column;
      gap: 4px;
      min-width: 0;
      .name-wrap {
        font-size: 16px;
        font-weight: 600;
        flex: 1;
        min-width: 0;
        line-height: 16px;
        .single-ellipsis;
      }
      .des-wrap {
        color: var(--font-info-color);
        font-size: 12px;
        .single-ellipsis;
      }
    }
    .button-wrap {
      .vertical-center;
      gap: 4px;
    }
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
}
</style>
