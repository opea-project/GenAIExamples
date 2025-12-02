// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

const configuration = {
  agent: {
    name: "",
    type: "",
    index: 0,
  },
  sessionId: "",
  configuration: {
    top_n: 0,
    k: 0,
    temperature: 0.01,
    top_p: 0.95,
    top_k: 10,
    repetition_penalty: 1.03,
    max_tokens: 1024,
    stream: true,
    chat_template_kwargs: {
      enable_thinking: true,
      enable_rag_retrieval: true,
    },
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
    setAgent(agent: EmptyObjectType) {
      this.agent = {
        ...this.agent,
        ...agent,
      };
    },
    setSessionId(id: string) {
      this.sessionId = id;
    },
  },
});
