// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

export const userAppStore = defineStore("user", {
  state: () => ({
    userGuide: false,
  }),
  persist: {
    key: "userInfo",
    storage: localStorage,
  },
  actions: {
    setUserGuideState(state: boolean) {
      this.userGuide = state;
    },
  },
});
