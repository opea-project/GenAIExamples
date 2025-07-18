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
          <div v-if="!props.message?.content" class="dot-loader">
            <span class="drop"></span>
            <span class="drop"></span>
            <span class="drop"></span>
          </div>

          <div class="think-container" v-if="isThinkMode || isThinkEnd">
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
                    isThinkEnd ? $t("chat.thinkStart") : $t("chat.thinkEnd")
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
      <div class="message-wrap">{{ message.content }}</div>
      <div class="user-wrap">
        <SvgIcon name="icon-user" inherit :size="22" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="MessageItem">
import { marked } from "marked";
import { PropType, ref } from "vue";
import { CheckCircleFilled, UpOutlined } from "@ant-design/icons-vue";
import { IMessage, Benchmark } from "../../type";
import CustomRenderer from "@/utils/customRenderer";
import "highlight.js/styles/atom-one-dark.css";

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
});

const emit = defineEmits(["preview", "stop"]);

const benchmarkData = computed<Benchmark>(() => {
  return (props.message?.benchmark || {}) as Benchmark;
});
const isExpanded = ref<boolean>(false);
const isCollapsed = ref(true);

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});
const thinkTagRegexSpecial = /^[\s\S]*?<\/think>/;
const thinkTagRegex = /<think>([\s\S]*?)<\/think>/;

const isThinkMode = computed(() => props.message.content.includes("<think>"));
const isThinkEnd = computed(() => props.message.content.includes("</think>"));
const getThinkMode = () => {
  const { content } = props.message;
  const endIndex = content.indexOf("</think>");
  return computed(() => {
    return isThinkMode.value
      ? content
      : isThinkEnd.value
      ? content.substring(0, endIndex)
      : "";
  });
};

const thinkMarkdown = computed(() => {
  return marked(getThinkMode().value);
});

const renderedMarkdown = computed(() => {
  const content = props.message?.content || "";
  if (!content) return "";
  if (isThinkMode.value && !isThinkEnd.value) {
    return "";
  }
  if (isThinkEnd.value) {
    const cleanedContent = isThinkMode.value
      ? content.replace(thinkTagRegex, "")
      : content.replace(thinkTagRegexSpecial, "");
    return marked(cleanedContent);
  }

  return marked(content);
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
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
  font-size: 16px;
  text-align: end;
  position: relative;
  .message-wrap {
    background-color: var(--message-bg);
    width: auto;
  }
}
.benchmark-wrap {
  .flex-left;
  margin-bottom: 20px;
  padding-left: 40px;
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
</style>
