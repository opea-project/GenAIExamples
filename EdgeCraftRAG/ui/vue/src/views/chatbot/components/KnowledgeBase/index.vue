<template>
  <div class="knowledge-base" :class="{ collapsed: isCollapsed }">
    <div class="menu-container">
      <div class="header-menu">
        <a-tooltip v-if="isCollapsed" :title="$t('knowledge.create')" placement="right">
          <a-button type="primary" block @click="handleCreateSelect">
            <template #icon>
              <PlusOutlined />
            </template>
          </a-button>
        </a-tooltip>
        <a-button v-else type="primary" block @click="handleCreateSelect">
          <template #icon>
            <PlusOutlined />
          </template>
          <span class="btn-text">{{ $t("knowledge.create") }}</span>
        </a-button>
      </div>
      <div class="list-container" v-if="kbList.length">
        <template v-if="isCollapsed">
          <a-tooltip
            v-for="item in kbList"
            :key="item.idx"
            :title="item.name"
            placement="right"
            :mouseEnterDelay="0.3"
          >
            <div
              :class="['kb-list', item.idx === selectedKB ? 'select-wrap' : '']"
              @click="handleView(item)"
            >
              <span
                :class="{
                  'active-icon': true,
                  'is-experience': item.comp_type === 'experience',
                }"
                v-if="item.active || item.experience_active"
                ><CheckOutlined :style="{ fontSize: '12px' }"
              /></span>
              <div class="left-wrap">
                <SvgIcon
                  :name="item.comp_type === 'experience' ? 'icon-experience' : 'icon-knowledge'"
                  :style="{ color: 'var(--color-primary-second)' }"
                />
              </div>
            </div>
          </a-tooltip>
        </template>
        <template v-else>
          <div
            v-for="item in kbList"
            :key="item.idx"
            :class="['kb-list', item.idx === selectedKB ? 'select-wrap' : '']"
            @click="handleView(item)"
          >
            <span
              :class="{
                'active-icon': true,
                'is-experience': item.comp_type === 'experience',
              }"
              v-if="item.active || item.experience_active"
              ><CheckOutlined :style="{ fontSize: '12px' }"
            /></span>
            <div class="left-wrap">
              <SvgIcon
                :name="item.comp_type === 'experience' ? 'icon-experience' : 'icon-knowledge'"
                :style="{ color: 'var(--color-primary-second)' }"
              />
              <div class="des-wrap">
                <div class="flex-left">
                  <div class="name-wrap">
                    {{ item.name }}
                  </div>
                  <template v-if="item.comp_type === 'experience'">
                    <span class="tag-wrap"> {{ $t("experience.unique") }}</span>
                  </template>
                  <template v-if="item?.comp_subtype === 'kbadmin_kb'">
                    <span class="tag-wrap">kbadmin</span>
                  </template>
                </div>
                <div class="total-wrap">
                  <template v-if="item.comp_type === 'experience'">
                    {{ $t("experience.total") }}
                    {{ item.total }}
                  </template>
                  <template v-else-if="item?.comp_subtype === 'origin_kb'">
                    {{ $t("knowledge.total") }}
                    {{ item.total }}</template
                  >
                </div>
              </div>
            </div>
            <div class="right-wrap">
              <a-dropdown arrow>
                <a @click.prevent class="expand-wrap"> ... </a>
                <template #overlay>
                  <a-menu>
                    <template v-if="item.comp_type === 'knowledge'">
                      <a-menu-item key="activate" @click="handleSwitchState(item)">
                        <template v-if="!item.active">
                          <CheckCircleFilled :style="{ color: 'var(--color-success)' }" />
                          {{ $t("common.active") }}
                        </template>
                        <template v-else>
                          <PauseCircleFilled :style="{ color: 'var(--color-error)' }" />
                          {{ $t("common.deactivate") }}
                        </template>
                      </a-menu-item>
                    </template>
                    <template v-else>
                      <a-menu-item
                        key="experience_active"
                        @click="handleSwitchExperienceState(item)"
                      >
                        <template v-if="!item.experience_active">
                          <CheckCircleFilled :style="{ color: 'var(--color-success)' }" />
                          {{ $t("common.active") }}</template
                        >
                        <template v-else>
                          <PauseCircleFilled :style="{ color: 'var(--color-error)' }" />
                          {{ $t("common.deactivate") }}
                        </template>
                      </a-menu-item>
                    </template>
                    <a-menu-item key="update" @click="handleUpdate(item)">
                      <EditFilled :style="{ color: 'var(--color-primary-second)' }" />
                      {{ $t("common.edit") }}</a-menu-item
                    >
                    <a-menu-item
                      key="delete"
                      @click="handleDelete(item)"
                      :disabled="item.active || item.experience_active"
                    >
                      <DeleteFilled :style="{ color: 'var(--color-error)' }" />
                      {{ $t("common.delete") }}</a-menu-item
                    >
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </div>
        </template>
      </div>
      <a-empty v-else />
    </div>
    <UpdateDialog
      v-if="updateDialog.visible"
      :dialog-data="updateDialog.data"
      :dialog-type="updateDialog.type"
      :dialog-flag="updateDialog.flag"
      @switch="handleSwitch"
      @close="updateDialog.visible = false"
    />
    <SelectTypeDialog
      v-if="selectTypeDialog.visible"
      :created="isCreated"
      @close="selectTypeDialog.visible = false"
      @createKB="handleCreate"
    />
  </div>
</template>

