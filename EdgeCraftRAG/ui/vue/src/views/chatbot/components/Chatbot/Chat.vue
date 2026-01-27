<template>
  <div class="chatbot-wrap">
    <div class="message-box" ref="scrollContainer" v-if="messagesLength">
      <div class="intel-markdown">
        <div ref="messageComponent">
          <div
            v-for="(msg, index) in messagesList"
            :key="`session-${currentSessionId}-${index}`"
          >
            <MessageItem
              :message-key="`session-${currentSessionId}-${index}`"
              :message="msg"
              ref="messageRef"
              :inResponse
              :message-Index="index"
              :last-query="isLastQuery(index)"
              :last-response="isLastResponse(index)"
              @preview="handleImagePreview"
              @stop="isUserScrolling = true"
              @regenerate="handleRegenerate"
              @resend="handleDelete"
            />
          </div>
        </div>
      </div>
    </div>
    <div class="initial-input" v-else>
      <div class="text-wrap">{{ $t("chat.tip2") }}</div>
      <div class="tip-wrap">
        <img :src="lightBulb" alt="" />{{ $t("chat.tip3") }}
      </div>
    </div>
    <div class="input-wrap" ref="inputRef">
      <div class="bottom-wrap" v-if="showScrollToBottomBtn">
        <div class="to-bottom" @click="scrollToBottom">
          <ArrowDownOutlined />
        </div>
      </div>
      <a-textarea
        v-model:value.trim="inputKeywords"
        @keydown.enter="handleEnter"
        :placeholder="$t('chat.tip4')"
        :bordered="false"
        :auto-size="{ minRows: 2, maxRows: 5 }"
      />
      <div class="button-wrap">
        <div class="flex-left">
          <span
            :class="{
              'think-btn': true,
              'is-deep': isThink,
              'is-disabled': isAgent,
            }"
            @click="handleThinkChange"
          >
            <SvgIcon name="icon-deep-think" :size="16" inherit />
            {{ $t(`chat.${isThink ? "reason" : "think"}`) }}
          </span>
          <span
            :class="{ 'think-btn': true, 'is-deep': enableKB }"
            @click="handleKBChange"
          >
            <SvgIcon name="icon-kb" :size="16" inherit />
            {{ $t("knowledge.title") }}
          </span>
        </div>

        <div class="send-btn">
          <a-tooltip placement="top" :title="$t('chat.new')">
            <span class="common-btn">
              <SvgIcon
                name="icon-newChat"
                :size="36"
                :style="{ color: 'var(--face-icon-bg)' }"
                @click="handleNewChat"
              />
            </span>
          </a-tooltip>
          <a-tooltip placement="top" :title="$t('generation.title')">
            <span class="common-btn">
              <SvgIcon
                name="icon-setting1"
                :size="36"
                :style="{ color: 'var(--face-icon-bg)' }"
                @click="handleConfig"
              />
            </span>
          </a-tooltip>
          <a-divider type="vertical" />
          <a-button
            v-if="!inResponse"
            type="primary"
            :disabled="inResponse || notInput"
            @click="handleSendMessage"
          >
            <SvgIcon name="icon-send" inherit />
          </a-button>
          <a-button v-else type="primary" @click="handleStopChat">
            <SvgIcon name="icon-stop" inherit />
          </a-button>
        </div>
      </div>
    </div>
  </div>
  <a-image
    :style="{ display: 'none' }"
    :preview="{
      visible: imgVisible,
      onVisibleChange: handleImageVisible,
    }"
    :src="imageSrc"
  />
</template>

