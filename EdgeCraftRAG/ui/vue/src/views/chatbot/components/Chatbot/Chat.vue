<template>
  <div class="chatbot-wrap">
    <div class="message-box" ref="scrollContainer" v-if="messagesLength">
      <div class="intel-markdown">
        <div ref="messageComponent">
          <div v-for="(msg, index) in messagesList" :key="index" :inResponse>
            <MessageItem
              :message="msg"
              ref="messageRef"
              :inResponse
              :think="isThink"
              @preview="handleImagePreview"
              @stop="isUserScrolling = true"
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
        <span
          :class="{ 'think-btn': true, 'is-deep': isThink }"
          @click="handleThinkChange"
        >
          <SvgIcon name="icon-deep-think" :size="16" inherit />
          {{ $t(`chat.${isThink ? "reason" : "think"}`) }}
        </span>
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
            type="primary"
            :disabled="inResponse || notInput"
            @click="handleSendMessage"
          >
            <SvgIcon name="icon-send" inherit />
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
import { getBenchmark } from "@/api/chatbot";
import lightBulb from "@/assets/svgs/lightBulb.svg";
import _ from "lodash";
import { reactive, ref, computed, nextTick } from "vue";
import { Benchmark, IMessage } from "../../type";
import MessageItem from "./MessageItem.vue";
import { handleMessageSend } from "./SseService";
import { pipelineAppStore } from "@/store/pipeline";
import { Local } from "@/utils/storage";
import { ArrowDownOutlined } from "@ant-design/icons-vue";
import { throttle } from "lodash";
import { chatbotAppStore } from "@/store/chatbot";

const chatbotStore = chatbotAppStore();
const emit = defineEmits(["config"]);
const ENV_URL = import.meta.env;
const pipelineStore = pipelineAppStore();
const defaultBenchmark = reactive<Benchmark>({
  generator: "",
  postprocessor: "",
  retriever: "",
});

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
const isThink = ref<boolean>(true);

const inputRef = ref();
const handleEnvUrl = () => {
  const { VITE_CHATBOT_URL } = ENV_URL;

  return `${VITE_CHATBOT_URL}v1/chatqna`;
};

const handleMessageDisplay = (data: any) => {
  if (inResponse.value) {
    isUserScrolling.value = false;
    messagesList.value[messagesList.value?.length - 1].content = data;
  }
};
const notInput = computed(() => {
  return inputKeywords.value.trim() === "";
});
const messagesLength = computed(() => {
  return messagesList.value?.length;
});
const handleStreamEnd = () => {
  handleStopDisplay();
  queryBenchmark();
};
const toggleConnection = () => {
  if (inResponse.value) {
    handleMessageSend(
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
      benchmark: _.cloneDeep(defaultBenchmark),
    }
  );
  inResponse.value = true;
  toggleConnection();
  inputKeywords.value = "";
  scrollToBottom();
};
const handleStopDisplay = () => {
  inResponse.value = false;
};

const queryBenchmark = async () => {
  const { activatedPipeline } = pipelineStore;
  const data = (await getBenchmark(activatedPipeline)) || {};

  if (data["Benchmark enabled"]) {
    const benchmarkData = data.last_benchmark_data || {};
    if (benchmarkData.generator) {
      const processedBenchmarkData = Object.fromEntries(
        Object.entries(benchmarkData).map(([key, value]: any) => [
          key,
          parseFloat(value.toFixed(4)),
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
  inputKeywords.value = "";
  messagesList.value = [];
  Local.remove("chat_session_id");
};
const handleThinkChange = () => {
  isThink.value = !isThink.value;

  chatbotStore.setChatbotConfiguration({
    chat_template_kwargs: { enable_thinking: isThink.value },
  });
};
const handleConfig = () => {
  emit("config");
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
onMounted(() => {
  isThink.value =
    chatbotStore.configuration?.chat_template_kwargs.enable_thinking;
});
onBeforeUnmount(() => {
  if (resizeObserver && messageComponent.value) {
    resizeObserver.unobserve(messageComponent.value);
    resizeObserver = null;
  }
  scrollContainer.value?.removeEventListener("scroll", handleScroll);
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
}
</style>
