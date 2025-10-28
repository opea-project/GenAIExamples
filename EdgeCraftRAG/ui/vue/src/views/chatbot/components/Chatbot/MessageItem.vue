<template>
  <div id="message-container">
    <template v-if="message.role === 'assistant'">
      <div class="chatbot-session">
        <div class="avatar-wrap">
          <SvgIcon
            name="icon-chatbot"
            :size="24"
            :style="{ color: 'var(--color-primary)' }"
          />
        </div>
        <div class="message-wrap">
          <div v-if="inResponse && !props.message?.content" class="dot-loader">
            <span class="drop" v-for="index in 3" :key="index"></span>
          </div>
          <div
            class="think-container"
            v-if="thinkMode && message.content?.length"
          >
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
          <div v-html="renderedMarkdown"></div>
          <div v-if="!inResponse" class="footer-btn">
            <a-tooltip placement="top" :title="$t('common.copy')">
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
import { PropType, ref } from "vue";
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
  think: {
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
});

const emit = defineEmits(["preview", "stop", "regenerate", "resend"]);

const benchmarkData = computed<Benchmark>(() => {
  return (props.message?.benchmark || {}) as Benchmark;
});
const isExpanded = ref<boolean>(false);
const isCollapsed = ref(true);
const thinkMode = ref(props.think);
const editState = ref<boolean>(false);
const queryInput = ref<string>(props.message.content);

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});
const thinkTagRegexSpecial = /^[\s\S]*?<\/think>/;

const isThinkEnd = computed(() => props.message.content.includes("</think>"));
const getThinkMode = () => {
  const { content } = props.message;
  const endIndex = content.indexOf("</think>");

  return computed(() => {
    if (isThinkEnd.value) {
      return content.substring(0, endIndex);
    } else if (thinkMode.value) {
      return content;
    } else {
      return "";
    }
  });
};

const thinkMarkdown = computed(() => {
  return marked(getThinkMode().value);
});

const readResponse = computed(() => {
  const content = props.message?.content || "";

  if (!content) return "";

  if (!thinkMode.value) {
    return content;
  }

  if (!isThinkEnd.value) {
    return "";
  }

  const cleanedContent = content.replace(thinkTagRegexSpecial, "");
  return cleanedContent;
});
const renderedMarkdown = computed(() => {
  return marked(readResponse.value);
});
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
