// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import serviceManager from "@/utils/serviceManager";
import { ConfigProvider, notification } from "ant-design-vue";
import type { App } from "vue";
import { customNotification } from "./notification";
import FormTooltip from "@/components/FormTooltip.vue";
import SvgIcon from "@/components/SvgIcon.vue";

//Global Notification
notification.config({
  placement: "topRight",
  duration: 3,
  maxCount: 3,
});

export const antConfig = (app: App) => {
  app.component("SvgIcon", SvgIcon);
  app.component("FormTooltip", FormTooltip);
  app.use(ConfigProvider);
  app.provide("customNotification", customNotification);
  serviceManager.registerService("antNotification", customNotification);
};
