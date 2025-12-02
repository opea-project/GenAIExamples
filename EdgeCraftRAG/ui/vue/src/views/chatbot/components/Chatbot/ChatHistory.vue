<template>
  <div class="chat-agent">
    <div class="new-chat" @click="handleNewChat">
      <SvgIcon name="icon-newChat" :size="20" inherit />
      {{ $t("chat.new") }}
    </div>
    <a-divider />
    <div class="agentsList-wrap">
      <div class="section-title mb-6">{{ $t("agent.agent") }}</div>
      <a-empty v-if="!agentsList?.length">
        <a-button
          type="primary"
          ghost
          size="small"
          @click="handleCreateAgent"
          >{{ $t("common.manual") }}</a-button
        >
      </a-empty>
      <div class="agent-menu">
        <div
          v-for="(agent, index) in agentsList"
          :key="index"
          :class="['agent-item', { selected: agent.active }]"
          :style="agent.active ? getActiveStyles(index) : {}"
          @click="() => handleAgentClick(agent, index)"
        >
          <span class="agent-icon">
            <SvgIcon :name="getAgentIcon(agent)" inherit />
          </span>
          <span class="agent-title">{{ agent.name }}</span>
        </div>
      </div>
    </div>
    <a-divider />
    <div
      class="session-wrapper"
      @mouseenter="sessionHovering = true"
      @mouseleave="sessionHovering = false"
    >
      <div class="section-title">{{ $t("chat.history") }}</div>
      <div
        class="session-list"
        ref="sessionListRef"
        :class="{ 'show-scroll': sessionHovering }"
      >
        <div
          v-for="session in sessionList"
          :key="session.id"
          :class="['session-item', { selected: isSessionSelected(session.id) }]"
          @click="() => handleSessionClick(session)"
        >
          <div class="session-main">
            <div class="session-texts">
              <div class="session-title" :title="session.name">
                {{ session.name }}
              </div>
            </div>
            <div class="session-actions" @click.stop v-if="false">
              <a-dropdown trigger="click" placement="bottomLeft">
                <template #overlay>
                  <a-menu>
                    <a-menu-item
                      key="delete"
                      @click="handleSessionDelete(session)"
                    >
                      <DeleteFilled :style="{ color: 'var(--color-error)' }" />
                      {{ $t("common.delete") }}</a-menu-item
                    >
                  </a-menu>
                </template>
                <a-button type="text" class="dots-btn" @click.prevent>
                  ⋮
                </a-button>
              </a-dropdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createVNode, ref } from "vue";
import { DeleteFilled, CloseCircleFilled } from "@ant-design/icons-vue";
import { Modal } from "ant-design-vue";
import { useI18n } from "vue-i18n";
import router from "@/router";
import { getAgentList, requestAgentUpdate } from "@/api/agent";
import { requestSessionDelete, getHistorySessionList } from "@/api/chatbot";
import { chatbotAppStore } from "@/store/chatbot";
import { sessionAppStore } from "@/store/session";
import emitter from "@/utils/mitt";

const chatbotStore = chatbotAppStore();
const sessionStore = sessionAppStore();
const route = useRoute();
const { t } = useI18n();

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

//delete
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
  (sessionId) => {
    if (sessionId) {
      const sessionIdStr = String(sessionId);
      if (selectedSessionId.value !== sessionIdStr) {
        selectedSessionId.value = sessionIdStr;
      }
      const isExist = sessionList.value.some(
        (item) => item.id === sessionIdStr
      );
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
  .intel-divider {
    margin: 12px 0;
  }
  .new-chat {
    .mb-6;
    .flex-left;
    gap: 6px;
    width: 100%;
    padding: 6px 12px;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 500;
    color: var(--color-primary);
    border: 1px solid var(--color-primary-tip);
    background-color: var(--color-second-primaryBg);
    &:hover {
      background-color: var(--color-primary-hover);
      color: var(--color-white);
    }
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
        .agent-icon {
          width: 22px;
          display: inline-block;
          text-align: center;
          margin-right: 10px;
        }
        .agent-title {
          font-size: 16px;
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
  }
  .session-main {
    width: 100%;
    .flex-between;
    .session-texts {
      overflow: hidden;
      padding-right: 8px;
    }

    .session-title {
      font-size: 14px;
      color: var(--font-main-color);
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
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

    .session-title {
      color: var(--color-primary);
    }
  }
}
</style>
