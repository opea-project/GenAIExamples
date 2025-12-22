<template>
  <div class="setting-container">
    <!-- system status -->
    <System />
    <a-tabs v-model:activeKey="activeKey" type="card">
      <a-tab-pane key="pipeline" :tab="$t('pipeline.pipelines')">
        <!-- Pipeline -->
        <Pipeline />
      </a-tab-pane>
      <a-tab-pane key="agent" :tab="$t('agent.agent')">
        <!-- Agent -->
        <Agent />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>
<script lang="ts" setup name="Settings">
  import { Agent, Pipeline, System } from "./components";

  const activeKey = ref<string>("pipeline");
</script>

<style scoped lang="less">
  .setting-container {
    position: relative;
    display: block !important;
    padding: 24px;
    width: 100%;

    .chatbot-wrap {
      display: none;
      padding: 12px 8px;
      position: absolute;
      transform: translateY(-50%);
      top: 40%;
      left: -80px;
      z-index: 99;
      background-color: var(--bg-content-color);
      box-shadow: 0px 2px 4px 0px var(--bg-box-shadow);
      border-radius: 6px;
      // display: flex;
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
    :deep(.intel-tabs) {
      .mt-24;
      .intel-tabs-nav {
        margin: 0;
      }
      .intel-tabs-nav::before {
        border-bottom: none;
      }
      .title-wrap {
        .flex-left;
        gap: 4px;
      }
    }
    @media (max-width: 1100px) {
      .chatbot-wrap {
        left: 0;
      }
    }
  }
</style>
