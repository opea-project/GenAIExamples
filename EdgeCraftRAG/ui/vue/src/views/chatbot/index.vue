<template>
  <div class="pipeline-container">
    <a-affix :offset-top="450">
      <div class="setting-icon" @click="jumpPipeline">
        <SvgIcon
          name="icon-setting"
          :size="32"
          :style="{ color: 'var(--color-big-icon)' }"
          inherit
        />
        <div>Pipeline</div>
      </div></a-affix
    >
    <!-- system status -->
    <Header @config="handleConfig" />
    <!-- chatbot-->
    <Chatbot :configuration="chatbotConfiguration" />
    <!-- upload file-->
    <UploadFile />
    <!-- config chatbot -->
    <ConfigDrawer
      v-if="configDrawer.visible"
      :drawer-data="configDrawer.data"
      @close="configDrawer.visible = false"
      @update="handleUpdateConfiguration"
    />
  </div>
</template>

<script lang="ts" setup name="Chatbot">
import router from "@/router";
import { chatbotAppStore } from "@/store/chatbot";
import { onMounted, reactive } from "vue";
import { Chatbot, ConfigDrawer, Header, UploadFile } from "./components";
import { ConfigType } from "./type";

const chatbotStore = chatbotAppStore();

let chatbotConfiguration = reactive<ConfigType>({
  top_n: 5,
  temperature: 0.1,
  top_p: 1,
  top_k: 50,
  repetition_penalty: 1.1,
  max_tokens: 512,
  stream: true,
});
const configDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});

const handleConfig = () => {
  configDrawer.visible = true;
  configDrawer.data = chatbotConfiguration;
};
//Jump Pipeline
const jumpPipeline = () => {
  router.push("/pipeline");
};
const handleUpdateConfiguration = (configuration: ConfigType) => {
  chatbotConfiguration = {
    ...chatbotConfiguration,
    ...configuration,
  };
  chatbotStore.setChatbotConfiguration(configuration);
};
onMounted(() => {
  if (chatbotStore?.configuration)
    chatbotConfiguration = {
      ...chatbotConfiguration,
      ...chatbotStore.configuration,
    };
});
</script>

<style scoped lang="less">
.pipeline-container {
  position: relative;

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
