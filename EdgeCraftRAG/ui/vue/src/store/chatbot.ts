// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

const configuration = {
  configuration: {
    top_n: 25,
    temperature: 0.01,
    top_p: 0.95,
    top_k: 10,
    repetition_penalty: 1.03,
    max_tokens: 1024,
    stream: true,
  },
};
export const chatbotAppStore = defineStore("chatbot", {
  state: () => configuration,
  persist: {
    key: "chatbotConfiguration",
    storage: localStorage,
  },
  actions: {
    setChatbotConfiguration(configuration: EmptyObjectType) {
      this.configuration = {
        ...this.configuration,
        ...configuration,
      };
    },
  },
});
