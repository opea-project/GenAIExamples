<template>
  <div class="chatbot-container">
    <!-- chatbot-->
    <Chat @config="handleConfig" />
    <!-- config chatbot -->
    <ConfigDrawer
      v-if="configDrawer.visible"
      :drawer-data="configDrawer.data"
      @close="configDrawer.visible = false"
      @update="handleUpdateConfiguration"
    />
  </div>
</template>

<script lang="ts" setup name="Chat">
import { chatbotAppStore } from "@/store/chatbot";
import { onMounted, reactive } from "vue";
import { Chat, ConfigDrawer } from "./index";
import { ConfigType } from "../../type";
import { Local } from "@/utils/storage";

const chatbotStore = chatbotAppStore();

let chatbotConfiguration = reactive<ConfigType>({
  top_n: 0,
  k: 0,
  temperature: 0.01,
  top_p: 0.95,
  top_k: 10,
  repetition_penalty: 1.03,
  max_tokens: 1024,
  stream: true,
});
const configDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});

const handleConfig = () => {
  const { configuration = {} } = Local.get("chatbotConfiguration") || {};
  configDrawer.visible = true;
  configDrawer.data = configuration || chatbotConfiguration;
};
const handleUpdateConfiguration = (configuration: ConfigType) => {
  chatbotConfiguration = {
    ...chatbotConfiguration,
    ...configuration,
  };
  chatbotStore.setChatbotConfiguration(configuration);
};
onMounted(() => {
  if (Local.get("chatbotConfiguration")) {
    const { configuration } = Local.get("chatbotConfiguration");
    Object.assign(chatbotConfiguration, configuration);
  } else {
    chatbotStore.setChatbotConfiguration(chatbotConfiguration);
  }
});
</script>

<style scoped lang="less">
.chatbot-container {
  position: relative;
  height: calc(100% - 20px);

  .setting-icon {
    padding: 12px 8px;
    position: absolute;
    transform: translateY(-50%);
    top: 40%;
    left: -80px;
    z-index: 99;
    background-color: var(--bg-content-color);
    box-shadow: 0px 2px 4px 0px var(--bg-box-shadow);
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    color: var(--font-main-color);
    &:hover {
      color: var(--color-primary);
    }
  }
  @media (max-width: 1100px) {
    .setting-icon {
      left: 0;
    }
  }
}
</style>
