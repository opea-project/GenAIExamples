// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

const configuration = {
  configuration: {
    top_n: 5,
    temperature: 0.1,
    top_p: 1,
    top_k: 50,
    repetition_penalty: 1.1,
    max_tokens: 512,
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