<script lang="ts" setup name="Chatbot">
import { getBenchmark, getSessionDetailById } from "@/api/chatbot";
import lightBulb from "@/assets/svgs/lightBulb.svg";
import _ from "lodash";
import { reactive, ref, computed, nextTick } from "vue";
import { Benchmark, IMessage } from "../../type";
import MessageItem from "./MessageItem.vue";
import { handleMessageSend, StreamController } from "./SseService";
import { Local } from "@/utils/storage";
import { ArrowDownOutlined } from "@ant-design/icons-vue";
import { throttle } from "lodash";
import { chatbotAppStore } from "@/store/chatbot";
import { sessionAppStore } from "@/store/session";
import emitter from "@/utils/mitt";
import router from "@/router";
import { message } from "ant-design-vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const route = useRoute();
const chatbotStore = chatbotAppStore();
const sessionStore = sessionAppStore();
const emit = defineEmits(["config"]);
const ENV_URL = import.meta.env;

const defaultBenchmark = reactive<Benchmark>({
  generator: "",
  postprocessor: "",
  retriever: "",
});

let streamController = ref<StreamController | null>(null);
const messagesList = ref<IMessage[]>([]);
const inputKeywords = ref<string>("");
const scrollContainer = ref<HTMLElement | null>(null);
const messageComponent = ref<HTMLElement | null>(null);
let resizeObserver: ResizeObserver | null = null;
const messageRef = ref<any>(null);
const inResponse = ref<boolean>(false);
const imgVisible = ref<boolean>(false);
const imageSrc = ref<string>("");
const isUserScrolling = ref(false);
const showScrollToBottomBtn = ref(false);
const resizeObserverRef = ref<ResizeObserver | null>(null);
const enableKB = ref<boolean>(true);
const isCreatingNewSession = ref(false);
const shouldIgnoreRouteChange = ref(false);

const inputRef = ref();
const handleEnvUrl = () => {
  const { VITE_CHATBOT_URL } = ENV_URL;
  return `${VITE_CHATBOT_URL}v1/chatqna`;
};

const handleMessageDisplay = (data: any) => {
  if (inResponse.value) {
    isUserScrolling.value = false;
    const regex = /code:0000(.*)/s;
    const match = data.match(regex);
    if (match) {
      messagesList.value.pop();
      messagesList.value[messagesList.value?.length - 1].errorMessage =
        match[1].trim();
      return;
    }

    messagesList.value[messagesList.value?.length - 1].content = data;
  }
};

const notInput = computed(() => {
  return inputKeywords.value.trim() === "";
});

const messagesLength = computed(() => {
  return messagesList.value?.length;
});

const lastQueryIndex = computed(() => {
  for (let i = messagesList.value.length - 1; i >= 0; i--) {
    if (messagesList.value[i].role === "user") {
      return i;
    }
  }
  return -1;
});

const lastResponseIndex = computed(() => {
  for (let i = messagesList.value.length - 1; i >= 0; i--) {
    if (messagesList.value[i].role === "assistant") {
      return i;
    }
  }
  return -1;
});

const isAgent = computed(() => {
  return !!chatbotStore.agent.name;
});

const isThink = computed({
  get() {
    const { enable_thinking = true } =
      chatbotStore.configuration?.chat_template_kwargs;
    return enable_thinking;
  },
  set(value: boolean) {
    chatbotStore.setChatbotConfiguration({
      chat_template_kwargs: {
        ...chatbotStore.configuration?.chat_template_kwargs,
        enable_thinking: value,
      },
    });
  },
});

const isLastQuery = (index: number) => index === lastQueryIndex.value;
const isLastResponse = (index: number) => index === lastResponseIndex.value;

const handleStreamEnd = () => {
  handleStopDisplay();
  queryBenchmark();
  updateSessionId();
  sessionStore.setResponseSessionId("");
};

const toggleConnection = () => {
  if (inResponse.value) {
    if (streamController.value) {
      streamController.value.cancel();
    }

    streamController.value = handleMessageSend(
      handleEnvUrl(),
      formatFormParam(),
      handleMessageDisplay,
      handleStreamEnd
    );
  }
};

// Format parameter
const formatFormParam = () => {
  const { configuration = {} } = Local.get("chatbotConfiguration") || {};
  return Object.assign({}, configuration, {
    messages: inputKeywords.value,
  });
};

