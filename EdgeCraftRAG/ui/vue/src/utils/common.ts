// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { inject } from "vue";
import { customNotification } from "./notification";
import { Local } from "./storage";

export const useNotification = () => {
  const customNotificationInjected =
    inject<typeof customNotification>("customNotification");

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

export const formatCapitalize = (
  string: string,
  start: number = 0,
  length: number = 1
) => {
  const end = start + length;
  const part1 = string.slice(0, start);
  const part2 = string.slice(start, end).toUpperCase();
  const part3 = string.slice(end);
  return part1 + part2 + part3;
};

export const getChatSessionId = (): string => {
  const STORAGE_KEY = "chat_session_id";

  const storedSessionId = Local.get(STORAGE_KEY);
  if (storedSessionId) {
    return storedSessionId;
  }
  const newSessionId = self.crypto?.randomUUID?.() || generateFallbackId();

  Local.set(STORAGE_KEY, newSessionId);
  return newSessionId;
};

const generateFallbackId = (): string => {
  if (
    typeof self !== "undefined" &&
    self.crypto &&
    self.crypto.getRandomValues
  ) {
    const array = new Uint32Array(2);
    self.crypto.getRandomValues(array);
    const randomPart = Array.from(array)
      .map((num) => num.toString(36))
      .join("");
    return `${Date.now()}_${randomPart}`;
  } else {
    throw new Error(
      "No secure random number generator available for session ID generation."
    );
  }
};
