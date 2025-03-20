<template>
  <div id="message-container">
    <template v-if="message.author === 'Bot'">
      <div class="chatbot-session">
        <div class="avatar-wrap">
          <SvgIcon name="icon-chatbot" :size="24" />
        </div>
        <div class="message-wrap">
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
      <div class="avatar-wrap">
        <SvgIcon name="icon-user" :size="22" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="MessageItem">
import { marked } from "marked";
import { PropType, reactive, ref } from "vue";
import { Benchmark, IMessage } from "../type";

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

const emit = defineEmits(["preview"]);
const benchmarkData = computed(() => {
  return props.message?.benchmark || {};
});
const isExpanded = ref<boolean>(false);

const renderer = new marked.Renderer();

renderer.link = ({ href, title, text }) => {
  let link = `<a href="${href}" target="_blank" rel="noopener noreferrer"`;
  if (title) {
    link += ` title="${title}"`;
  }
  link += `>${text}</a>`;
  return link;
};

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: renderer,
});

const renderedMarkdown = computed(() => marked(props.message.content));

const toggleTabs = () => {
  isExpanded.value = !isExpanded.value;
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
.chatbot-session {
  margin-bottom: 16px;
  display: flex;
  padding-right: 40px;
  gap: 8px;
  font-size: 16px;
}
.avatar-wrap {
  background-color: var(--bg-main-color);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  .vertical-center;
}
.message-wrap {
  background-color: var(--bg-main-color);
  border-radius: 6px;
  line-height: 24px;
  padding: 10px 14px;
  max-width: calc(100% - 40px);
}
.user-session {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
  padding-left: 40px;
  gap: 8px;
  font-size: 16px;
  .message-wrap {
    background-color: var(--color-primaryBg);
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
/* 定义 <transition> 的进入和离开动画 */
.detail-transition-enter-active,
.detail-transition-leave-active {
  transition: all 0.7s ease-in-out;
}
</style>
