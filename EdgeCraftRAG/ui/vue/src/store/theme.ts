// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineStore } from "pinia";

export const themeAppStore = defineStore("theme", {
  state: () => ({
    theme: "light",
    lang: "en_US",
  }),
  persist: {
    key: "themeInfo",
    storage: localStorage,
  },
  actions: {
    toggleTheme(type: string) {
      this.theme = type;
    },
    toggleLanguage(lang: string) {
      this.lang = lang;
    },
  },
});
