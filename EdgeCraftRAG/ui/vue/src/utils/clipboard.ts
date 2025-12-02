// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ref, Ref } from "vue";
import { message } from "ant-design-vue";
import i18n from "@/i18n";

interface UseClipboardReturn {
  copied: Ref<boolean>;
  copy: (text: string) => Promise<boolean>;
}

export const copyText = async (text: string, showMessage: boolean = true): Promise<boolean> => {
  if (!text) {
    if (showMessage) {
      message.error(i18n.global.t("common.copyError"));
    }
    return false;
  }

  const copyWithExecCommand = (text: string): boolean => {
    try {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.cssText = "position:fixed;top:0;left:0;opacity:0;pointer-events:none;z-index:-1;";
      document.body.appendChild(textArea);
      textArea.select();
      textArea.setSelectionRange(0, 99999);
      const successful = document.execCommand("copy");
      document.body.removeChild(textArea);
      return successful;
    } catch (err) {
      return false;
    }
  };

  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    } else {
      const success = copyWithExecCommand(text);
      if (!success) throw new Error("Copy failed");
    }

    if (showMessage) message.success(i18n.global.t("common.copySucc"));
    return true;
  } catch (error) {
    try {
      const success = copyWithExecCommand(text);
      if (success) {
        if (showMessage) message.success(i18n.global.t("common.copySucc"));
        return true;
      }
    } catch (fallbackError) {
      console.error("Fallback also failed:", fallbackError);
    }

    if (showMessage) message.error(i18n.global.t("common.copyError"));
    return false;
  }
};

export const useClipboard = (timeout: number = 2000): UseClipboardReturn => {
  const copied = ref(false);
  let timeoutId: number | null = null;

  const copy = async (text: string): Promise<boolean> => {
    const success = await copyText(text, true);

    if (success) {
      copied.value = true;
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        copied.value = false;
      }, timeout);
    }

    return success;
  };

  return {
    copied,
    copy,
  };
};
