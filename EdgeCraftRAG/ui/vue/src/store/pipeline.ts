// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

export const pipelineAppStore = defineStore("pipeline", {
  state: () => ({
    activatedPipeline: "",
  }),
  persist: {
    key: "pipelineInfo",
    storage: localStorage,
  },
  actions: {
    setPipelineActivate(name: string) {
      this.activatedPipeline = name;
    },
  },
});