const handleEnter = (e: any) => {
  e.preventDefault();
  if (inResponse.value) {
    return;
  }
  handleSendMessage();
};

const handleSendMessage = async () => {
  if (!inputKeywords.value.trim()) return;

  messagesList.value.push(
    {
      role: "user",
      content: inputKeywords.value,
    },
    {
      role: "assistant",
      content: "",
      query: inputKeywords.value,
      benchmark: _.cloneDeep(defaultBenchmark),
    }
  );

  inResponse.value = true;
  toggleConnection();
  inputKeywords.value = "";
  scrollToBottom();

  const { currentSession = "" } = sessionStore;
  sessionStore.setResponseSessionId(currentSession);
};

const handleStopDisplay = () => {
  inResponse.value = false;
};
const currentSessionId = computed(() => sessionStore.currentSession);
const updateSessionId = () => {
  const sessionId = route.query?.sessionId;
  const storedSessionId = sessionStore.currentSession;

  if (!sessionId && storedSessionId) {
    shouldIgnoreRouteChange.value = true;
    router.replace({
      query: {
        ...route.query,
        sessionId: storedSessionId,
      },
    });
    nextTick(() => {
      setTimeout(() => {
        shouldIgnoreRouteChange.value = false;
      }, 100);
    });
  }
};

const queryBenchmark = async () => {
  const data = (await getBenchmark()) || {};

  if (data["Benchmark enabled"]) {
    const benchmarkData = data.last_benchmark_data || {};
    if (benchmarkData.generator) {
      const processedBenchmarkData = Object.fromEntries(
        Object.entries(benchmarkData).map(([key, value]: any) => [
          key,
          value ? parseFloat(value.toFixed(4)) : 0,
        ])
      );
      messagesList.value[messagesList.value.length - 1].benchmark =
        processedBenchmarkData;
    }
  }
};

const handleImagePreview = (url: string) => {
  imageSrc.value = url;
  handleImageVisible(true);
};

const handleImageVisible = (value: boolean = false) => {
  imgVisible.value = value;
};

const handleNewChat = () => {
  isCreatingNewSession.value = true;
  shouldIgnoreRouteChange.value = true;

  inputKeywords.value = "";
  messagesList.value = [];
  sessionStore.setSessionId("");
  router.replace({
    query: {},
  });
  nextTick(() => {
    setTimeout(() => {
      isCreatingNewSession.value = false;
      shouldIgnoreRouteChange.value = false;
    }, 100);
  });
};

const handleThinkChange = () => {
  if (isAgent.value) return;
  isThink.value = !isThink.value;
};

const handleKBChange = () => {
  enableKB.value = !enableKB.value;
  const { chat_template_kwargs } = chatbotStore.configuration;

  const chat_template = {
    ...chat_template_kwargs,
    enable_rag_retrieval: enableKB.value,
  };

  chatbotStore.setChatbotConfiguration({
    chat_template_kwargs: chat_template,
  });
};

const handleConfig = () => {
  emit("config");
};

const handleRegenerate = (query: string) => {
  inputKeywords.value = query;
  handleSendMessage();
};

const handleDelete = ({ index, query }: { index: number; query: string }) => {
  messagesList.value.splice(index);
  inputKeywords.value = query;
  handleSendMessage();
};

const handleStopChat = async () => {
  if (streamController.value) {
    streamController.value.cancel();
    streamController.value = null;
  }
};

const scrollToBottom = () => {
  if (!scrollContainer.value) return;

  scrollContainer.value?.scrollTo({
    top: scrollContainer.value.scrollHeight,
    behavior: "smooth",
  });
  isUserScrolling.value = false;
  showScrollToBottomBtn.value = false;
};

