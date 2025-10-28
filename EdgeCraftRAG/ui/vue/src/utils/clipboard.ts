// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ref, Ref } from "vue";
import { message } from "ant-design-vue";
import type { MessageType } from "ant-design-vue/es/message";
import i18n from "@/i18n";

interface UseClipboardOptions {
  timeout?: number;
}

interface UseClipboardReturn {
  copied: Ref<boolean>;
  clipboardText: Ref<string>;
  isSupported: Ref<boolean>;
  copy: (text: string) => Promise<boolean>;
  read: () => Promise<string | null>;
  reset: () => void;
}

export const useClipboard = (options: UseClipboardOptions = {}): UseClipboardReturn => {
  const { timeout = 2000 } = options;

  const copied = ref(false);
  const clipboardText = ref("");
  const isSupported = ref(!!navigator.clipboard);
  let timeoutId: number | null = null;
  let messageInstance: MessageType | null = null;

  const setCopiedState = (): void => {
    copied.value = true;

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = window.setTimeout(() => {
      copied.value = false;
    }, timeout);
  };

  const copy = async (text: string): Promise<boolean> => {
    if (!text) {
      message.error(i18n.global.t("common.copyError"));
      return false;
    }

    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(text);
      }
      clipboardText.value = text;
      setCopiedState();
      message.success(i18n.global.t("common.copySucc"));
      return true;
    } catch (error) {
      message.error(i18n.global.t("common.copyError"));
      return false;
    }
  };

  const read = async (): Promise<string | null> => {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        const text = await navigator.clipboard.readText();
        clipboardText.value = text;
        return text;
      } else {
        return null;
      }
    } catch (error) {
      console.error(error);

      return null;
    }
  };

  const reset = (): void => {
    copied.value = false;
    clipboardText.value = "";
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    if (messageInstance) {
      messageInstance();
      messageInstance = null;
    }
  };

  return {
    copied,
    clipboardText,
    isSupported,
    copy,
    read,
    reset,
  };
};
