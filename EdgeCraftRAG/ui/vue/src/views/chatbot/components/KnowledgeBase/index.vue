<template>
  <div class="knowledge-base">
    <div class="menu-container">
      <div class="header-menu">
        <a-button type="primary" @click="handleCreate">
          <template #icon>
            <PlusOutlined />
          </template>
          {{ $t("knowledge.create") }}</a-button
        >
      </div>
      <div class="list-container" v-if="kbList.length">
        <div
          :class="['kb-list', item.idx === selectedKB ? 'select-wrap' : '']"
          v-for="item in kbList"
          :key="item.idx"
          @click="handleView(item)"
        >
          <span class="active-icon" v-if="item.active"
            ><CheckOutlined :style="{ fontSize: '12px' }"
          /></span>
          <div class="left-wrap">
            <SvgIcon
              name="icon-knowledge"
              :style="{ color: 'var(--color-primary-second)' }"
            />
            <div class="des-wrap">
              <div class="name-wrap">{{ item.name }}</div>
              <div class="total-wrap">
                {{ $t("knowledge.total") }}
                {{ Object.keys(item.file_map).length || 0 }}
              </div>
            </div>
          </div>
          <div class="right-wrap">
            <a-dropdown>
              <a @click.prevent class="expand-wrap"> ... </a>
              <template #overlay>
                <a-menu>
                  <a-menu-item
                    key="activate"
                    :disabled="item.active"
                    @click="handleSwitchState(item)"
                  >
                    <CheckCircleFilled
                      :style="{ color: 'var(--color-success)' }"
                    />
                    {{ $t("common.active") }}</a-menu-item
                  >
                  <a-menu-item key="update" @click="handleUpdate(item)">
                    <EditFilled
                      :style="{ color: 'var(--color-primary-second)' }"
                    />
                    {{ $t("common.edit") }}</a-menu-item
                  >
                  <a-menu-item
                    key="delete"
                    @click="handleDelete(item)"
                    :disabled="item.active"
                  >
                    <DeleteFilled :style="{ color: 'var(--color-error)' }" />
                    {{ $t("common.delete") }}</a-menu-item
                  >
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </div>
      </div>
      <a-empty v-else />
    </div>
    <UpdateDialog
      v-if="updateDialog.visible"
      :dialog-data="updateDialog.data"
      :dialog-type="updateDialog.type"
      @search="handleSearch"
      @close="updateDialog.visible = false"
    />
  </div>
</template>

<script lang="ts" setup name="KnowledgeBase">
import { onMounted, reactive, createVNode } from "vue";
import { UpdateDialog } from "./index";
import {
  getKnowledgeBaseList,
  getKnowledgeBaseDetialById,
  requestKnowledgeBaseUpdate,
  requestKnowledgeBaseDelete,
} from "@/api/knowledgeBase";
import {
  PlusOutlined,
  CheckOutlined,
  DeleteFilled,
  EditFilled,
  CheckCircleFilled,
  CloseCircleFilled,
} from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";
import { Modal } from "ant-design-vue";
import eventBus from "@/utils/mitt";

const emit = defineEmits(["view"]);
const { t } = useI18n();
const selectedKB = ref<string>("");

const updateDialog = reactive<DialogType>({
  visible: false,
  type: "create",
  data: {},
});

const kbList = ref<EmptyArrayType>([]);

const queryKnowledgeBaseList = async () => {
  const data: any = await getKnowledgeBaseList();

  kbList.value = [].concat(data);
};
//create
const handleCreate = () => {
  updateDialog.type = "create";
  updateDialog.data = {};
  updateDialog.visible = true;
};
//edit
const handleUpdate = async (row: EmptyObjectType) => {
  const data: any = await getKnowledgeBaseDetialById(row.idx);

  updateDialog.data = data;
  updateDialog.type = "edit";
  updateDialog.visible = true;
};
//detail
const handleView = async (row: EmptyObjectType) => {
  const { idx } = row;
  selectedKB.value = idx;
  emit("view", selectedKB.value);
};
//delete
const handleDelete = (row: EmptyObjectType) => {
  Modal.confirm({
    title: t("common.delete"),
    icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
    content: t("knowledge.deleteTip"),
    okText: t("common.confirm"),
    okType: "danger",
    async onOk() {
      await requestKnowledgeBaseDelete(row.idx);
      handleSearch();
      if (selectedKB.value === row.idx) {
        selectedKB.value = "";
        emit("view", selectedKB.value);
      }
    },
  });
};
//activate
const handleSwitchState = (row: EmptyObjectType) => {
  const { name } = row;

  Modal.confirm({
    title: t("common.prompt"),
    content: t("knowledge.activeTip"),
    okText: t("common.confirm"),
    async onOk() {
      await requestKnowledgeBaseUpdate({ name, active: true });
      handleSearch();
    },
  });
};
//search
const handleSearch = () => {
  queryKnowledgeBaseList();
};

onMounted(() => {
  queryKnowledgeBaseList();
  eventBus.on("refresh", queryKnowledgeBaseList);
  eventBus.on("reset", () => {
    selectedKB.value = "";
  });
});

onUnmounted(() => {
  eventBus.off("refresh", queryKnowledgeBaseList);
  eventBus.on("reset", () => {
    selectedKB.value = "";
  });
});
</script>

<style scoped lang="less">
.knowledge-base {
  position: relative;
  height: 100%;

  .menu-container {
    width: 100%;
    height: 100%;
    padding: 16px 0;
    border-right: 1px solid var(--border-main-color);
    .flex-column;
    gap: 12px;
    .header-menu {
      .vertical-center;
      padding: 0 16px 12px 16px;
      border-bottom: 1px solid var(--border-main-color);
      .intel-btn {
        width: 100%;
      }
    }
    .list-container {
      flex: 1;
      overflow-y: auto;
      width: 100%;
      padding: 0 16px;
      .kb-list {
        width: 100%;
        border: 1px solid var(--border-main-color);
        border-radius: 6px;
        padding: 8px;
        margin-bottom: 12px;
        position: relative;
        cursor: pointer;
        display: flex;
        &:hover {
          background-color: var(--bg-main-color);
          .card-shadow;
        }
        .left-wrap {
          flex: 1;
          min-width: 0;
          .flex-left;
          gap: 6px;
          .des-wrap {
            flex: 1;
            min-width: 0;
            padding-right: 10px;
            overflow: hidden;
            .flex-column;
            gap: 8px;
            .name-wrap {
              font-weight: 600;
              flex: 1;
              min-width: 0;
              line-height: 16px;
              text-align: left;
              .single-ellipsis;
            }
            .total-wrap {
              color: var(--font-info-color);
              font-size: 12px;
              text-align: left;
            }
          }
        }
        .right-wrap {
          padding-left: 4px;
          height: 100%;
          .expand-wrap {
            font-size: 18px;
            font-weight: 600;
            color: var(--font-text-color);
            cursor: pointer;
          }
        }
        &.select-wrap {
          border: 1px solid var(--color-primary-second);
          background-color: var(--bg-content-color);
        }
        .active-icon {
          position: absolute;
          right: -1px;
          top: -1px;
          border-radius: 0 6px 0 6px;
          width: 18px;
          height: 18px;
          background-color: var(--color-success);
          color: var(--color-white);
          .vertical-center;
        }
      }
    }
  }

  .body-container {
    height: 100%;
  }
}
.chart-box {
  width: 440px;
  padding: 10px;
  :deep(.chart-wrap) {
    width: 200px !important;
    height: 140px !important;
  }
}
.intel-empty {
  margin: 200px auto;
}
</style>