const handleResize = (entries: ResizeObserverEntry[]) => {
  for (const entry of entries) {
    if (!scrollContainer.value || isUserScrolling.value) return;

    scrollContainer.value?.scrollTo({
      top: entry.contentRect.height,
      behavior: "smooth",
    });
  }
};

const handleScroll = () => {
  const container = scrollContainer.value;
  if (!container) return;
  const distanceToBottom =
    container.scrollHeight - container.scrollTop - container.clientHeight;
  if (distanceToBottom > 80) {
    isUserScrolling.value = true;
    showScrollToBottomBtn.value = true;
    if (resizeObserverRef.value) resizeObserverRef.value.disconnect();
  } else {
    isUserScrolling.value = false;
    showScrollToBottomBtn.value = false;
    if (messageComponent.value && resizeObserverRef.value)
      resizeObserverRef.value.observe(messageComponent.value);
  }
};

const initResizeObserver = () => {
  if (messageComponent.value) {
    if (resizeObserverRef.value) {
      resizeObserverRef.value.disconnect();
    }

    resizeObserverRef.value = new ResizeObserver(handleResize);
    resizeObserverRef.value.observe(messageComponent.value);

    const throttledHandleScroll = throttle(handleScroll, 100);

    scrollContainer.value?.addEventListener("scroll", throttledHandleScroll);
  }
};

const initialSessionDetail = (messages: IMessage[]): IMessage[] => {
  return messages?.map((msg, i, arr) => {
    if (msg.role === "assistant" && i > 0 && arr[i - 1].role === "user") {
      return {
        ...msg,
        query: arr[i - 1].content,
      };
    }
    return msg;
  });
};

const handleViewSessionDetail = async (sessionId: string) => {
  try {
    const data: any = await getSessionDetailById(sessionId);
    if (!data?.session_content?.messages) {
      handleNewChat();
      message.error(t("chat.notExist"));
      return;
    }
    messagesList.value = initialSessionDetail(data?.session_content?.messages);
    nextTick(() => {
      scrollToBottom();
    });
  } catch (error) {
    console.error(error);
  }
};

watch(
  () => messageComponent.value,
  (value) => {
    if (value) {
      nextTick(() => {
        initResizeObserver();
      });
    }
  },
  { immediate: true }
);

watch(
  () => route.query?.sessionId,
  (sessionId) => {
    if (shouldIgnoreRouteChange.value || isCreatingNewSession.value) {
      shouldIgnoreRouteChange.value = false;
      return;
    }

    if (sessionId) {
      handleViewSessionDetail(String(sessionId));
      if (sessionId !== sessionStore.responseSession) {
        inResponse.value = false;
      } else {
        inResponse.value = true;
      }
    } else {
      messagesList.value = [];
    }
  },
  { immediate: true }
);

onMounted(() => {
  const { enable_thinking = true, enable_rag_retrieval = false } =
    chatbotStore.configuration?.chat_template_kwargs;
  isThink.value = enable_thinking;
  enableKB.value = enable_rag_retrieval;
  emitter.on("new-chat", handleNewChat);
  if (!route.query?.sessionId) {
    sessionStore.setSessionId("");
  }
});

onBeforeUnmount(() => {
  if (resizeObserver && messageComponent.value) {
    resizeObserver.unobserve(messageComponent.value);
    resizeObserver = null;
  }
  scrollContainer.value?.removeEventListener("scroll", handleScroll);
});

onUnmounted(() => {
  emitter.off("new-chat", handleNewChat);
  sessionStore.setSessionId("");
});
</script>

