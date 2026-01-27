<template>
  <div class="chat-agent" :class="{ collapsed: isCollapsed }">
    <div class="header-section">
      <a-tooltip v-if="isCollapsed" :title="$t('chat.new')" placement="right">
        <div class="new-chat" @click="handleNewChat">
          <SvgIcon name="icon-newChat" :size="20" inherit />
        </div>
      </a-tooltip>
      <div v-else class="new-chat" @click="handleNewChat">
        <SvgIcon name="icon-newChat" :size="20" inherit />
        <span class="btn-text">{{ $t("chat.new") }}</span>
      </div>
    </div>
    <a-divider />
    <div class="agentsList-wrap">
      <div class="section-title mb-6" v-show="!isCollapsed">{{ $t("agent.agent") }}</div>
      <a-empty v-if="!isCollapsed && !agentsList?.length">
        <a-button type="primary" ghost size="small" @click="handleCreateAgent">{{
          $t("common.manual")
        }}</a-button>
      </a-empty>
      <div class="agent-menu">
        <div
          v-for="(agent, index) in agentsList"
          :key="index"
          :class="['agent-item', { selected: agent.active }]"
          :style="agent.active ? getActiveStyles(index) : {}"
          @click="() => handleAgentClick(agent, index)"
        >
          <a-tooltip v-if="isCollapsed" :title="agent.name" placement="right">
            <SvgIcon :name="getAgentIcon(agent)" inherit />
          </a-tooltip>
          <template v-else>
            <SvgIcon :name="getAgentIcon(agent)" inherit />
            <span class="agent-title">{{ agent.name }}</span>
          </template>
        </div>
      </div>
    </div>
    <a-divider />
    <div
      class="session-wrapper"
      @mouseenter="sessionHovering = true"
      @mouseleave="sessionHovering = false"
    >
      <div class="section-title" v-show="!isCollapsed">{{ $t("chat.history") }}</div>
      <div class="session-list" ref="sessionListRef" :class="{ 'show-scroll': sessionHovering }">
        <div
          v-for="session in sessionList"
          :key="session.id"
          :class="['session-item', { selected: isSessionSelected(session.id) }]"
          @click="() => handleSessionClick(session)"
        >
          <div class="session-main">
            <div class="session-texts">
              <a-tooltip v-if="isCollapsed" :title="session.name" placement="right">
                <div class="session-icon">
                  <MessageOutlined />
                </div>
              </a-tooltip>
              <template v-else>
                <div class="session-icon">
                  <MessageOutlined />
                </div>
                <div class="session-title" :title="session.name">
                  {{ session.name }}
                </div>
              </template>
            </div>
            <div class="session-actions" @click.stop v-if="!isCollapsed && false">
              <a-dropdown trigger="click" placement="bottomLeft">
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="delete" @click="handleSessionDelete(session)">
                      <DeleteFilled :style="{ color: 'var(--color-error)' }" />
                      {{ $t("common.delete") }}</a-menu-item
                    >
                  </a-menu>
                </template>
                <a-button type="text" class="dots-btn" @click.prevent> ⋮ </a-button>
              </a-dropdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { getAgentList, requestAgentUpdate } from "@/api/agent";
  import { getHistorySessionList, requestSessionDelete } from "@/api/chatbot";
  import router from "@/router";
  import { chatbotAppStore } from "@/store/chatbot";
  import { sessionAppStore } from "@/store/session";
  import emitter from "@/utils/mitt";
  import { CloseCircleFilled, DeleteFilled, MessageOutlined } from "@ant-design/icons-vue";
  import { Modal } from "ant-design-vue";
  import { createVNode, onMounted, ref, watch } from "vue";
  import { useI18n } from "vue-i18n";

  const chatbotStore = chatbotAppStore();
  const sessionStore = sessionAppStore();
  const route = useRoute();
  const { t } = useI18n();

  const props = defineProps({
    isCollapsed: {
      type: Boolean,
      default: false,
    },
  });

  type AgentItem = {
    id: string;
    name: string;
    type: string;
    active: boolean;
    icon?: string;
  };
  type sessionItem = { id: string; name: string };

  const agentsList = ref<AgentItem[]>([]);
  const sessionList = ref<sessionItem[]>([]);
  const selectedSessionId = ref<string>("");
  const sessionHovering = ref(false);
  const sessionListRef = ref<HTMLElement | null>(null);

  const isSessionSelected = (id: string) => selectedSessionId.value === id;

  const getAgentIcon = (agent: EmptyObjectType) => {
    const { type } = agent;
    if (type === "deep_search") {
      return "icon-deep_search";
    } else {
      return "icon-simple-robot";
    }
  };

  const handleAgentClick = (agent: AgentItem, index: number) => {
    const { active } = agent;
    const { name, type } = agent;

    const text = active ? t("agent.deactivateTip") : t("agent.activeTip");
    Modal.confirm({
      title: t("common.prompt"),
      content: text,
      okText: t("common.confirm"),
      async onOk() {
        await requestAgentUpdate(name, { active: !active });
        queryAgentList();
        if (!active) {
          handleThinkState();
          chatbotStore.setAgent({
            name,
            type,
            index,
          });
        } else {
          emitter.emit("chat-style", null);
          chatbotStore.setAgent({ name: "", type: "", index: 0 });
          handleThinkState(true);
        }
      },
    });
  };

  const handleThinkState = (value: boolean = false) => {
    const { chat_template_kwargs } = chatbotStore.configuration;
    const chat_template = {
      ...chat_template_kwargs,
      enable_thinking: value,
    };
    chatbotStore.setChatbotConfiguration({
      chat_template_kwargs: chat_template,
    });
  };

  const handleSessionClick = (session: sessionItem) => {
    selectedSessionId.value = session.id;
    sessionStore.setSessionId(session.id);
    router.replace({
      query: {
        sessionId: session.id,
      },
    });
  };

  const handleNewChat = () => {
    emitter.emit("new-chat");
    selectedSessionId.value = "";
  };

  const queryAgentList = async () => {
    try {
      const data: any = await getAgentList();
      agentsList.value = Object.values(data);
      const index = data.findIndex((item: AgentItem) => item.active);
      if (index !== -1) {
        const agent = data[index];
        handleThinkState();
        const { name, type } = agent;
        chatbotStore.setAgent({
          name,
          type,
          index,
        });
      } else {
        chatbotStore.setAgent({ name: "", type: "", index: 0 });
      }
    } catch (error) {
      console.error(error);
    }
  };

  const querySessionList = async () => {
    try {
      const data: any = await getHistorySessionList();
      sessionList.value = Object.entries(data).map(([id, name]) => ({
        id,
        name: name as string,
      }));
    } catch (error) {
      console.error(error);
    }
  };

  const getActiveStyles = (index: number) => {
    const colorIndex = (index % 5) + 1;
    return {
      backgroundColor: `var(--color-multicolored-${colorIndex}) `,
    };
  };

  const handleSessionDelete = (row: EmptyObjectType) => {
    Modal.confirm({
      title: t("common.delete"),
      icon: createVNode(CloseCircleFilled, { class: "error-icon" }),
      content: t("agent.deleteTip"),
      okText: t("common.confirm"),
      okType: "danger",
      async onOk() {
        const { id } = row;
        await requestSessionDelete(id);
        if (selectedSessionId.value === id) {
          selectedSessionId.value = "";
          sessionStore.setSessionId("");
          router.replace({ query: {} });
        }
        querySessionList();
      },
    });
  };

  const handleCreateAgent = () => {
    router.push({ name: "Settings" });
  };

  watch(
    () => route.query?.sessionId,
    sessionId => {
      if (sessionId) {
        const sessionIdStr = String(sessionId);
        if (selectedSessionId.value !== sessionIdStr) {
          selectedSessionId.value = sessionIdStr;
        }
        const isExist = sessionList.value.some(item => item.id === sessionIdStr);
        if (!isExist) {
          querySessionList();
        }
        const storedSessionId = sessionStore.currentSession;
        if (storedSessionId !== sessionIdStr) {
          sessionStore.setSessionId(sessionIdStr);
        }
      } else {
        selectedSessionId.value = "";
      }
    },
    { immediate: true }
  );

  onMounted(() => {
    queryAgentList();
    querySessionList();
  });
