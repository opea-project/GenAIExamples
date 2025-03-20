<template>
  <div class="chatbot-wrap">
    <div class="message-box" ref="scrollContainer">
      <div ref="messageComponent" class="intel-markdown">
        <div v-for="(msg, index) in messagesList" :key="index" :inResponse>
          <MessageItem
            :message="msg"
            ref="messageRef"
            :inResponse
            @preview="hadleImagePreview"
          />
        </div>
      </div>
    </div>
    <div class="input-wrap">
      <div class="chatbot-tip">
        <img :src="lightBulb" alt="" />
        <span class="info-wrap">
          Uploading relevant documents can help AI answer questions more
          accurately
        </span>
      </div>
      <a-input
        size="large"
        v-model:value="inputKeywords"
        @pressEnter="handleSendMessage"
        placeholder="Please enter your question..."
      />
      <div class="button-wrap">
        <a-button
          type="primary"
          size="large"
          :disabled="inResponse"
          @click="handleSendMessage"
        >
          <SvgIcon
            name="icon-send"
            :size="22"
            :style="{ color: 'var(--color-white)' }"
          />
        </a-button>
        <a-config-provider :theme="antTheme.subTheme">
          <a-button
            v-if="false"
            type="primary"
            size="large"
            @click="handleStopDisplay"
          >
            <SvgIcon
              name="icon-stop"
              :style="{ color: 'var(--color-white)' }"
            />
          </a-button>
          <a-button
            type="primary"
            size="large"
            :icon="h(DeleteFilled)"
            @click="handleClearMessage"
          >
          </a-button>
        </a-config-provider>
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
import { antTheme } from "@/utils/antTheme";
import { DeleteFilled } from "@ant-design/icons-vue";
import _ from "lodash";
import { h, onMounted, reactive, ref, onBeforeUnmount } from "vue";
import { Benchmark, ConfigType, IMessage } from "../type";
import MessageItem from "./MessageItem.vue";
import { handleMessageSend } from "./SseService";
import { pipelineAppStore } from "@/store/pipeline";

const props = defineProps({
  configuration: {
    type: Object as PropType<ConfigType>,
    required: true,
    default: () => {},
  },
});

const ENV_URL = import.meta.env;
const pipelineStore = pipelineAppStore();
const defaultBenchmark = reactive<Benchmark>({
  generator: "",
  postprocessor: "",
  retriever: "",
});

const messagesList = ref<IMessage[]>([
  {
    author: "Bot",
    content: "Hello! I am an Edge AI assistant. May I help you?",
  },
]);
const inputKeywords = ref<string>("");
const scrollContainer = ref<HTMLElement | null>(null);
const messageComponent = ref<HTMLElement | null>(null);
let resizeObserver: ResizeObserver | null = null;
const messageRef = ref<any>(null);
const inResponse = ref<boolean>(false);
const imgVisible = ref<boolean>(false);
const imageSrc = ref<string>("");

const handleEnvUrl = () => {
  const { VITE_CHATBOT_URL } = ENV_URL;

  return `${VITE_CHATBOT_URL}v1/chatqna`;
};

const handleMessageDisplay = (data: any) => {
  if (inResponse.value)
    messagesList.value[messagesList.value?.length - 1].content = data;
};
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
  const { configuration } = props;

  return Object.assign({}, configuration, {
    messages: inputKeywords.value,
  });
};
const handleSendMessage = async () => {
  if (!inputKeywords.value.trim()) return;
  messagesList.value.push(
    {
      author: "User",
      content: inputKeywords.value,
    },
    {
      author: "Bot",
      content: "",
      benchmark: _.cloneDeep(defaultBenchmark),
    }
  );
  inResponse.value = true;
  toggleConnection();
  inputKeywords.value = "";
};
const handleStopDisplay = () => {
  inResponse.value = false;
};

const handleClearMessage = () => {
  messagesList.value.splice(1);
};

const handleResize = (entries: ResizeObserverEntry[]) => {
  for (let entry of entries) {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = entry.contentRect.height;
    }
  }
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
const hadleImagePreview = (url: string) => {
  imageSrc.value = url;
  handleImageVisible(true);
};
const handleImageVisible = (value: boolean = false) => {
  imgVisible.value = value;
};
onMounted(() => {
  if (messageComponent.value) {
    resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(messageComponent.value);
  }
});

onBeforeUnmount(() => {
  if (resizeObserver && messageComponent.value) {
    resizeObserver.unobserve(messageComponent.value);
    resizeObserver = null;
  }
});
</script>
<style scoped lang="less">
.chatbot-wrap {
  border-radius: 6px;
  background-color: var(--bg-content-color);
  overflow: hidden;
  padding-top: 4px;
  .message-box {
    height: 400px;
    width: 100%;
    overflow-y: auto;
    padding: 20px 24px 0 24px;
  }
  .input-wrap {
    display: flex;
    align-items: center;
    padding: 32px 24px 24px 24px;
    gap: 16px;
    position: relative;
    .chatbot-tip {
      .vertical-center;
      position: absolute;
      width: calc(100% - 48px);
      top: 6px;
      gap: 4px;
      .info-wrap {
        background-color: var(--bg-main-color);
        color: var(--font-text-color);
        line-height: 20px;
        border-radius: 10px;
        padding: 0 12px;
      }
    }
    .button-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
      .intel-btn,
      .ant-btn {
        width: 65px;
        .icon-intel {
          position: relative;
          top: 1px;
        }
      }
      .intel-btn-primary:disabled {
        background-color: var(--color-info);
        .icon-intel {
          color: var(--color-primaryBg) !important;
        }
      }
    }
  }
}
</style>
