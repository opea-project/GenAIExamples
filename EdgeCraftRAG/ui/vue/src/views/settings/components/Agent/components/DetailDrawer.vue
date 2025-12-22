<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="$t('agent.detail')"
    destroyOnClose
    width="500px"
    @close="handleClose"
  >
    <!-- basic -->
    <div class="basic-wrap">
      <p class="basic-item">
        <span class="label-wrap">{{ $t("agent.name") }}</span>
        <span class="content-wrap">{{ formData.name }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("agent.label.type") }}</span>
        <span class="content-wrap">{{ getEnumField(AgentType, formData.type) }}</span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("agent.pipeline") }}</span>
        <span class="content-wrap"
          >{{ formData.pipeline_idx }}
          <a-tooltip :title="$t('common.detail')"
            ><EyeOutlined class="click-link" @click="handlePipelineView"
          /></a-tooltip>
        </span>
      </p>
      <p class="basic-item">
        <span class="label-wrap">{{ $t("agent.status") }}</span>
        <span :class="{ 'active-state': formData.active, 'content-wrap': true }">{{
          formData.active ? $t("pipeline.activated") : $t("pipeline.inactive")
        }}</span>
      </p>
    </div>
    <!-- Configs -->
    <div class="module-wrap">
      <a-collapse v-model:activeKey="agentActive" expandIconPosition="end">
        <a-collapse-panel key="config" :header="$t('agent.label.configs')">
          <ul class="form-wrap">
            <li class="item-wrap" v-for="(value, key) in formData.configs">
              <span class="label-wrap">{{ key }}</span>
              <span class="content-wrap">{{ value }}</span>
            </li>
          </ul>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </a-drawer>
</template>
<script lang="ts" setup name="DetailDrawer">
  import { getEnumField } from "@/utils/common";
  import { EyeOutlined } from "@ant-design/icons-vue";
  import { reactive, ref } from "vue";
  import { AgentType } from "../enum";

  const props = defineProps({
    drawerData: {
      type: Object,
      required: true,
      default: () => {},
    },
  });
  const emit = defineEmits(["close", "viewPipeline"]);
  const formData = reactive<EmptyObjectType>(props.drawerData);
  const drawerVisible = ref<boolean>(true);
  const agentActive = ref<string>("config");

  const handlePipelineView = () => {
    emit("viewPipeline", formData);
  };
  const handleClose = () => {
    emit("close");
  };
</script>
<style scoped lang="less">
  .basic-wrap {
    .basic-item {
      display: flex;
      gap: 12px;
      margin: 0;
      line-height: 32px;
      .content-wrap {
        color: var(--font-main-color);
        font-weight: 600;
      }
      .click-link {
        color: var(--color-primary);
        cursor: pointer;
        transition: color 0.3s;
        &:hover {
          color: var(--color-primary-hover);
          text-decoration: underline;
        }
      }
      .active-state {
        color: var(--color-success);
      }
    }
  }
  .module-wrap {
    margin-top: 10px;
    .intel-collapse {
      border-color: var(--border-main-color);
      :deep(.intel-collapse-header) {
        padding: 8px 16px;
      }
      :deep(.intel-collapse-header-text) {
        .fs-14;
        font-weight: 600;
        color: var(--font-main-color);
      }

      :deep(.intel-collapse-item) {
        border-bottom: 1px solid var(--border-main-color);
      }

      :deep(.intel-collapse-content) {
        border-top: 1px solid var(--border-main-color);
        .intel-collapse-content-box {
          padding: 10px 16px;
        }
      }
    }
    .form-wrap {
      padding: 0;
      margin: 0;
      .item-wrap {
        list-style: none;
        display: flex;
        gap: 12px;
        line-height: 1.2;
        padding: 6px 0;
        display: flex;
        color: var(--font-text-color);
        word-wrap: break-word;
        .content-wrap {
          color: var(--font-main-color);
          font-weight: 500;
          display: inline-flex;
          align-items: baseline;
          justify-content: end;
          flex: 1;
          word-break: break-word;
          overflow-wrap: break-word;
        }
      }
      &.bt-border {
        border-top: 1px dashed var(--border-main-color);
      }
    }
  }
  .label-wrap {
    position: relative;
    &::after {
      content: ":";
      .ml-2;
    }
  }
</style>
