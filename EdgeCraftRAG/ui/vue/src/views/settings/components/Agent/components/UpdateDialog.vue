<template>
  <a-modal
    v-model:open="modelVisible"
    width="800px"
    centered
    destroyOnClose
    :title="dialogTitle"
    :keyboard="false"
    :maskClosable="false"
    @cancel="handleCancel"
    class="experience-dialog"
  >
    <div class="enter-wrap">
      <a-form
        :model="form"
        :rules="rules"
        name="form"
        ref="formRef"
        autocomplete="off"
        class="form-wrap"
        layout="vertical"
      >
        <a-form-item :label="$t('agent.label.name')" name="name" :rules="rules.name">
          <a-input
            v-model:value="form.name"
            :disabled="isEdit"
            :placeholder="$t('agent.valid.name')"
          />
        </a-form-item>

        <a-form-item :label="$t('agent.label.type')" name="type">
          <a-select
            showSearch
            v-model:value="form.type"
            :disabled="isEdit"
            :placeholder="$t('agent.valid.type')"
            @change="handleTypeChange"
          >
            <a-select-option v-for="item in agentTypeList" :key="item.value" :value="item.value">{{
              item.name
            }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="pipeline_idx">
          <template #label>
            {{ $t("agent.label.pipeline") }}

            <span class="tip-wrap" v-if="showPipelineTip">
              <ExclamationCircleOutlined />
              {{ $t("agent.valid.notPipeline") }}
            </span>
          </template>
          <a-select
            showSearch
            v-model:value="form.pipeline_idx"
            :disabled="isEdit"
            :placeholder="$t('agent.valid.pipeline')"
            @dropdownVisibleChange="handlePipelineVisible"
          >
            <a-select-option v-for="item in pipelineList" :key="item.idx" :value="item.idx">{{
              item.name
            }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item
          :label="$t('agent.label.configs')"
          name="configs"
          class="gt-wrap"
          v-if="form.type"
        >
          <div class="configs-wrap">
            <DynamicConfigs :configs="configsTemplate" v-model="form.configs" />
          </div>
        </a-form-item>
      </a-form>
    </div>
    <template #footer>
      <a-button type="primary" ghost @click="handleCancel">{{ $t("common.cancel") }}</a-button>
      <a-button key="submit" type="primary" :loading="submitLoading" @click="handleSubmit">{{
        $t("common.submit")
      }}</a-button>
    </template>
  </a-modal>
</template>

<script lang="ts" setup name="UpdateDialog">
  import { getAgentConfigs, requestAgentCreate, requestAgentUpdate } from "@/api/agent";
  import { getPipelineList } from "@/api/pipeline";
  import { isValidPipelineName } from "@/utils/validate";
  import { ExclamationCircleOutlined } from "@ant-design/icons-vue";
  import { FormInstance } from "ant-design-vue";
  import { computed, reactive, ref } from "vue";
  import { useI18n } from "vue-i18n";
  import { AgentType } from "../enum";
  import { DynamicConfigs } from "./index";
  interface FormType {
    idx?: string;
    name: string;
    type: string | undefined;
    pipeline_idx: string | undefined;
    active: boolean;
    configs: any;
  }

  const props = defineProps({
    dialogData: {
      type: Object,
      default: () => ({}),
    },
    dialogType: {
      type: String,
      default: "create",
    },
  });

  const { t } = useI18n();
  const emit = defineEmits(["close", "search"]);

  const typeMap = {
    create: t("agent.create"),
    edit: t("agent.edit"),
  } as const;
  const validateName = async (rule: any, value: string) => {
    if (!value) {
      return Promise.reject(t("pipeline.valid.nameValid1"));
    }
    const len = value.length;
    if (len < 2 || len > 30) {
      return Promise.reject(t("pipeline.valid.nameValid2"));
    }
    if (!isValidPipelineName(value)) {
      return Promise.reject(t("pipeline.valid.nameValid3"));
    }
    return Promise.resolve();
  };
  const dialogTitle = computed(() => {
    return typeMap[props.dialogType as keyof typeof typeMap];
  });
  const isEdit = computed(() => props.dialogType === "edit");
  const agentTypeList = computed(() => AgentType);

  const {
    name = "",
    type = undefined,
    pipeline_idx = undefined,
    active = false,
    configs = {},
  } = props.dialogData || {};

  // visible & loading
  const modelVisible = ref<boolean>(true);
  const submitLoading = ref<boolean>(false);
  const formRef = ref<FormInstance>();
  const pipelineList = ref<EmptyArrayType>([]);
  const showPipelineTip = ref<boolean>(false);
  const configsTemplate = ref<EmptyObjectType>(configs);
  const form = reactive<FormType>({
    name,
    type,
    pipeline_idx,
    active,
    configs,
  });

  const rules: FormRules = reactive({
    name: [
      {
        required: true,
        validator: validateName,
        trigger: ["blur", "change"],
      },
    ],
    type: [
      {
        required: true,
        message: t("agent.valid.type"),
        trigger: "change",
      },
    ],
    pipeline_idx: [
      {
        required: true,
        message: t("agent.valid.pipeline"),
        trigger: "change",
      },
    ],
    key: [
      {
        required: true,
        message: t("agent.valid.key"),
        trigger: "change",
      },
    ],
    value: [
      {
        required: true,
        message: t("agent.valid.value"),
        trigger: "change",
      },
    ],
    active: [
      {
        required: true,
        trigger: "change",
      },
    ],
  });

  /* ---- pipeline utils ---- */
  const handlePipelineVisible = (visible: boolean) => {
    if (visible) {
      try {
        queryPipelineList();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const queryPipelineList = async () => {
    const data: any = await getPipelineList();
    pipelineList.value = data.filter((item: any) => item.generator.generator_type === "freechat");
    showPipelineTip.value = !(pipelineList.value.length > 0);

    console.log(pipelineList.value);
  };
  /* ---- type change ---- */
  const handleTypeChange = () => {
    queryConfigs();
  };

  const queryConfigs = async () => {
    try {
      const { type } = form;
      if (!type) return;
      const data: any = await getAgentConfigs(type!);
      configsTemplate.value = { ...data };
      form.configs = {
        ...configsTemplate.value,
      };
    } catch (err) {
      console.error(err);
    }
  };

  const formatFormParam = () => {
    const { name } = form;
    const { idx } = props.dialogData;
    return {
      ...form,
      name,
      idx: isEdit.value ? idx : undefined,
    };
  };

  const handleSubmit = () => {
    formRef.value?.validate().then(() => {
      submitLoading.value = true;
      const payload = formatFormParam();
      const api = isEdit.value
        ? requestAgentUpdate(form.name, payload)
        : requestAgentCreate(payload);

      api
        .then(() => {
          emit("search");
          handleCancel();
        })
        .catch((error: any) => {
          console.error(error);
        })
        .finally(() => {
          submitLoading.value = false;
        });
    });
  };

  const handleCancel = () => {
    emit("close");
  };
  onMounted(() => {
    if (isEdit.value) {
      queryPipelineList();
    }
  });
</script>

<style scoped lang="less">
  .enter-wrap {
    width: 100%;
    .title-wrap {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 16px;
      color: var(--font-main-color);
    }
    .form-wrap {
      .gt-wrap {
        margin-bottom: 0;
        :deep(.intel-form-item-control-input-content) {
          display: block;
        }
      }
      .configs-wrap {
        border: 1px solid var(--border-main-color);
        background-color: var(--bg-card-color);
        padding: 16px;
        margin-bottom: 16px;
        border-radius: 6px;
        width: 1005;
      }
      .item-wrap {
        width: 100%;
        position: relative;
        gap: 12px;
        padding-bottom: 8px;
        :deep(.intel-form-item) {
          flex: 1;
        }
      }
      .icon-wrap {
        cursor: pointer;
        display: inline-flex;
        gap: 8px;
        width: 20px;
        &.absolute {
          position: relative;
          top: -12px;
        }
        .anticon {
          font-size: 16px;
          &:hover {
            color: var(--color-primary);
          }
          &.anticon-delete {
            &:hover {
              color: var(--color-error) !important;
            }
          }
          &.anticon-minus-circle {
            &:hover {
              color: var(--color-error) !important;
            }
          }
        }
      }
      .add-wrap {
        .flex-end;
        gap: 6px;
        cursor: pointer;
        color: var(--color-primary);
        &:hover {
          color: var(--color-primary-hover);
        }
        &.vertical-center {
          justify-content: center !important;
        }
      }
    }
    .operate-wrap {
      height: 28px;
      border-radius: 4px;
      cursor: pointer;
      gap: 4px;
      border: 1px dashed var(--border-main-color);
      .vertical-center;
      &:hover {
        border: 1px dashed var(--color-primary-hover);
        color: var(--color-primary-hover);
      }
    }
  }
  .tip-wrap {
    .ml-12;
    font-size: 12px;
    color: var(--color-error);
  }
</style>
