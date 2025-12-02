<template>
  <div id="message-container">
    <template v-if="message.role === 'assistant'">
      <div class="chatbot-session">
        <div class="avatar-wrap">
          <SvgIcon
            :name="fixedAgentStyle.icon"
            :size="22"
            :style="{ color: 'var(--color-primary)' }"
            inherit
          />
        </div>
        <div class="message-wrap agent-wrap" :style="fixedAgentStyle.styleVars">
          <div v-if="inResponse && !props.message?.content" class="dot-loader">
            <span class="drop" v-for="index in 3" :key="index"></span>
          </div>
          <div class="think-container" v-if="shouldShowThinkContainer">
            <div
              :class="{
                'think-title': true,
                'completed-icon': isThinkEnd,
              }"
            >
              <div
                :class="{
                  'title-bg': isThinkEnd,
                }"
                @click="toggleThink"
              >
                <span>
                  {{
                    isThinkEnd ? $t("chat.thinkEnd") : $t("chat.thinkStart")
                  }}</span
                >
                <UpOutlined
                  v-if="isThinkEnd"
                  :class="['toggle-icon', { rotate: isCollapsed }]"
                />
              </div>
            </div>
            <div class="think-msg-wrap" v-show="isCollapsed">
              <div class="state-wrap">
                <div v-if="isThinkEnd" class="completed-icon">
                  <CheckCircleFilled />
                </div>
                <div v-else class="state-icon"></div>
              </div>
              <div
                class="think-message"
                v-html="thinkMarkdown"
                ref="thinkElement"
              ></div>
            </div>
          </div>
          <div class="agent-container" v-if="agentBlocks.length > 0">
            <div
              v-for="(agent, index) in agentBlocks"
              :key="`agent-${index}`"
              class="agent-block"
            >
              <div class="agent-header" @click="toggleAgent(index)">
                <div class="agent-title">
                  <SvgIcon name="icon-agent" :size="16" />
                  <span class="title-wrap">
                    <span v-if="agent.title" v-html="agent.title"></span>
                    <span v-else>{{ $t("agent.think") }} {{ index + 1 }}</span>
                    <SvgIcon
                      v-if="!agent.completed"
                      name="icon-loading1"
                      :size="18"
                      inherit
                  /></span>
                </div>
                <UpOutlined
                  v-if="!agent.nofold"
                  :class="[
                    'agent-toggle-icon',
                    { rotate: !agentStates[index]?.collapsed },
                  ]"
                />
              </div>
              <div
                class="agent-content"
                v-show="shouldShowAgentContent(agent, index)"
              >
                <div
                  class="agent-message"
                  v-html="formatAgentContent(agent.content)"
                ></div>
              </div>
            </div>
          </div>
          <div v-if="shouldShowMainContent" v-html="renderedMainMarkdown"></div>
          <div v-if="!inResponse && readResponse" class="footer-btn">
            <a-tooltip
              placement="top"
              :title="$t('common.copy')"
              v-if="readResponse.length"
            >
              <span class="icon-style" @click="handleCopyResponses()">
                <CopyOutlined /></span
            ></a-tooltip>
            <a-tooltip
              v-if="lastResponse"
              placement="top"
              :title="$t('common.regenerate')"
            >
              <span class="icon-style" @click="handleRegenerate()">
                <SyncOutlined /></span
            ></a-tooltip>
          </div>
        </div>
      </div>
      <div
        v-if="benchmarkData.generator"
        :class="['benchmark-wrap', isExpanded ? 'expanded' : 'retract']"
      >
        <span class="item-tag">
          <SvgIcon name="icon-generation" :size="14" />
          Generation: {{ benchmarkData.generator }}s
        </span>
        <transition appear name="detail-transition">
          <div v-if="isExpanded" class="detail-wrap">
            <span class="item-tag">
              <SvgIcon name="icon-search-time" :size="14" />
              Retrieval: {{ benchmarkData.retriever }}s
            </span>
            <span class="item-tag">
              <SvgIcon name="icon-handle-time" :size="14" />
              Post-process: {{ benchmarkData.postprocessor }}s
            </span>
          </div></transition
        >
        <SvgIcon
          :name="isExpanded ? 'icon-time-retract' : 'icon-time-expand'"
          :size="16"
          class="expanded-icon"
          @click="toggleTabs"
        />
      </div>
    </template>
    <div v-else class="user-session">
      <template v-if="editState">
        <div class="input-wrap">
          <a-textarea
            v-model:value.trim="queryInput"
            :bordered="false"
            :auto-size="{ minRows: 1, maxRows: 2 }"
          />
          <div class="button-wrap">
            <a-button shape="round" @click="handleCancel">
              {{ $t("common.cancel") }}
            </a-button>
            <a-button
              type="primary"
              shape="round"
              @click="handleSend"
              :disabled="!queryInput"
            >
              {{ $t("common.send") }}
            </a-button>
          </div>
        </div>
      </template>
      <template v-else>
        <a-tooltip
          v-if="message.errorMessage"
          placement="left"
          color="var(--bg-card-color)"
          :overlayInnerStyle="{
            color: 'var(--font-text-color)',
            border: '1px solid var(--color-error)',
          }"
        >
          <template #title>
            <SvgIcon
              name="icon-chatbot1"
              class="mr-6"
              :size="20"
              :style="{
                color: 'var(--color-error)',
              }"
            />{{ message.errorMessage }}</template
          >
          <ExclamationCircleFilled class="error-icon"
        /></a-tooltip>
        <div class="message-wrap">
          {{ message.content }}
          <div class="footer-btn">
            <a-tooltip placement="top" :title="$t('common.copy')">
              <span class="icon-style" @click="handleCopyQuery()">
                <CopyOutlined /></span
            ></a-tooltip>
            <a-tooltip
              v-if="!inResponse && lastQuery"
              placement="top"
              :title="$t('common.edit')"
            >
              <span class="icon-style" @click="handleEdit()">
                <EditOutlined /></span
            ></a-tooltip>
            <a-tooltip
              v-if="!inResponse && message.errorMessage && lastQuery"
              placement="top"
              :title="$t('common.regenerate')"
            >
              <span class="icon-style" @click="handleRetry()">
                <SyncOutlined /></span
            ></a-tooltip>
          </div>
        </div>
      </template>
      <div class="user-wrap">
        <SvgIcon name="icon-user" inherit :size="22" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="MessageItem">