<style scoped lang="less">
.chatbot-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;

  .initial-input {
    text-align: center;

    .title-wrap {
      font-size: 28px;
      line-height: 36px;
      color: var(--font-main-color);
    }

    .text-wrap {
      font-size: 20px;
      color: var(--font-main-color);
    }

    .tip-wrap {
      font-size: 12px;
      color: var(--font-tip-color);
      margin-top: 24px;

      img {
        margin-right: 4px;
      }
    }
  }

  .message-box {
    flex: 1;
    width: 100%;
    overflow-y: auto;
    position: relative;
    display: flex;
    justify-content: center;

    .intel-markdown {
      max-width: 960px;
      width: 75%;
      position: relative;
      transition: all 0.2s;
      // height: 100%;
      min-height: 0;
      margin: 0 48px;
      padding: 24px 0;
    }
  }

  .input-wrap {
    padding: 8px;
    margin: 24px 0;
    border: 1px solid var(--color-primary);
    border-radius: 20px;
    background-color: var(--input-bg);
    max-width: 960px;
    min-width: 500px;
    transition: all 0.2s;
    width: 75%;
    display: flow-root;
    position: relative;
    left: -2px;
    text-align: center;

    &:hover {
      box-shadow: 0 4px 12px var(--bg-primary-shadow);
      border: 1px solid var(--color-primary-hover);
    }
    .bottom-wrap {
      position: absolute;
      top: -40px;
      width: 100%;
      height: 32px;
      .vertical-center;
      .to-bottom {
        .vertical-center;
        width: 32px;
        height: 32px;
        cursor: pointer;
        z-index: 20;
        border-radius: 50%;
        background-color: var(--bg-card-color);
        border: 1px solid var(--border-main-color);
        box-shadow: 0px 2px 4px 0px var(--bg-box-shadow);
        &:hover {
          background-color: var(--color-second-primaryBg);
          border: 1px solid var(--color-primary-second);
          .anticon-arrow-down {
            color: var(--color-primary-second);
          }
        }
      }
    }

    textarea {
      resize: none;
    }

    .button-wrap {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 12px;
      .flex-left {
        gap: 8px;
      }
      .think-btn {
        height: 24px;
        line-height: 24px;
        padding: 0 8px;
        border: 1px solid var(--border-main-color);
        color: var(--font-text-color);
        cursor: pointer;
        border-radius: 12px;
        font-size: 12px;
        .mt-12;
        .vertical-center;
        gap: 4px;
        &:hover {
          border: 1px solid var(--color-primary-second);
          color: var(--color-primary-second);
          background-color: var(--color-primaryBg);
        }
        &.is-deep {
          border: 1px solid var(--color-primary-second);
          color: var(--color-primary-second);
          background-color: var(--color-primaryBg);
        }
        &.is-disabled,
        .is-disabled:hover {
          border: 1px solid var(--border-main-color);
          color: var(--font-text-color);
          background-color: var(--bg-main-color);
          cursor: no-drop;
        }
      }
      .send-btn {
        display: flex;

        .common-btn {
          width: 36px;
          height: 36px;
          margin-left: 8px;
          cursor: pointer;
          .vertical-center;

          &:hover .icon-intel {
            color: var(--color-primary) !important;
          }
        }

        .icon-send {
          &:hover {
            color: var(--color-white);
          }
        }

        .intel-divider-vertical {
          height: 28px;
          margin: 0 12px 0 8px;
          top: 4px;
        }

        .intel-btn,
        .ant-btn {
          width: 36px;
          height: 36px;
          padding: 0;
          .vertical-center;

          .icon-intel {
            position: relative;
            top: 1px;
            font-size: 16px;
          }
        }
      }

      .intel-btn-primary:disabled {
        background-color: var(--color-info);

        .icon-intel {
          color: var(--color-white) !important;
        }
      }
    }
  }
  .error-tip {
    border: 1px solid var(--border-warning);
    background-color: var(--color-warningBg);
    color: var(--color-second-warning);
    padding: 8px 12px;
    border-radius: 0 4px 4px 0;
    margin-bottom: 12px;
    font-size: 12px;
    .flex-between;
    &:hover {
      .card-shadow;
    }
    .message-wrap {
      flex: 1;
    }
    .close-btn {
      cursor: pointer;
      text-align: end;
      &:hover {
        color: var(--color-error);
      }
    }
  }
}
</style>
