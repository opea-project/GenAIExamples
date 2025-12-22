// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { inject } from "vue";
import { customNotification } from "./notification";
import { sessionAppStore } from "@/store/session";

export const useNotification = () => {
  const customNotificationInjected = inject<typeof customNotification>("customNotification");

  if (!customNotificationInjected) {
    throw new Error("Notification service not provided");
  }
  return {
    antNotification: customNotificationInjected,
  };
};

export const formatDecimals = (num: number, decimalPlaces: number = 2) => {
  const factor = Math.pow(10, decimalPlaces);
  return Math.round(num * factor) / factor;
};

export const formatCapitalize = (string: string, start: number = 0, length: number = 1) => {
  const end = start + length;
  const part1 = string.slice(0, start);
  const part2 = string.slice(start, end).toUpperCase();
  const part3 = string.slice(end);
  return part1 + part2 + part3;
};

export const getChatSessionId = (): string => {
  const sessionStore = sessionAppStore();

  const storedSessionId = sessionStore.currentSession;
  if (storedSessionId) {
    return storedSessionId;
  }
  const newSessionId = self.crypto?.randomUUID?.() || generateFallbackId();

  sessionStore.setSessionId(newSessionId);
  return newSessionId;
};

const generateFallbackId = (): string => {
  if (typeof self !== "undefined" && self.crypto && self.crypto.getRandomValues) {
    const array = new Uint32Array(2);
    self.crypto.getRandomValues(array);
    const randomPart = Array.from(array)
      .map((num) => num.toString(36))
      .join("");
    return `${Date.now()}_${randomPart}`;
  } else {
    throw new Error("No secure random number generator available for session ID generation.");
  }
};

export const downloadJson = (data: object | string, filename: string = "pipeline.json") => {
  const jsonStr: string = typeof data === "string" ? data : JSON.stringify(data, null, 2);

  const blob: Blob = new Blob([jsonStr], { type: "application/json" });

  const url: string = URL.createObjectURL(blob);

  const a: HTMLAnchorElement = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export const formatTextStrict = (
  str: string,
  options?: {
    preserveSpaces?: boolean;
    keepOriginalCase?: boolean;
  },
): string => {
  const { preserveSpaces = true, keepOriginalCase = false } = options || {};

  // replace _ and -
  let processed = str.replace(/[_-]/g, " ");

  if (!preserveSpaces) {
    processed = processed.replace(/\s+/g, " ");
  }
  return processed
    .split(preserveSpaces ? /(\s+)/ : /\s+/)
    .map((segment) => {
      if (segment.trim() === "") {
        return segment;
      }
      const firstChar = segment.charAt(0).toUpperCase();
      const restChars = keepOriginalCase ? segment.slice(1) : segment.slice(1).toLowerCase();
      return firstChar + restChars;
    })
    .join("");
};

export const getEnumField = <T extends readonly Record<string, any>[]>(
  list: T,
  inputValue: any,
  matchKey: string = "value",
  outputKey: string = "name",
): any => {
  const item = list.find((item) => item[matchKey] === inputValue);
  return item?.[outputKey];
};