</script>

<style lang="less" scoped>
  .chat-agent {
    display: flex;
    flex-direction: column;
    width: 260px;
    height: 100%;
    min-height: 0;
    border-right: 1px solid var(--border-main-color);
    padding: 16px 12px 12px 12px;
    box-sizing: border-box;
    transition: all 0.3s ease;

    &.collapsed {
      width: 60px;
      padding: 16px 8px 12px 8px;

      .header-section {
        justify-content: center;
      }

      .new-chat {
        justify-content: center;
        padding: 6px;
        width: 40px;
        height: 40px;
      }

      .section-title {
        display: none;
      }

      .agent-menu {
        .agent-item {
          justify-content: center;
          padding: 10px;

          .agent-title {
            display: none;
          }
        }
      }

      .session-wrapper {
        .session-item {
          padding: 0;
          .session-texts {
            padding: 0;
            .session-icon {
              margin-right: 0;
            }

            .session-title {
              display: none;
            }
            .session-icon {
              padding: 8px;
            }
          }
        }
      }
    }

    .header-section {
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: relative;
      margin-bottom: 12px;
    }

    .new-chat {
      display: flex;
      align-items: center;
      gap: 6px;
      width: 100%;
      padding: 6px 12px;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 500;
      color: var(--color-primary);
      border: 1px solid var(--color-primary-tip);
      background-color: var(--color-second-primaryBg);
      transition: all 0.2s ease;

      &:hover {
        background-color: var(--color-primary-hover);
        color: var(--color-white);
      }
    }

    .intel-divider {
      margin: 12px 0;
    }

    .agentsList-wrap {
      .agent-menu {
        .agent-item {
          display: flex;
          align-items: center;
          padding: 10px;
          cursor: pointer;
          border-radius: 6px;
          margin-bottom: 6px;
          transition: background 0.15s;
          gap: 10px;

          .agent-title {
            font-size: 16px;
            transition: opacity 0.3s ease;
          }

          &:hover {
            background: var(--color-second-primaryBg);
          }

          &.selected {
            color: var(--color-white);
          }

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }

  .section-title {
    color: var(--font-tip-color);
    font-size: 12px;
    transition: opacity 0.3s ease;
  }

  .session-wrapper {
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;

    .session-list {
      overflow-y: auto;
      padding-right: 6px;
      margin-top: 6px;
      scrollbar-width: none;
      -ms-overflow-style: none;

      &::-webkit-scrollbar {
        width: 0;
        height: 0;
      }
    }

    &:hover {
      .session-list,
      .session-list.show-scroll {
        scrollbar-width: thin;
      }

      .session-list::-webkit-scrollbar,
      .session-list.show-scroll::-webkit-scrollbar {
        width: 8px;
      }

      .session-list::-webkit-scrollbar-thumb,
      .session-list.show-scroll::-webkit-scrollbar-thumb {
        border-radius: 4px;
      }
    }
  }

  .session-item {
    padding: 8px;
    border-radius: 6px;
    cursor: pointer;
    margin-bottom: 6px;
    transition: background 0.12s;
    display: flex;
    align-items: center;
    border-left: 3px solid transparent;

    .session-actions {
      display: flex;
      align-items: center;
      visibility: hidden;
      width: 16px;
    }

    .session-main {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .session-texts {
        overflow: hidden;
        padding-right: 8px;
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 1;
      }

      .session-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
      }

      .session-title {
        font-size: 14px;
        color: var(--font-main-color);
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
        transition: opacity 0.3s ease;
      }

      .dots-btn {
        border: none;
        padding: 0 6px;
        height: 24px;
        line-height: 24px;
        background: transparent;
        cursor: pointer;
        border-radius: 4px;
      }

      .dots-btn:hover {
        background: var(--color-fuzzy-white);
      }
    }

    &:hover {
      background: var(--color-second-primaryBg);

      .session-actions {
        visibility: visible;
      }
    }

    &.selected {
      background: var(--color-second-primaryBg);
      border-left: 3px solid var(--color-primary-second);

      .session-title,
      .session-icon {
        color: var(--color-primary);
      }
    }
  }
</style>