import { marked } from "marked";
import { PropType, ref, onMounted, computed, watch } from "vue";
import {
  CheckCircleFilled,
  UpOutlined,
  CopyOutlined,
  SyncOutlined,
  EditOutlined,
  ExclamationCircleFilled,
} from "@ant-design/icons-vue";
import { IMessage, Benchmark } from "../../type";
import CustomRenderer from "@/utils/customRenderer";
import { useClipboard } from "@/utils/clipboard";
import "highlight.js/styles/atom-one-dark.css";
import { chatbotAppStore } from "@/store/chatbot";

const chatbotStore = chatbotAppStore();
const { copy } = useClipboard();

const props = defineProps({
  message: {
    type: Object as PropType<IMessage>,
    required: true,
    default: () => {},
  },
  inResponse: {
    type: Boolean,
    required: true,
  },
  messageIndex: {
    type: Number,
  },
  lastQuery: {
    type: Boolean,
    default: false,
  },
  lastResponse: {
    type: Boolean,
    default: false,
  },
  messageKey: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["preview", "stop", "regenerate", "resend"]);

type AgentItem = { id: string; icon?: string; css?: string };

const agentsList = ref<AgentItem[]>([
  {
    id: "simple",
    icon: "icon-simple-robot",
    css: "agent-simple",
  },
  {
    id: "deep_search",
    icon: "icon-deep_search",
    css: "agent-recursive",
  },
]);

interface AgentBlock {
  content: string;
  title: string;
  completed: boolean;
  startIndex: number;
  endIndex?: number;
  nofold?: boolean;
  hasSetInitialState?: boolean;
}

const agentBlocks = ref<AgentBlock[]>([]);
const agentStates = ref<Record<number, { collapsed: boolean }>>({});

const benchmarkData = computed<Benchmark>(() => {
  return (props.message?.benchmark || {}) as Benchmark;
});
const isExpanded = ref<boolean>(false);
const isCollapsed = ref(true);
const editState = ref<boolean>(false);
const queryInput = ref<string>(props.message.content);

interface FixedAgentStyle {
  icon: string;
  css: string;
  styleVars: Record<string, string>;
}

const fixedAgentStyle = ref<FixedAgentStyle>({
  icon: "icon-chatbot",
  css: "",
  styleVars: {},
});

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});

