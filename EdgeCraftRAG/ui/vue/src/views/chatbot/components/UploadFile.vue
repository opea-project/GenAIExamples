<template>
  <div class="upload-wrap">
    <a-upload-dragger
      v-model:file-list="uploadFileList"
      name="file"
      multiple
      :max-count="10"
      :action="uploadFileUrl"
      accept=".csv,.doc,.docx,.enex,.epub,.html,.md,.odt,.pdf,.ppt,.pptx,.txt,"
      :before-upload="handleBeforeUpload"
      @change="handleChange"
    >
      <SvgIcon
        name="icon-cloudupload-fill"
        :size="50"
        :style="{ color: 'var(--font-tip-color)' }"
      />
      <p class="upload-text">Click to upload or drag the file here</p>
      <div class="upload-tip">
        <p>
          Supported formats: PDF,PPT,PPTX,TXT,DOC,DOCX,HTML,MD,CSV,ENEX,EPUB and
          ODT.
        </p>
        <p>Single file size not exceeding 20M.</p>
      </div>
    </a-upload-dragger>
    <div class="uploaded-wrap" v-if="uploadedList.length">
      <a-collapse v-model:activeKey="listActive" expandIconPosition="end" ghost>
        <a-collapse-panel key="file" header="File uploaded">
          <transition-group name="expand-fade" tag="div">
            <div
              v-for="item in displayFiles"
              :key="item.file_id"
              class="file-item"
            >
              <div class="left-wrap">
                <img :src="uploaded" alt="" />
                {{ item.file_name }}
              </div>
              <div class="right-wrap">
                <a-tooltip placement="top">
                  <template #title>
                    <span>Delete File</span>
                  </template>
                  <DeleteFilled
                    class="delete-icon"
                    @click="handleFileDelete(item)"
                  />
                </a-tooltip>
              </div>
            </div>
          </transition-group>
          <div v-if="uploadedList.length > 10" class="expande-wrap">
            <span @click="handleToggleExpand"
              >{{ isExpanded ? "Collapse" : "Expand" }}
              <component :is="isExpanded ? UpOutlined : DownOutlined"
            /></span>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </div>
</template>

<script lang="ts" setup name="UploadFile">
import {
  getFilleList,
  requestFileDelete,
  requestParsingFiles,
  uploadFileUrl,
} from "@/api/chatbot";
import uploaded from "@/assets/svgs/uploaded.svg";
import router from "@/router";
import { pipelineAppStore } from "@/store/pipeline";
import { useNotification } from "@/utils/common";
import {
  CloseCircleFilled,
  DeleteFilled,
  DownOutlined,
  UpOutlined,
} from "@ant-design/icons-vue";
import { message, Modal, UploadProps, UploadFile } from "ant-design-vue";
import { createVNode, onMounted, ref } from "vue";

const { antNotification } = useNotification();
const pipelineStore = pipelineAppStore();
const uploadFileList = ref([]);
const uploadedList = ref<EmptyArrayType>([]);
const listActive = ref<string>("file");
const isExpanded = ref<boolean>(false);

const displayFiles = computed(() =>
  isExpanded.value ? uploadedList.value : uploadedList.value.slice(0, 10)
);
const handleBeforeUpload = (file: UploadProps["fileList"][number]) => {
  const isFileSize = file.size / 1024 / 1024 < 20;

  if (!isFileSize) {
    message.error("Single file size not exceeding 20M.");
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
  const { response, status } = file;
  if (status === "done") {
    requestParsingFiles({
      local_path: response,
    });
    handleSuccess(file);
  } else if (status === "error") {
    antNotification("error", "Error", response.detail);
  }

  const isAllEnd = fileList.every((file: any) => file.status !== "uploading");

  if (isAllEnd) {
    setTimeout(() => {
      queryFilleList();
    }, 50);
  }
};
const handleSuccess = (file: UploadFile) => {
  uploadFileList.value = uploadFileList.value.filter(
    (item: UploadFile) => item.uid !== file.uid
  );
};
const queryFilleList = async () => {
  const data: any = await getFilleList();
  uploadedList.value = [].concat(data);
};

const handleFileDelete = (row: EmptyObjectType) => {
  const { file_name } = row;
  Modal.confirm({
    title: "Delete",
    icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
    content: `Are you sure delete this file?`,
    okText: "Confirm",
    okType: "danger",
    async onOk() {
      await requestFileDelete(file_name);
      queryFilleList();
    },
  });
};
const handleToggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};
onMounted(() => {
  if (!pipelineStore.activatedPipeline) {
    Modal.warning({
      title: "Prompt",
      content:
        "There is no available pipeline. Please create or activate it first.",
      okText: "Go Configure",
      class: "centered-model",
      onOk() {
        router.push("/pipeline");
      },
    });

    return false;
  }
  queryFilleList();
});
</script>

<style scoped lang="less">
.upload-wrap {
  width: 100%;
  padding: 20px;
  border-radius: 6px;
  margin-top: 20px;
  background-color: var(--bg-content-color);

  :deep(.intel-upload) {
    border-radius: 6px;
    background-color: var(--bg-content-color);
    &:hover {
      color: var(--color-primary);
    }
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
  .uploaded-wrap {
    margin-top: 16px;
    :deep(.intel-collapse) {
      .intel-collapse-header {
        font-size: 16px;
        font-weight: 600;
        border-radius: 8px 8px 0 0;
        background-color: var(--border-main-color);
      }
      .intel-collapse-content-box {
        padding: 8px 0;
      }
    }
    .file-item {
      margin-bottom: 8px;
      font-size: 14px;
      height: 48px;
      padding: 0 12px;
      color: var(--font-text-color);
      background-color: var(--bg-card-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      .left-wrap {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 6px;
        img {
          height: 20px;
        }
        .size-text {
          color: var(--font-tip-color);
        }
      }
      .right-wrap {
        width: 30px;
        text-align: end;
        font-size: 16px;
        cursor: pointer;
        color: var(--font-tip-color);
        &:hover {
          color: var(--color-primary);
        }
      }
    }
    .expande-wrap {
      .vertical-center;
      padding-top: 12px;
      font-weight: 600;
      font-size: 16px;
      cursor: pointer;
      color: var(--color-primary);
      &:hover {
        color: var(--color-primary-hover);
      }
    }
  }
}
.delete-icon {
  &:hover {
    color: var(--color-error);
  }
}
.expand-fade-enter-active,
.expand-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.expand-fade-enter-from,
.expand-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
