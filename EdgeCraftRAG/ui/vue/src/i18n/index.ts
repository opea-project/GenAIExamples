// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createI18n } from "vue-i18n";
import { Local } from "@/utils/storage";
import enLocale from "ant-design-vue/es/locale/en_US";
import zhLocale from "ant-design-vue/es/locale/zh_CN";
import en from "./en";
import zh from "./zh";

const messages = {
  en_US: { ...en, ...enLocale },
  zh_CN: { ...zh, ...zhLocale },
};

const i18n = createI18n({
  locale: Local.get("themeInfo")?.lang || "en_US",
  fallbackLocale: "en_US",
  messages,
});

export default i18n;