const isThinkInsideAgent = computed(() => {
  const content = props.message.content || "";
  const thinkStartIndex = content.indexOf("<think>");

  if (thinkStartIndex === -1) return false;

  return agentBlocks.value.some((agent) => {
    return (
      agent.startIndex < thinkStartIndex &&
      (agent.endIndex === undefined || thinkStartIndex < agent.endIndex)
    );
  });
});

const hasThinkContent = computed(() => {
  return (
    props.message.content?.includes("<think>") && !isThinkInsideAgent.value
  );
});

const isThinkEnd = computed(() => {
  return (
    props.message.content?.includes("</think>") && !isThinkInsideAgent.value
  );
});

const thinkContent = computed(() => {
  if (!hasThinkContent.value) return "";

  const content = props.message.content;
  const startIndex = content.indexOf("<think>") + 7;
  const endIndex = isThinkEnd.value
    ? content.indexOf("</think>")
    : content.length;

  return content.substring(startIndex, endIndex);
});

const shouldShowThinkContainer = computed(() => {
  return hasThinkContent.value && thinkContent.value.trim().length > 0;
});

const parseAttributes = (attrString: string): Record<string, string> => {
  const attrs: Record<string, string> = {};
  const attrRegex = /(\w+)\s*=\s*("([^"]*)"|'([^']*)'|([^\s>]+))/g;
  let match;

  while ((match = attrRegex.exec(attrString)) !== null) {
    const key = match[1];
    const value = match[3] || match[4] || match[5] || "";
    attrs[key] = value.trim();
  }

  return attrs;
};

const parseAgentContentIncremental = (
  content: string,
  previousBlocks: AgentBlock[]
): AgentBlock[] => {
  const blocks = [...previousBlocks];
  let currentIndex = 0;

  while (currentIndex < content.length) {
    const startTag = content.indexOf("<agent", currentIndex);
    if (startTag === -1) break;

    const endOfStartTag = content.indexOf(">", startTag);
    if (endOfStartTag === -1) break;

    const attributes = content.substring(startTag + 6, endOfStartTag).trim();
    const attrs = parseAttributes(attributes);

    const title = attrs.title || "";
    const tag = attrs?.tag || "";

    const endTag = content.indexOf("</agent>", endOfStartTag);

    if (endTag !== -1) {
      const agentContent = content.substring(endOfStartTag + 1, endTag).trim();

      const existingBlockIndex = blocks.findIndex(
        (block) => block.startIndex === startTag
      );

      if (existingBlockIndex !== -1) {
        blocks[existingBlockIndex].content = agentContent;
        if (title) {
          blocks[existingBlockIndex].title = title;
        }
        blocks[existingBlockIndex].completed = true;
        blocks[existingBlockIndex].endIndex = endTag + 8;
        blocks[existingBlockIndex].nofold = tag === "nofold";
        if (!blocks[existingBlockIndex].hasSetInitialState) {
          if (tag === "nofold") {
            agentStates.value[existingBlockIndex] = {
              collapsed: !agentContent.trim(),
            };
          } else {
            agentStates.value[existingBlockIndex] = { collapsed: true };
          }
          blocks[existingBlockIndex].hasSetInitialState = true;
        }
      } else {
        const newBlock: AgentBlock = {
          content: agentContent,
          title: title,
          completed: true,
          nofold: tag === "nofold",
          startIndex: startTag,
          endIndex: endTag + 8,
          hasSetInitialState: true,
        };
        blocks.push(newBlock);

        const newIndex = blocks.length - 1;
        if (tag === "nofold") {
          agentStates.value[newIndex] = {
            collapsed: !agentContent.trim(),
          };
        } else {
          agentStates.value[newIndex] = { collapsed: true };
        }
      }

      currentIndex = endTag + 8;
    } else {
      const agentContent = content.substring(endOfStartTag + 1).trim();

      const existingBlockIndex = blocks.findIndex(
        (block) => block.startIndex === startTag && !block.completed
      );

      if (existingBlockIndex !== -1) {
        blocks[existingBlockIndex].content = agentContent;
        if (title) {
          blocks[existingBlockIndex].title = title;
        }
      } else {
        const newBlock: AgentBlock = {
          content: agentContent,
          title: title,
          completed: false,
          nofold: tag === "nofold",
          startIndex: startTag,
          hasSetInitialState: false,
        };
        blocks.push(newBlock);

        const newIndex = blocks.length - 1;
        if (!agentStates.value[newIndex]) {
          agentStates.value[newIndex] = { collapsed: false };
        }
      }

      break;
    }
  }

  return blocks;
};

