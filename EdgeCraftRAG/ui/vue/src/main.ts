// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createApp } from "vue";
import App from "./App.vue";
import i18n from "./i18n";
import router from "./router";
import pinia from "./store";
import "@/theme/index.less";
import { antConfig } from "@/utils/other";
import dayjs from "dayjs";
import "dayjs/locale/en";
import "dayjs/locale/zh-cn";
import "@/assets/iconFont/iconfont.css";
import { Local } from "@/utils/storage";

// setting dayjs language
const setDayjsLocale = (locale: string) => {
  if (locale === "en_US") {
    dayjs.locale("en");
  } else {
    dayjs.locale("zh-cn");
  }
};

const body = document.documentElement as HTMLElement;

if (Local.get("themeInfo")?.theme === "dark")
  body.setAttribute("data-theme", "dark");
else body.setAttribute("data-theme", "");

// watch i18n update dayjs language
watch(
  () => i18n.global.locale,
  (newLocale) => {
    setDayjsLocale(newLocale);
  },
  { immediate: true }
);
const app = createApp(App);

antConfig(app);

app.use(router).use(pinia).use(i18n).mount("#app");