<script lang="ts" setup name="KnowledgeBase">
  import {
    getKnowledgeBaseDetailByName,
    getKnowledgeBaseList,
    requestKnowledgeBaseDelete,
    requestKnowledgeBaseUpdate,
  } from "@/api/knowledgeBase";
  import eventBus from "@/utils/mitt";
  import {
    CheckCircleFilled,
    CheckOutlined,
    CloseCircleFilled,
    DeleteFilled,
    EditFilled,
    PauseCircleFilled,
    PlusOutlined,
  } from "@ant-design/icons-vue";
  import { Modal } from "ant-design-vue";
  import { computed, createVNode, onMounted, reactive, ref } from "vue";
  import { useI18n } from "vue-i18n";
  import { SelectTypeDialog, UpdateDialog } from "./index";

  const emit = defineEmits(["view"]);
  const { t } = useI18n();

  const props = defineProps({
    isCollapsed: {
      type: Boolean,
      default: false,
    },
  });

  const selectedKB = ref<string>("");

  const updateDialog = reactive<DialogType>({
    visible: false,
    type: "create",
    flag: "knowledge",
    data: {},
  });
  const selectTypeDialog = reactive<DialogType>({
    visible: false,
  });

  const kbList = ref<EmptyArrayType>([]);
  const isCreated = computed(() => kbList.value.some(item => item.comp_type === "experience"));

  const queryKnowledgeBaseList = async () => {
    const data: any = await getKnowledgeBaseList();

    kbList.value = [].concat(data);
  };
  const handleCreateSelect = () => {
    selectTypeDialog.visible = true;
  };
  //create
  const handleCreate = (flag = "create") => {
    updateDialog.type = "create";
    updateDialog.flag = flag;
    updateDialog.data = {};
    updateDialog.visible = true;
  };
  //edit
  const handleUpdate = async (row: EmptyObjectType) => {
    const data: any = await getKnowledgeBaseDetailByName(row.name);

    updateDialog.data = data;
    updateDialog.type = "edit";
    updateDialog.flag = row.comp_type;
    updateDialog.visible = true;
  };
  //detail
  const handleView = async (row: EmptyObjectType) => {
    const { idx } = row;

    if (row.comp_subtype !== "kbadmin_kb") {
      selectedKB.value = idx;
      emit("view", row);
    }
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
        const { idx, name } = row;
        await requestKnowledgeBaseDelete(name);
        handleSearch();

        if (selectedKB.value === idx) {
          selectedKB.value = "";
          emit("view", { name: "" });
        }
      },
    });
  };
  //activate
  const handleSwitchState = (row: EmptyObjectType) => {
    const { name, active } = row;

    Modal.confirm({
      title: t("common.prompt"),
      content: t("knowledge.activeTip"),
      okText: t("common.confirm"),
      async onOk() {
        await requestKnowledgeBaseUpdate({ name, active: !active });
        handleSearch();
      },
    });
  };
  const handleSwitchExperienceState = (row: EmptyObjectType) => {
    const { name, experience_active } = row;

    const text = experience_active ? t("experience.deactivateTip") : t("experience.activeTip");
    Modal.confirm({
      title: t("common.prompt"),
      content: text,
      okText: t("common.confirm"),
      async onOk() {
        await requestKnowledgeBaseUpdate({
          name,
          experience_active: !experience_active,
        });
        handleSearch();
      },
    });
  };
  //search
  const handleSearch = () => {
    queryKnowledgeBaseList();
  };
  const handleSwitch = async (name: string) => {
    const data: any = await getKnowledgeBaseList();

    kbList.value = [].concat(data);

    const rowData = kbList.value.find(item => item.name === name) || {};
    handleView(rowData);
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

    &.collapsed {
      .menu-container {
        width: 60px;

        .header-menu {
          padding: 0 8px;
        }

        .list-container {
          padding: 0 8px;

          .kb-list {
            width: 40px;
            height: 40px;
            padding: 8px;
            margin-bottom: 8px;
            justify-content: center;

            .left-wrap {
              .des-wrap {
                display: none;
              }
            }

            .right-wrap {
              display: none;
            }

            .active-icon {
              right: -1px;
              top: -1px;
              width: 14px;
              height: 14px;

              .anticon {
                font-size: 10px !important;
              }
            }
          }
        }
      }
    }

    .menu-container {
      width: 100%;
      height: 100%;
      border-right: 1px solid var(--border-main-color);
      .flex-column;
      gap: 12px;
      transition: all 0.3s ease;

      .header-menu {
        .vertical-center;
        padding: 0 12px;
        height: 60px;
        border-bottom: 1px solid var(--border-main-color);
      }

      .list-container {
        flex: 1;
        overflow-y: auto;
        width: 100%;
        padding: 0 16px;
        transition: all 0.3s ease;

        .kb-list {
          width: 100%;
          height: 60px;
          border: 1px solid var(--border-main-color);
          border-radius: 6px;
          padding: 8px;
          margin-bottom: 12px;
          position: relative;
          cursor: pointer;
          display: flex;
          align-items: center;
          transition: all 0.3s ease;

          &:hover {
            background-color: var(--bg-main-color);
            .card-shadow;
          }

          .left-wrap {
            flex: 1;
            min-width: 0;
            .flex-left;
            gap: 6px;
            align-items: center;

            .des-wrap {
              flex: 1;
              min-width: 0;
              padding-right: 10px;
              overflow: hidden;
              .flex-column;
              gap: 8px;
              transition: opacity 0.3s ease;

              .name-wrap {
                font-weight: 600;
                min-width: 0;
                line-height: 16px;
                text-align: left;
                .single-ellipsis;
              }

              .tag-wrap {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                height: 16px;
                line-height: 1;
                padding: 0 6px;
                border-radius: 10px;
                font-size: 10px;
                margin-left: 4px;
                color: var(--color-primary-tip);
                background-color: var(--color-second-primaryBg);
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

            &.is-experience {
              background-color: var(--color-purple);
            }
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
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
</style>
