<template>
  <a-form
    :model="form"
    :rules="rules"
    name="basic"
    layout="vertical"
    ref="formRef"
    autocomplete="off"
    class="form-wrap"
  >
    <a-form-item :label="$t('knowledge.type')" name="comp_subtype" class="horizontal-form-item">
      <a-radio-group
        v-model:value="form.comp_subtype"
        @change="handleTypeChange"
        :disabled="isEdit"
      >
        <a-radio value="origin_kb">{{ $t("knowledge.original") }}</a-radio>
        <a-radio value="kbadmin_kb">{{ $t("knowledge.kbadmin") }}</a-radio>
      </a-radio-group>
      <FormTooltip :title="$t('knowledge.desc.type')" />
    </a-form-item>
    <a-form-item :label="$t('knowledge.name')" name="name" v-if="isOriginal">
      <a-input
        v-model:value.trim="form.name"
        :maxlength="30"
        :disabled="isEdit"
        :placeholder="$t('knowledge.nameValid1')"
      />
      <FormTooltip :title="$t('knowledge.desc.name')" />
    </a-form-item>
    <template v-else>
      <a-form-item :name="['indexer', 'vector_url']" :rules="rules.vector_url">
        <template #label>
          {{ $t("pipeline.config.vector_url") }}
          <span class="eg-wrap">
            {{ $t("pipeline.valid.kb_vector_url") }}
          </span>
        </template>
        <a-input
          v-model:value="form.indexer.vector_url"
          :placeholder="$t('pipeline.valid.kb_vector_url')"
          @change="handleUriChange"
        >
          <template #addonBefore>
            <a-select v-model:value="protocol">
              <a-select-option value="http://">Http://</a-select-option>
              <a-select-option value="https://">Https://</a-select-option>
            </a-select>
          </template>
          <template #addonAfter>
            <a-button
              type="primary"
              class="text-btn"
              :disabled="!isVectorUrlPass"
              @click="handlleQueryKB"
            >
              <CheckCircleFilled
                v-if="isConnected"
                style="color: var(--color-success); font-size: 18px"
              />
              <span v-else>{{ $t("common.connect") }}</span>
            </a-button>
          </template>
        </a-input>
        <FormTooltip :title="$t('pipeline.desc.vector_url')" />
      </a-form-item>
      <a-form-item :label="$t('knowledge.name')" :rules="rules.kbName" name="name">
        <a-select
          showSearch
          v-model:value="form.name"
          :placeholder="$t('knowledge.nameRequired')"
          @dropdownVisibleChange="handleKBVisible"
        >
          <a-select-option v-for="item in kbList" :key="item" :value="item">{{
            item
          }}</a-select-option>
        </a-select>
        <FormTooltip :title="$t('knowledge.desc.name')" />
      </a-form-item>
    </template>
    <a-form-item :label="$t('knowledge.des')">
      <a-textarea
        v-model:value.trim="form.description"
        :placeholder="$t('knowledge.desValid')"
        :rows="3"
        :autoSize="false"
      />
      <FormTooltip :title="$t('knowledge.desc.description')" />
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup name="Basic">
  import { getkbadminList } from "@/api/knowledgeBase";
  import { useNotification } from "@/utils/common";
  import { isValidName, validateServiceAddress } from "@/utils/validate";
  import { CheckCircleFilled } from "@ant-design/icons-vue";
  import type { FormInstance } from "ant-design-vue";
  import { RuleObject } from "ant-design-vue/es/form";
  import { computed, reactive, ref } from "vue";
  import { useI18n } from "vue-i18n";

  const { t } = useI18n();
  const { antNotification } = useNotification();

  const props = defineProps({
    formData: {
      type: Object,
      default: () => {},
    },
    formType: {
      type: String,
      default: "create",
    },
  });

  interface IndexerType {
    vector_url?: string;
  }
  interface FormType {
    name: string | undefined;
    description: string;
    comp_type: string;
    comp_subtype: string;
    indexer: IndexerType;
  }
  const validateName = async (rule: any, value: string) => {
    if (!value) {
      return Promise.reject(t("knowledge.nameValid1"));
    }
    const len = value.length;
    if (len < 2 || len > 30) {
      return Promise.reject(t("knowledge.nameValid2"));
    }
    if (!isValidName(value)) {
      return Promise.reject(t("knowledge.nameValid3"));
    }
    return Promise.resolve();
  };
  const validateUnique = () => {
    return async (_rule: RuleObject, value: string) => {
      if (!value) {
        return Promise.reject(new Error(t("pipeline.valid.urlValid1")));
      }

      const serverUrl = protocol.value + value;
      if (!validateServiceAddress(serverUrl)) {
        return Promise.reject(new Error(t("pipeline.valid.urlValid2")));
      }

      isVectorUrlPass.value = true;

      return Promise.resolve();
    };
  };
  const {
    comp_subtype = "origin_kb",
    name = "default_kb",
    description = "",
    comp_type = "knowledge",
  } = props.formData;

  const host = window.location.hostname;
  const handleUrlFormat = (url: string) => {
    return url ? url.replace(/https?:\/\//g, "") : "";
  };
  const { vector_url = "" } = props.formData?.indexer || {};
  const kbList = ref<EmptyArrayType>([]);
  const formRef = ref<FormInstance>();
  const form = reactive<FormType>({
    comp_subtype,
    name,
    description,
    comp_type,
    indexer: { vector_url: vector_url ? handleUrlFormat(vector_url) : `${host}:29530` },
  });
  const isVectorUrlPass = ref<boolean>(false);
  const isConnected = ref<boolean>(false);
  const protocol = ref<string>("http://");
  const isEdit = computed(() => {
    const { formType } = props;
    return formType === "update";
  });
  const isOriginal = computed(() => {
    return form.comp_subtype === "origin_kb";
  });

  const rules: FormRules = reactive({
    comp_subtype: [
      {
        required: true,
        message: t("knowledge.typeValid"),
        trigger: "change",
      },
    ],
    name: [
      {
        required: true,
        validator: validateName,
        trigger: ["blur", "change"],
      },
    ],
    kbName: [
      {
        required: true,
        message: t("knowledge.nameRequired"),
        trigger: "change",
      },
    ],
    vector_url: [
      {
        required: true,
        validator: validateUnique(),
        trigger: "blur",
      },
    ],
  });

  const handleTypeChange = () => {
    form.name = undefined;
    isVectorUrlPass.value = false;
    isConnected.value = false;

    if (form.comp_subtype === "kbadmin_kb") {
      if (form.indexer.vector_url) {
        nextTick(() => formRef.value?.validateFields([["indexer", "vector_url"]]));
      }
    }
  };

  const handleUriChange = () => {
    isVectorUrlPass.value = false;
    isConnected.value = false;
    form.name = undefined;
  };
  const handleKBVisible = async (visible: boolean) => {
    if (visible) {
      try {
        if (!form.indexer.vector_url) {
          antNotification("warning", t("common.prompt"), t("pipeline.valid.urlValid1"));
          return;
        }
      } catch (err) {
        console.error(err);
      }
    }
  };
  const handlleQueryKB = () => {
    queryKbadmin();
  };
  const queryKbadmin = async () => {
    const { vector_url } = form.indexer;
    const url = protocol.value + vector_url;

    const data: any = await getkbadminList({ vector_url: url });
    kbList.value = [].concat(data);
    if (kbList.value.length) isConnected.value = true;
  };
  const formatFormParam = () => {
    const { indexer = {} } = props.formData || {};
    const { vector_url, ...otherParams } = indexer;

    return {
      ...form,
      indexer: {
        vector_url: form.indexer.vector_url,
        ...otherParams,
      },
    };
  };
  // Validate the form, throw results form
  const handleValidate = (): Promise<object> => {
    return new Promise(resolve => {
      formRef.value
        ?.validate()
        .then(() => {
          resolve({
            result: true,
            data: formatFormParam(),
          });
        })
        .catch(() => {
          resolve({ result: false });
        });
    });
  };
  defineExpose({
    validate: handleValidate,
  });
  watch(
    () => form.comp_subtype,
    val => {
      props.formData.comp_subtype = val;
    },
    { immediate: true }
  );
  onMounted(() => {
    if (props.formType === "update" && !isOriginal.value) {
      isVectorUrlPass.value = isConnected.value = true;
      queryKbadmin();
    }
  });
</script>

<style scoped lang="less">
  .text-btn {
    width: 72px;
    height: 30px;
    margin: 0 -11px;
    border-radius: 0 6px 6px 0;
    padding: 0;
    .vertical-center;
  }
</style>