const getMainContent = (content: string, agentBlocks: AgentBlock[]): string => {
  if (!content) return "";

  let result = content;

  if (!agentBlocks.length) {
    return result.replace(/\x1b\[[0-9;]*m/g, "").trim();
  }

  const sortedBlocks = [...agentBlocks].sort(
    (a, b) => (b.startIndex || 0) - (a.startIndex || 0)
  );

  for (const block of sortedBlocks) {
    if (block.completed && block.endIndex !== undefined) {
      result =
        result.substring(0, block.startIndex) +
        result.substring(block.endIndex);
    } else {
      result = result.substring(0, block.startIndex);
    }
  }

  result = result.replace(/\x1b\[[0-9;]*m/g, "");

  return result.trim();
};

const formatAgentContent = (content: string) => {
  const cleanedContent = content.replace(/\x1b\[[0-9;]*m/g, "");
  return marked(cleanedContent);
};

const shouldShowAgentContent = (agent: AgentBlock, index: number): boolean => {
  if (agent.nofold) {
    return !!agent.content.trim();
  }
  return !agentStates.value[index]?.collapsed;
};

const thinkMarkdown = computed(() => {
  return marked(thinkContent.value);
});

const readResponse = computed(() => {
  const content = props.message?.content || "";
  if (!content) return "";

  if (!hasThinkContent.value) {
    return content;
  }

  if (!isThinkEnd.value) {
    return "";
  }

  const thinkEndIndex = content.indexOf("</think>");
  if (thinkEndIndex !== -1) {
    return content.substring(thinkEndIndex + 8);
  }

  return content;
});

const mainContent = computed(() => {
  return getMainContent(readResponse.value, agentBlocks.value);
});

const shouldShowMainContent = computed(() => {
  return mainContent.value && (!hasThinkContent.value || isThinkEnd.value);
});

const renderedMainMarkdown = computed(() => {
  return marked(mainContent.value);
});

const calculateAgentStyle = () => {
  const agent = agentsList.value.find(
    (item) => item.id === chatbotStore.agent?.type
  );

  const colorIndex = (chatbotStore.agent.index % 5) + 1;

  const styleVars = {
    "--agent-bg-var": `var(--color-multicolored-bg-${colorIndex})`,
    "--agent-border-var": `var(--color-multicolored-border-${colorIndex})`,
  };

  return {
    icon: agent?.icon || "icon-chatbot",
    css: agent?.css || "",
    styleVars,
  };
};

const resetAgentState = () => {
  agentBlocks.value = [];
  agentStates.value = {};
};

const toggleAgent = (index: number) => {
  if (agentBlocks.value[index]?.nofold) {
    return;
  }
  if (!agentStates.value[index]) {
    agentStates.value[index] = { collapsed: false };
  }
  agentStates.value[index].collapsed = !agentStates.value[index].collapsed;
};

const toggleTabs = () => {
  isExpanded.value = !isExpanded.value;
};

const toggleThink = () => {
  if (!isThinkEnd.value) return;
  emit("stop");
  isCollapsed.value = !isCollapsed.value;
};

const addClickListeners = () => {
  const images = document.querySelectorAll("#message-container img");

  images.forEach((img) => {
    img.addEventListener("click", (event) => {
      const target = event.target as HTMLImageElement;
      if (target && target.tagName.toLowerCase() === "img") {
        emit("preview", target.src);
      }
    });
  });
};

const handleRegenerate = () => {
  const { query = "" } = props.message;
  if (!query) return;
  emit("regenerate", query);
};

const handleRetry = () => {
  emit("resend", { index: props.messageIndex, query: queryInput.value });
};

const handleCopyQuery = async () => {
  await copy(queryInput.value);
};

const handleCopyResponses = async () => {
  await copy(readResponse.value);
};

const handleEdit = () => {
  queryInput.value = props.message.content;
  editState.value = true;
};

const handleCancel = () => {
  editState.value = false;
};

const handleSend = () => {
  if (!queryInput.value) return;
  emit("resend", { index: props.messageIndex, query: queryInput.value });
  handleCancel();
};

watch(
  () => props.messageKey,
  (newKey, oldKey) => {
    if (newKey !== oldKey) {
      resetAgentState();
      if (props.message?.content) {
        agentBlocks.value = parseAgentContentIncremental(
          props.message.content,
          []
        );
      }
    }
  }
);

watch(
  () => props.message.content,
  (newContent, oldContent) => {
    if (
      newContent &&
      oldContent &&
      !newContent.includes(oldContent) &&
      !oldContent.includes(newContent)
    ) {
      resetAgentState();
    }

    if (newContent) {
      agentBlocks.value = parseAgentContentIncremental(
        newContent,
        agentBlocks.value
      );
    } else {
      resetAgentState();
    }
  },
  { immediate: true }
);

watch(
  () => props.message.role,
  (newRole, oldRole) => {
    if (newRole !== oldRole) {
      resetAgentState();
    }
  }
);

watch(
  () => props.inResponse,
  (newValue) => {
    if (!newValue) {
      addClickListeners();
    }
  }
);

watch(
  () => isThinkEnd.value,
  (value) => {
    if (value) {
      isCollapsed.value = false;
    }
  }
);

onMounted(() => {
  fixedAgentStyle.value = calculateAgentStyle();

  if (props.message?.content) {
    agentBlocks.value = parseAgentContentIncremental(props.message.content, []);
  }
});
</script>

<style lang="less" scoped>
@keyframes expandIcon {
  from {
    width: 250px;
    left: 0;
    transform: none;
  }
  to {
    width: 700px;
    left: 0;
    transform: none;
  }
}
@keyframes retractIcon {
  from {
    width: 700px;
    left: 0;
    transform: none;
  }
  to {
    width: 250px;
    left: 0;
    transform: none;
  }
}
@keyframes breath-animation {
  75%,
  100% {
    opacity: 0;
    transform: scale(2);
  }
}
@keyframes dotPulse {
  0% {
    background-color: var(--bg-card-color);
    transform: scale(1);
  }
  50% {
    background-color: var(--font-tip-color);
    transform: scale(1.4);
  }
  100% {
    background-color: var(--bg-card-color);
    transform: scale(1);
  }
}
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.agent-container {
  margin: 12px 0;
}

.agent-block {
  border: 1px solid var(--color-primary-light);
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px var(--bg-box-shadow);
  border: 1px solid var(--agent-border-var);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: rgba(from var(--agent-bg-var) r g b / 0.7);
  &:hover {
    background-color: var(--agent-bg-var);
  }
  .icon-loading1 {
    animation: spin 3s linear infinite;
    position: relative;
    top: 3px;
    left: 4px;
  }
  .agent-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: var(--color-primary);
    font-size: 14px;
    .title-wrap {
      flex: 1;
    }
  }

  .agent-toggle-icon {
    transition: transform 0.3s ease;
    color: var(--color-info);
    font-size: 14px;
  }

  .agent-toggle-icon.rotate {
    transform: rotate(180deg);
  }
}

.agent-content {
  background: var(--bg-content-color);
}
.agent-message {
  padding: 16px;
  line-height: 1.6;
  font-size: 14px;
  color: var(--font-text-color);
}

.chatbot-session {
  margin-bottom: 16px;
  font-size: 16px;
  text-align: left;
  position: relative;
}
.avatar-wrap {
  background-color: var(--color-primaryBg);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  .vertical-center;
  position: absolute;
  left: -48px;
}
.user-wrap {
  background-color: var(--color-scrollbar);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  .vertical-center;
  position: absolute;
  right: -48px;
}
.message-wrap {
  background-color: var(--bg-content-color);
  border-radius: 6px;
  line-height: 22px;
  min-height: 36px;
  padding: 12px 16px;
  width: 100%;
}

.agent-wrap {
  background: linear-gradient(
    to bottom right,
    rgb(from var(--agent-bg-var) r g b / 0.4),
    rgb(from var(--bg-content-color) r g b / 0.4),
    var(--bg-content-color)
  );
}

.user-session {
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-size: 16px;
  text-align: end;
  position: relative;
  .message-wrap {
    background-color: var(--message-bg);
    width: auto;
    text-align: left;
    position: relative;
    .footer-btn {
      position: absolute;
      bottom: -24px;
      right: 0;
      z-index: 20;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.3s ease, visibility 0s linear 2s;
      gap: 8px;
      .anticon {
        cursor: pointer;
        &:hover {
          color: var(--color-primary-hover);
        }
      }
    }
    &:hover .footer-btn {
      opacity: 1;
      visibility: visible;
      transition: opacity 0.3s ease;
    }
  }
  .error-icon {
    font-size: 18px;
    color: var(--color-error);
    .mr-8;
  }
}
.benchmark-wrap {
  .flex-left;
  margin-bottom: 20px;
  gap: 12px;
  position: relative;
  top: -8px;
  transition: none;
  overflow: hidden;
  &.expanded {
    animation: expandIcon 1s forwards;
  }
  &.retract {
    animation: retractIcon 1s forwards;
  }
  .detail-wrap {
    .flex-left;
    gap: 12px;
  }
  .item-tag {
    white-space: nowrap;
    padding: 8px 12px;
    border-radius: 8px;
    .vertical-center;
    background-color: var(--bg-card-color);
    gap: 4px;
    .icon-intel {
      color: var(--color-primary) !important;
    }
  }
  .expanded-icon {
    cursor: pointer;
    position: relative;
    left: -4px;
  }
}

.detail-transition-enter-active,
.detail-transition-leave-active {
  transition: all 0.7s ease-in-out;
}
.think-container {
  color: var(--font-think-color);
  background: var(--think-done-bg);
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 12px;
  border-radius: 6px;
  transition: 0.3s background cubic-bezier(0.4, 0, 0.2, 1);
  .think-title {
    line-height: 24px;
    letter-spacing: 0.25px;
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    position: relative;
    width: 100%;
    min-width: 200px;
    &::before {
      content: "";
      display: inline-block;
      background: url("@/assets/images/think-reasoning.png") no-repeat center
        center;
      background-size: 100% 100%;
      width: 18px;
      height: 18px;
      margin-right: 6px;
    }
    &.completed-icon {
      &::before {
        background: url("@/assets/images/think-completed.png") no-repeat center
          center;
        background-size: 100% 100%;
      }
    }
    .title-bg {
      width: 100%;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 4px 4px 4px 6px;
      transition: 0.3s background-color;
      &:hover {
        background-color: var(--border-main-color);
        cursor: pointer;
      }
    }
    .toggle-icon {
      font-size: 16px;
      color: var(--font-tip-color);
      transition: transform 0.3s ease;
      transform: none;
      &.rotate {
        transform: rotate(180deg);
        transition: transform 0.3s ease;
      }
    }
  }
  .think-msg-wrap {
    display: flex;
    gap: 8px;
    width: 100%;
    font-size: 14px;
    .state-wrap {
      width: 18px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
      &::after {
        content: "";
        width: 1px;
        height: 100%;
        background: var(--border-main-color);
        border-radius: 13px;
        transition: 0.3s background cubic-bezier(0.4, 0, 0.2, 1);
      }
      .completed-icon {
        margin-bottom: 4px;
        font-size: 14px;
        color: var(--think-done-icon);
      }
      .state-icon {
        width: 16px;
        height: 16px;
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-bottom: 8px;
        margin-top: 2px;
        &::before {
          content: "";
          position: absolute;
          transform-origin: center;
          width: 8px;
          height: 8px;
          border-radius: 100%;
          background-color: var(--think-done-icon);
        }
        &::after {
          position: absolute;
          content: "";
          width: 10px;
          height: 10px;
          border: 2px solid var(--think-done-icon);
          box-sizing: border-box;
          border-radius: 100%;
          background-color: transparent;
          animation: breath-animation 1.6s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
      }
    }
    .think-message {
      line-height: 24px;
      flex: 1;
    }
  }
}
.think-transition-enter-active,
.think-transition-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.think-transition-enter-from,
.think-transition-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
.dot-loader {
  display: flex;
  align-items: center;
  height: 12px;
  gap: 8px;
  .drop {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--bg-card-color);
    animation: dotPulse 1.2s infinite ease-in-out;
    &:nth-child(1) {
      animation-delay: 0s;
    }
    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}
.footer-btn {
  .flex-end;
  .mt-8;
  gap: 8px;
  font-size: 14px;
  color: var(--font-tip-color);
  .anticon {
    cursor: pointer;
    &:hover {
      color: var(--color-primary-hover);
    }
  }
}
.input-wrap {
  padding: 4px;
  border: 1px solid var(--color-primary);
  border-radius: 20px;
  background-color: var(--input-bg);
  max-width: 960px;
  min-width: 500px;
  transition: all 0.2s;
  width: 100%;
  display: flow-root;
  position: relative;
  left: -2px;
  text-align: center;

  &:hover {
    box-shadow: 0 4px 12px var(--bg-primary-shadow);
    border: 1px solid var(--color-primary-hover);
  }
  textarea {
    resize: none;
  }

  .button-wrap {
    .flex-end;
    padding: 6px 12px;
  }
}
</style>
